from base_test_utils import BaseAPITestCase
from django.contrib.auth.models import Group, User

class ManagerGroupTests(BaseAPITestCase):
    
    def setUp(self):
        super().setUp()
        # Create another user to add/remove from Managers
        self.user2 = User.objects.create_user(username = "user2", password = self.password)
        # Make self.user1 a manager
        self.user1.groups.add(self.manager_group)
        # Authenticate client with testuser1 token
        token = self.get_auth_token()
        self.authenticate_client(token)
        
    def test_manager_can_view_all_users(self):
        # Add another user to ensure multiple users exist
        User.objects.create_user(username="user3", password=self.password)
        User.objects.create_user(username="user4", password=self.password)
        url = "/api/users/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200) # type: ignore
        # Response should be a list of all users
        all_usernames = [user.username for user in User.objects.all()]
        response_usernames = [user["username"] for user in response.data] # type: ignore
        for username in all_usernames:
            self.assertIn(username, response_usernames)
        
    def test_manager_can_view_all_users_in_manager_group(self):
        # Add another user to ensure multiple users exist
        User.objects.create_user(username="user3", password=self.password)
        url = "/api/groups/manager/users/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200) # type: ignore
        # Check that all users in the Manager group are returned
        manager_group = Group.objects.get(name = "Manager")
        manager_usernames = [user.username for user in manager_group.user_set.all()]    # type: ignore
        response_usernames = [user["username"] for user in response.data] # type: ignore
        for username in manager_usernames:
            self.assertIn(username, response_usernames)
        
    def test_add_user_to_manager_group(self):
        url = "/api/groups/manager/users/"
        response = self.client.post(url, {"username": self.user2.username}, format = "json")
        self.assertEqual(response.status_code, 201) # type: ignore
        self.assertTrue(self.user2.groups.filter(name = "Manager").exists())
        
    def test_remove_user_from_manager_group(self):
        url = "/api/groups/manager/users/"
        response = self.client.delete(url, {"username": self.user2.username}, format = "json")
        self.assertEqual(response.status_code, 200) # type: ignore
        self.assertFalse(self.user2.groups.filter(name = "Manager").exists())

    def test_add_anonymous_user_to_manager_group_should_fail(self):
        url = "/api/groups/manager/users/"
        response = self.client.post(url, {"username": "nonexistentuser"}, format = "json")
        self.assertEqual(response.status_code, 404) # Should return 404 Not Found # type: ignore

    def test_remove_user_not_in_manager_group_should_fail(self):
        # Create a user not in the manager group
        user3 = User.objects.create_user(username = "user3", password = self.password)
        url = "/api/groups/manager/users/"
        response = self.client.delete(url, {"username": user3.username}, format = "json")
        self.assertEqual(response.status_code, 200) # Should still return 200 OK    # type: ignore
        self.assertFalse(user3.groups.filter(name = "Manager").exists())

    def test_non_manager_cannot_view_all_users(self):
        # Create a user who is not in the manager group
        user_non_manager = User.objects.create_user(username="notmanager", password=self.password)
        token = self.get_auth_token(username="notmanager", password=self.password)
        self.authenticate_client(token)
        url = "/api/users/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403) # Forbidden for non-managers # type: ignore

    def test_anonymous_cannot_view_all_users(self):
        # Unauthenticate the client
        self.client.logout()
        url = "/api/users/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401) # Unauthorized for anonymous users # type: ignore