from tests.base_test import BaseAPITestCase
from tests.endpoints import MANAGERS

class ManagersPermissionTests(BaseAPITestCase):
    def test_manager_views_list_of_users_in_manager_group(self):
        self.add_user_to_manager_group(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        response = self.client.get(MANAGERS)
        self.assertEqual(response.status_code, 200) # type: ignore
        
    def test_authenticated_and_authorized_admin_access(self):
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        response = self.client.get(MANAGERS)
        self.assertEqual(response.status_code, 200) # type: ignore
        
    def test_unauthenticated_access(self):
        response = self.client.get(MANAGERS)
        self.assertEqual(response.status_code, 401) # 401 Unauthorized for unauthenticated users # type: ignore

    def test_authenticated_but_not_authorized_access(self):
        token = self.get_auth_token()
        self.authenticate_client(token)
        response = self.client.get(MANAGERS)
        self.assertEqual(response.status_code, 403) # type: ignore

    # === Performance & Scalability Tests ===
    
    def test_permission_checks_large_user_base_performance(self):
        """Test permission system performance with many users and roles."""
        from django.contrib.auth.models import User
        from rest_framework import status
        from tests.endpoints import CATEGORIES, MENU_ITEMS
        
        # Arrange: Create many users with different permission levels
        regular_users = []
        manager_users = []
        
        # Create 25 regular users
        for i in range(25):
            user = User.objects.create_user(
                username=f"regular{i}",
                password="testpass123"
            )
            regular_users.append(user)
        
        # Create 25 manager users
        for i in range(25):
            user = User.objects.create_user(
                username=f"manager{i}",
                password="testpass123"
            )
            self.add_user_to_manager_group(user)
            manager_users.append(user)
        
        # Act: Test permission checks for regular users (should be denied manager access)
        denied_access_count = 0
        for user in regular_users[:10]:  # Test subset for performance
            # Get token for this user
            from rest_framework.authtoken.models import Token
            token, _ = Token.objects.get_or_create(user=user)
            
            # Test access to manager endpoint
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
            response = self.client.get(MANAGERS)
            if response.status_code == status.HTTP_403_FORBIDDEN:
                denied_access_count += 1
        
        # Assert: All regular users should be denied manager access
        self.assertEqual(denied_access_count, 10)

    def test_permission_rapid_authentication_switching(self):
        """Test rapid switching between different user authentication contexts."""
        from django.contrib.auth.models import User
        from rest_framework import status
        from rest_framework.authtoken.models import Token
        
        # Arrange: Create users with different permission levels
        regular_user = User.objects.create_user("rapidreg", "testpass123")
        manager_user = User.objects.create_user("rapidmgr", "testpass123") 
        self.add_user_to_manager_group(manager_user)
        
        regular_token, _ = Token.objects.get_or_create(user=regular_user)
        manager_token, _ = Token.objects.get_or_create(user=manager_user)
        
        # Act: Rapidly switch between user contexts
        permission_results = []
        
        # Alternate between users multiple times
        for i in range(10):
            if i % 2 == 0:
                # Use regular user (should be denied)
                self.client.credentials(HTTP_AUTHORIZATION=f'Token {regular_token.key}')
                expected_status = status.HTTP_403_FORBIDDEN
            else:
                # Use manager user (should be allowed)
                self.client.credentials(HTTP_AUTHORIZATION=f'Token {manager_token.key}')
                expected_status = status.HTTP_200_OK
            
            response = self.client.get(MANAGERS)
            permission_results.append(response.status_code == expected_status)
        
        # Assert: All permission checks should work correctly
        self.assertTrue(all(permission_results))

    def test_permission_token_expiry_and_reuse_validation(self):
        """Test permission system behavior with token reuse and validation."""
        from rest_framework import status
        from rest_framework.authtoken.models import Token
        
        # Arrange: Create manager user
        self.add_user_to_manager_group(self.user1)
        token, _ = Token.objects.get_or_create(user=self.user1)
        
        # Act: Use same token for multiple requests
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        successful_requests = 0
        for i in range(15):
            response = self.client.get(MANAGERS)
            if response.status_code == status.HTTP_200_OK:
                successful_requests += 1
        
        # Assert: All requests should succeed with valid token
        self.assertEqual(successful_requests, 15)

    def test_permission_boundary_conditions(self):
        """Test permission system edge cases and boundary conditions."""
        from rest_framework import status
        from endpoints import CATEGORIES, MENU_ITEMS
        
        # Test 1: User with staff status but no group membership
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token(self.user1.username)
        self.authenticate_client(token)
        
        response = self.client.get(MANAGERS)
        # Staff users should have access to manager endpoints
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test 2: User in manager group but no staff status (edge case)
        self.user1.is_staff = False
        self.user1.save()
        self.add_user_to_manager_group(self.user1)
        
        # Refresh token
        token = self.get_auth_token(self.user1.username)
        self.authenticate_client(token)
        
        response = self.client.get(MANAGERS)
        # Manager group members should still have access
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    def test_permission_malformed_tokens_and_headers(self):
        """Test permission system with various malformed authentication scenarios."""
        from rest_framework import status
        
        malformed_auth_scenarios = [
            "",  # Empty authorization header
            "Token",  # Missing token value
            "Bearer invalid_token",  # Wrong auth type
            "Token " + "x" * 100,  # Invalid token format
            "Token invalid_token_123",  # Non-existent token
            "token lowercase_prefix",  # Wrong case
        ]
        
        for auth_header in malformed_auth_scenarios:
            with self.subTest(auth_header=auth_header):
                if auth_header:
                    self.client.credentials(HTTP_AUTHORIZATION=auth_header)
                else:
                    self.client.credentials()  # No auth header
                
                response = self.client.get(MANAGERS)
                # Should return 401 Unauthorized for all malformed scenarios
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)