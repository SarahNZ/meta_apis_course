from rest_framework import status

from base_test import BaseAPITestCase
from endpoints import LOGIN


class AuthTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        # Ensure default user exists
        self.user = self.user1

    # === Helper Methods ===
    
    def _login_with_credentials(self, username, password):
        """Helper method to attempt login with given credentials"""
        credentials = {"username": username, "password": password}
        return self.client.post(LOGIN, credentials, format="json")
    
    def _verify_successful_login(self, response):
        """Helper method to verify successful login response"""
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json().get("auth_token")
        self.assertIsNotNone(token)
        return token
    
    def _verify_failed_login(self, response):
        """Helper method to verify failed login response"""
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("auth_token", response.json())
    
    def _verify_token_validity(self, token):
        """Helper method to verify token exists for user"""
        self.assertTrue(self.user.auth_token.key == token)
    
    def _test_multiple_login_attempts(self, credentials, expected_success_count):
        """Helper method to test multiple login attempts"""
        successful_logins = 0
        for i in range(expected_success_count):
            response = self._login_with_credentials(credentials["username"], credentials["password"])
            if response.status_code == status.HTTP_200_OK:
                successful_logins += 1
        return successful_logins
    
    def _test_invalid_credentials_list(self, invalid_credentials_list):
        """Helper method to test list of invalid credentials"""
        for credentials in invalid_credentials_list:
            with self.subTest(credentials=credentials):
                response = self._login_with_credentials(credentials["username"], credentials["password"])
                self._verify_failed_login(response)
    
    def _test_authenticated_api_calls(self, token, endpoint, expected_count):
        """Helper method to test authenticated API calls"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        successful_requests = 0
        for i in range(expected_count):
            response = self.client.get(endpoint)
            if response.status_code == status.HTTP_200_OK:
                successful_requests += 1
        return successful_requests
        
    # === Login Tests ===
    
    def test_login_success(self):
        # Act
        response = self._login_with_credentials(self.user.username, self.password)
        
        # Assert
        token = self._verify_successful_login(response)
        self._verify_token_validity(token)
        
    def test_login_failure_wrong_credentials(self):
        # Act
        response = self._login_with_credentials("wrong", "wrong")
        
        # Assert
        self._verify_failed_login(response)

    # === Performance & Scalability Tests ===
    
    def test_authentication_rapid_login_requests(self):
        """Test authentication system under rapid login attempts."""
        # Arrange: Valid credentials
        credentials = {
            "username": self.user.username,
            "password": self.password
        }
        
        # Act & Assert: All login attempts should succeed
        successful_logins = self._test_multiple_login_attempts(credentials, 10)
        self.assertEqual(successful_logins, 10)

    def test_authentication_invalid_credential_patterns(self):
        """Test authentication with various invalid credential patterns."""
        invalid_credentials = [
            {"username": "", "password": ""},  # Empty credentials
            {"username": "a" * 151, "password": self.password},  # Username too long (User model default max_length=150)
            {"username": self.user.username, "password": "a" * 129},  # Password too long (default max_length=128)
            {"username": "nonexistent", "password": "validpassword"},  # Nonexistent user
            {"username": self.user.username, "password": ""},  # Empty password
            {"username": "", "password": self.password},  # Empty username
        ]
        
        # Act & Assert: All should return 400 Bad Request
        self._test_invalid_credentials_list(invalid_credentials)

    def test_authentication_token_reuse_validation(self):
        """Test that authentication tokens work correctly for repeated API calls."""
        # Arrange: Login and get token
        login_response = self._login_with_credentials(self.user.username, self.password)
        token = self._verify_successful_login(login_response)
        
        # Act & Assert: Use token for multiple API calls
        from endpoints import CATEGORIES
        successful_requests = self._test_authenticated_api_calls(token, CATEGORIES, 10)
        self.assertEqual(successful_requests, 10)

    def test_authentication_malformed_requests(self):
        """Test authentication system with malformed request data."""
        malformed_requests = [
            {},  # Missing both username and password
            {"username": self.user.username},  # Missing password
            {"password": self.password},  # Missing username
            {"user": self.user.username, "pass": self.password},  # Wrong field names
            {"username": None, "password": None},  # Null values
            {"username": 123, "password": 456},  # Wrong data types
        ]
        
        # Act & Assert: All should return 400 Bad Request
        for request_data in malformed_requests:
            with self.subTest(request_data=request_data):
                response = self.client.post(LOGIN, request_data, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authentication_case_sensitivity(self):
        """Test authentication username case sensitivity."""
        # Test various username case combinations
        username_variations = [
            self.user.username.upper(),  # All uppercase
            self.user.username.lower(),  # All lowercase
            self.user.username.capitalize(),  # First letter uppercase
        ]
        
        for username in username_variations:
            with self.subTest(username=username):
                response = self._login_with_credentials(username, self.password)
                
                # Django usernames are case-sensitive by default
                if username == self.user.username:
                    self._verify_successful_login(response)
                else:
                    self._verify_failed_login(response)
