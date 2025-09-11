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
        response = self.client.delete(MANAGERS, {"username": self.user2.username}, format = "json")
        self.assertEqual(response.status_code, 200) # type: ignore
        self.assertFalse(self.user2.groups.filter(name = "Manager").exists())
        
    def test_unauthorized_user_cannot_remove_user_from_manager_group(self):
        # Add user2 to manager group first
        self.user2.groups.add(self.manager_group)
        # Create and authenticate as non-manager user
        User.objects.create_user(username="unauthorized2", password=self.password)
        token = self.get_auth_token(username="unauthorized2", password=self.password)
        self.authenticate_client(token)
        response = self.client.delete(MANAGERS, {"username": self.user2.username}, format="json")
        self.assertEqual(response.status_code, 403) # Forbidden for non-managers # type: ignore
        self.assertTrue(self.user2.groups.filter(name="Manager").exists())
        
    def test_anonymous_user_cannot_remove_user_from_manager_group(self):
        # Add user2 to manager group first
        self.user2.groups.add(self.manager_group)
        # Unauthenticate the client
        self.client.logout()
        response = self.client.delete(MANAGERS, {"username": "nonexistentuser"}, format = "json")
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

    def test_remove_user_from_manager_group_missing_username(self):
        response = self.client.delete(MANAGERS, {}, format="json")
        self.assertEqual(response.status_code, 400)  # Bad Request # type: ignore

    def test_remove_user_from_manager_group_empty_username(self):
        response = self.client.delete(MANAGERS, {"username": ""}, format="json")
        self.assertEqual(response.status_code, 400)  # Bad Request # type: ignore

    def test_remove_user_from_manager_group_nonexistent_username(self):
        response = self.client.delete(MANAGERS, {"username": "nonexistentuser"}, format="json")
        self.assertEqual(response.status_code, 404)  # Not Found # type: ignore

    def test_remove_user_from_manager_group_invalid_field_name(self):
        response = self.client.delete(MANAGERS, {"user": self.user2.username}, format="json")
        self.assertEqual(response.status_code, 400)  # Bad Request # type: ignore