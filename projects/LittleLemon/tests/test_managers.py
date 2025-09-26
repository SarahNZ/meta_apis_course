from rest_framework import status
from base_test import BaseAPITestCase
from django.contrib.auth.models import Group, User
from endpoints import USERS, MANAGERS 

class ManagerGroupTests(BaseAPITestCase):
    
    def setUp(self):
        super().setUp()
        # Ensure the Manager group exists
        self.manager_group, _ = Group.objects.get_or_create(name="Manager")
        # Create users to add/remove from Managers
        self.user2 = User.objects.create_user(username = "user2", password = self.password)
        self.user3 = User.objects.create_user(username="user3", password=self.password)
        # Make self.user1 a manager and give staff status
        self.user1.groups.add(self.manager_group)
        self.give_user_staff_status(self.user1)
        # Authenticate client with testuser1 token
        token = self.get_auth_token()
        self.authenticate_client(token)
    
    # === View All Users Tests ===
    
    def test_manager_views_all_users(self):
        response = self.client.get(USERS)
        self.assertEqual(response.status_code, 200) # type: ignore
        # Response should be a list of all users
        all_usernames = [user.username for user in User.objects.all()]
        response_usernames = [user["username"] for user in response.data] # type: ignore
        for username in all_usernames:
            self.assertIn(username, response_usernames)
            
    def test_unauthorized_user_cannot_view_all_users(self):
        # Create a user who is not in the manager group
        user_non_manager = User.objects.create_user(username="notmanager", password=self.password)
        token = self.get_auth_token(username="notmanager", password=self.password)
        self.authenticate_client(token)
        response = self.client.get(USERS)
        self.assertEqual(response.status_code, 403) # Forbidden for non-managers # type: ignore

    def test_anonymous_user_cannot_view_all_users(self):
        # Unauthenticate the client
        self.client.logout()
        response = self.client.get(USERS)
        self.assertEqual(response.status_code, 401) # Unauthorized for anonymous users # type: ignore
        
    # === View All Users in the Manager Group Tests ===
        
    def test_manager_views_all_users_in_manager_group(self):
        response = self.client.get(MANAGERS)
        self.assertEqual(response.status_code, 200) # type: ignore
        # Check that all users in the Manager group are returned
        manager_group = Group.objects.get(name = "Manager")
        manager_usernames = [user.username for user in manager_group.user_set.all()]    # type: ignore
        response_usernames = [user["username"] for user in response.data] # type: ignore
        for username in manager_usernames:
            self.assertIn(username, response_usernames)
            
    def test_unauthorized_authenticated_user_cannot_view_all_users_in_manager_group(self):
        # Create a user who is not in the manager group
        user_non_manager = User.objects.create_user(username="notmanager", password=self.password)
        token = self.get_auth_token(username="notmanager", password=self.password)
        self.authenticate_client(token)
        response = self.client.get(MANAGERS)
        self.assertEqual(response.status_code, 403) # Forbidden for non-managers # type: ignore

    def test_anonymous_user_cannot_view_all_users_in_manager_group(self):
        self.client.credentials() # remove authentication
        response = self.client.get(MANAGERS)
        self.assertEqual(response.status_code, 401) # Unauthorized for anonymous users # type: ignore
        
    # === Add Users to the Manager Group Tests ===
        
    def test_manager_adds_user_to_manager_group(self):
        response = self.client.post(MANAGERS, {"username": self.user2.username}, format = "json")
        self.assertEqual(response.status_code, 201) # type: ignore
        self.assertTrue(self.user2.groups.filter(name = "Manager").exists())
        
    def test_unsupported_http_methods_to_managers_endpoint_return_405(self):
        response = self.client.put(MANAGERS, {"username": self.user2.username}, format = "json")
        self.assertEqual(response.status_code, 405) # type: ignore
        
    def test_unauthorized_user_cannot_add_user_to_manager_group(self):
        # Create and authenticate a non-manager user
        User.objects.create_user(username="unauthorized", password=self.password)
        token = self.get_auth_token(username="unauthorized", password=self.password)
        self.authenticate_client(token)
        response = self.client.post(MANAGERS, {"username": self.user3.username}, format="json")
        self.assertEqual(response.status_code, 403) # Forbidden for non-managers # type: ignore
        self.assertFalse(self.user3.groups.filter(name="Manager").exists())

    def test_anonymous_user_cannot_add_user_to_manager_group(self):
        # Unauthenticate the client
        self.client.logout()
        response = self.client.post(MANAGERS, {"username": "nonexistentuser"}, format = "json")
        self.assertEqual(response.status_code, 401) # Should return 401 Unauthenticated # type: ignore
        
    # === Remove Users from the Manager Group Tests ===

    def test_manager_removes_user_from_manager_group(self):
        # Add user2 to manager group first
        response = self.client.post(MANAGERS, {"username": self.user2.username}, format = "json")
        # Now delete using the id-based URL
        user_id = self.user2.id
        response = self.client.delete(f"{MANAGERS}{user_id}/")
        self.assertEqual(response.status_code, 204) # type: ignore
        self.assertFalse(self.user2.groups.filter(name = "Manager").exists())
        
    def test_unauthorized_user_cannot_remove_user_from_manager_group(self):
        # Add user2 to manager group first
        self.user2.groups.add(self.manager_group)
        # Create and authenticate as non-manager user
        User.objects.create_user(username="unauthorized2", password=self.password)
        token = self.get_auth_token(username="unauthorized2", password=self.password)
        self.authenticate_client(token)
        # Now delete using the id-based URL
        user_id = self.user2.id
        response = self.client.delete(f"{MANAGERS}{user_id}/")
        self.assertEqual(response.status_code, 403) # Forbidden for non-managers # type: ignore
        self.assertTrue(self.user2.groups.filter(name="Manager").exists())
        
    def test_anonymous_user_cannot_remove_user_from_manager_group(self):
        # Add user2 to manager group first
        self.user2.groups.add(self.manager_group)
        # Unauthenticate the client
        self.client.logout()
        # Now delete using the id-based URL
        user_id = self.user2.id
        response = self.client.delete(f"{MANAGERS}{user_id}/")
        self.assertEqual(response.status_code, 401) # Should return 401 Unauthenticated # type: ignore
    
    # === Manager Group Input Validation Tests ===

    def test_add_user_to_manager_group_missing_username(self):
        response = self.client.post(MANAGERS, {}, format="json")
        self.assertEqual(response.status_code, 400)  # Bad Request # type: ignore

    def test_add_user_to_manager_group_empty_username(self):
        response = self.client.post(MANAGERS, {"username": ""}, format="json")
        self.assertEqual(response.status_code, 400)  # Bad Request # type: ignore

    def test_add_user_to_manager_group_nonexistent_username(self):
        response = self.client.post(MANAGERS, {"username": "nonexistentuser"}, format="json")
        self.assertEqual(response.status_code, 404)  # Not Found # type: ignore

    def test_add_user_to_manager_group_invalid_field_name(self):
        response = self.client.post(MANAGERS, {"user": self.user2.username}, format="json")
        self.assertEqual(response.status_code, 400)  # Bad Request # type: ignore

    def test_remove_user_from_manager_group_missing_id(self):
        # Using an empty string as ID
        response = self.client.delete(f"{MANAGERS}/")
        self.assertEqual(response.status_code, 404)  # Not Found # type: ignore

    def test_remove_user_from_manager_group_nonexistent_id(self):
        # Using a nonexistent ID (99999)
        response = self.client.delete(f"{MANAGERS}99999/")
        self.assertEqual(response.status_code, 404)  # Not Found # type: ignore

    def test_remove_user_from_manager_group_invalid_id(self):
        # Using an invalid ID format
        response = self.client.delete(f"{MANAGERS}invalid/")
        self.assertEqual(response.status_code, 404)  # Not Found # type: ignore

    def test_remove_user_not_in_manager_group(self):
        # Try to remove a user not in the manager group
        user_id = self.user3.id  # user3 is not in manager group
        response = self.client.delete(f"{MANAGERS}{user_id}/")
        self.assertEqual(response.status_code, 404)  # Not Found # type: ignore

    # === Performance & Scalability Tests ===
    
    def test_managers_large_user_base_performance(self):
        """Test manager group operations with many users."""
        from django.contrib.auth.models import User
        
        # Arrange: Create many users to test scalability
        bulk_users = []
        for i in range(50):
            bulk_users.append(User(
                username=f"mgrtestuser{i}",  # Unique prefix to avoid conflicts
                email=f"mgrtestuser{i}@example.com"
            ))
        
        User.objects.bulk_create(bulk_users)
        
        # Act: Request all users as manager
        response = self.client.get(USERS)
        
        # Assert: Should handle large user base gracefully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 50)  # At least our test users

    def test_managers_rapid_user_group_modifications(self):
        """Test rapid addition and removal of users from manager group."""
        from django.contrib.auth.models import User
        
        # Arrange: Create test users for bulk operations
        test_users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f"bulktest{i}",
                password="testpass123"
            )
            test_users.append(user)
        
        # Act: Rapidly add users to manager group
        successful_additions = 0
        for user in test_users:
            data = {"username": user.username}
            response = self.client.post(MANAGERS, data, format="json")
            if response.status_code == status.HTTP_201_CREATED:
                successful_additions += 1
        
        # Assert: All additions should succeed
        self.assertEqual(successful_additions, 10)
        
        # Act: Rapidly remove users from manager group  
        successful_removals = 0
        for user in test_users:
            response = self.client.delete(f"{MANAGERS}{user.id}/")
            if response.status_code == status.HTTP_204_NO_CONTENT:
                successful_removals += 1
        
        # Assert: All removals should succeed
        self.assertEqual(successful_removals, 10)

    def test_managers_username_length_limits(self):
        """Test manager operations with username boundary values."""
        from django.contrib.auth.models import User
        
        # Test maximum username length (User model default max_length=150)
        max_length_username = "a" * 150
        
        # Create user with maximum length username
        test_user = User.objects.create_user(
            username=max_length_username,
            password="testpass123"
        )
        
        # Act: Add user with max length username to manager group
        data = {"username": max_length_username}
        response = self.client.post(MANAGERS, data, format="json")
        
        # Assert: Should succeed
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user is in manager group
        from django.contrib.auth.models import Group
        manager_group = Group.objects.get(name='Manager')
        self.assertTrue(test_user.groups.filter(name='Manager').exists())

    def test_managers_invalid_username_patterns(self):
        """Test manager operations with various invalid username patterns."""
        invalid_usernames = [
            "",  # Empty username
            "a" * 151,  # Username too long (> 150 chars)
            "nonexistent_user_12345",  # Nonexistent user
            "user with spaces",  # Username with spaces (may be invalid)
            "user@domain.com",  # Email-like format
        ]
        
        # Act & Assert: All should return appropriate error responses
        for username in invalid_usernames:
            with self.subTest(username=username):
                data = {"username": username}
                response = self.client.post(MANAGERS, data, format="json")
                
                # Should return 400 Bad Request for various validation failures
                self.assertIn(response.status_code, [
                    status.HTTP_400_BAD_REQUEST,
                    status.HTTP_404_NOT_FOUND
                ])

    def test_managers_concurrent_group_operations_simulation(self):
        """Test manager group operations under simulated concurrent access."""
        from django.contrib.auth.models import User
        
        # Arrange: Create users for concurrent operations testing
        concurrent_users = []
        for i in range(20):
            user = User.objects.create_user(
                username=f"concurrent{i}",
                password="testpass123"
            )
            concurrent_users.append(user)
        
        # Act: Simulate concurrent additions (sequential but rapid)
        operations_data = []
        for user in concurrent_users:
            operations_data.append({"username": user.username})
        
        successful_operations = 0
        failed_operations = 0
        
        for data in operations_data:
            response = self.client.post(MANAGERS, data, format="json")
            if response.status_code == status.HTTP_201_CREATED:
                successful_operations += 1
            else:
                failed_operations += 1
        
        # Assert: Most or all operations should succeed
        self.assertGreaterEqual(successful_operations, 18)  # Allow for some potential race conditions
        
        # Verify users are actually in manager group
        from django.contrib.auth.models import Group
        manager_group = Group.objects.get(name='Manager')
        managers_count = manager_group.user_set.filter(
            username__startswith='concurrent'
        ).count()
        self.assertEqual(managers_count, successful_operations)

    def test_managers_group_membership_validation(self):
        """Test validation of manager group membership status."""
        from django.contrib.auth.models import User, Group
        
        # Create test user
        test_user = User.objects.create_user(
            username="membership_test",
            password="testpass123"
        )
        
        # Verify user is not initially in manager group
        manager_group = Group.objects.get(name='Manager')
        self.assertFalse(test_user.groups.filter(name='Manager').exists())
        
        # Add user to manager group
        data = {"username": "membership_test"}
        response = self.client.post(MANAGERS, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user is now in manager group and has staff status
        test_user.refresh_from_db()
        self.assertTrue(test_user.groups.filter(name='Manager').exists())
        self.assertTrue(test_user.is_staff)  # Should automatically get staff status
        
        # Try to add same user again (should handle gracefully)
        response = self.client.post(MANAGERS, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)