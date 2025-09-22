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
