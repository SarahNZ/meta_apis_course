from rest_framework import status

from base_test import BaseAPITestCase
from endpoints import LOGIN


class AuthTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        # Ensure default user exists
        self.user = self.user1
        
    # === Login Tests ===
    
    def test_login_success(self):
        # Arrange: Credentials
        credentials = {
            "username": self.user.username,
            "password": self.password
        }
        
        # Act
        response = self.client.post(LOGIN, credentials, format = "json")
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        token = response.json().get("auth_token")   # type: ignore
        self.assertIsNotNone(token)
        
        # Database-level check: ensure the token exists for the user
        self.assertTrue(self.user.auth_token.key == token)  # type: ignore
        
    def test_login_failure_wrong_credentials(self):
        
        # Arrange
        credentials = {
            "username": "wrong",
            "password": "wrong"
        }
        
        # Act
        response = self.client.post(LOGIN, {"username": "wrong", "password": "wrong"},format="json")
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) # type: ignore
        self.assertNotIn("auth_token", response.json()) # type: ignore

    # === Performance & Scalability Tests ===
    
    def test_authentication_rapid_login_requests(self):
        """Test authentication system under rapid login attempts."""
        # Arrange: Valid credentials
        credentials = {
            "username": self.user.username,
            "password": self.password
        }
        
        # Act: Perform multiple rapid login requests
        successful_logins = 0
        for i in range(10):
            response = self.client.post(LOGIN, credentials, format="json")
            if response.status_code == status.HTTP_200_OK:
                successful_logins += 1
        
        # Assert: All login attempts should succeed
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
        for credentials in invalid_credentials:
            with self.subTest(credentials=credentials):
                response = self.client.post(LOGIN, credentials, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertNotIn("auth_token", response.json())

    def test_authentication_token_reuse_validation(self):
        """Test that authentication tokens work correctly for repeated API calls."""
        # Arrange: Login and get token
        credentials = {
            "username": self.user.username,
            "password": self.password
        }
        
        login_response = self.client.post(LOGIN, credentials, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        token = login_response.json().get("auth_token")
        self.assertIsNotNone(token)
        
        # Act: Use token for multiple API calls (using categories as test endpoint)
        from endpoints import CATEGORIES
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        successful_requests = 0
        for i in range(10):
            response = self.client.get(CATEGORIES)
            if response.status_code == status.HTTP_200_OK:
                successful_requests += 1
        
        # Assert: All authenticated requests should succeed
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
                credentials = {
                    "username": username,
                    "password": self.password
                }
                
                response = self.client.post(LOGIN, credentials, format="json")
                
                # Django usernames are case-sensitive by default
                if username == self.user.username:
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                else:
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
