from base_test_utils import BaseAPITestCase
from django.contrib.auth.models import Group, User
from endpoints import DELIVERY_CREW

class DeliveryCrewTests(BaseAPITestCase):
    
    def setUp(self):
        super().setUp()
        # Create 2 users and add them to the "Delivery Crew" group
        self.user2 = User.objects.create_user(username = "user2", password = self.password)
        self.user3 = User.objects.create_user(username="user3", password=self.password)
        self.user2.groups.add(self.delivery_crew_group)
        self.user3.groups.add(self.delivery_crew_group)
        # Make self.user1 a manager
        self.user1.groups.add(self.manager_group)
        # Authenticate client with testuser1 token
        token = self.get_auth_token()
        self.authenticate_client(token)
        
    def test_manager_views_all_users_in_delivery_crew_group(self):
        response = self.client.get(DELIVERY_CREW)
        self.assertEqual(response.status_code, 200) # type: ignore
        # Check that all users in the Delivery Crew group are returned
        delivery_crew = Group.objects.get(name = "Delivery Crew")
        delivery_crew_usernames = [user.username for user in delivery_crew.user_set.all()]    # type: ignore
        response_usernames = [user["username"] for user in response.data] # type: ignore
        for username in delivery_crew_usernames:
            self.assertIn(username, response_usernames) 
            
    def test_non_manager_cannot_view_all_delivery_crew_users(self):
        # Create a user who is not in the manager group
        user_non_manager = User.objects.create_user(username="notmanager", password=self.password)
        token = self.get_auth_token(username="notmanager", password=self.password)
        self.authenticate_client(token)
        response = self.client.get(DELIVERY_CREW)
        self.assertEqual(response.status_code, 403) # Forbidden for non-managers # type: ignore
        
    def test_anonymous_cannot_view_all_delivery_crew_users(self):
        # Unauthenticate the client
        self.client.logout()
        response = self.client.get(DELIVERY_CREW)
        self.assertEqual(response.status_code, 401) # Unauthorized for anonymous users # type: ignore
        
    # def test_add_user_to_manager_group(self):
    #     url = "/api/groups/manager/users/"
    #     response = self.client.post(url, {"username": self.user2.username}, format = "json")
    #     self.assertEqual(response.status_code, 201) # type: ignore
    #     self.assertTrue(self.user2.groups.filter(name = "Manager").exists())
        
    # def test_remove_user_from_manager_group(self):
    #     url = "/api/groups/manager/users/"
    #     response = self.client.delete(url, {"username": self.user2.username}, format = "json")
    #     self.assertEqual(response.status_code, 200) # type: ignore
    #     self.assertFalse(self.user2.groups.filter(name = "Manager").exists())

    # def test_add_anonymous_user_to_manager_group_should_fail(self):
    #     url = "/api/groups/manager/users/"
    #     response = self.client.post(url, {"username": "nonexistentuser"}, format = "json")
    #     self.assertEqual(response.status_code, 404) # Should return 404 Not Found # type: ignore

    # def test_remove_user_not_in_manager_group_should_fail(self):
    #     # Create a user not in the manager group
    #     user3 = User.objects.create_user(username = "user3", password = self.password)
    #     url = "/api/groups/manager/users/"
    #     response = self.client.delete(url, {"username": user3.username}, format = "json")
    #     self.assertEqual(response.status_code, 200) # Should still return 200 OK    # type: ignore
    #     self.assertFalse(user3.groups.filter(name = "Manager").exists())