from base_test import BaseAPITestCase
from django.contrib.auth.models import Group, User
from endpoints import DELIVERY_CREW

class DeliveryCrewGroupTests(BaseAPITestCase):
    
    def setUp(self):
        super().setUp()
        # Create 2 users and add them to the "Delivery Crew" group
        self.user2 = User.objects.create_user(username = "user2", password = self.password)
        self.user3 = User.objects.create_user(username="user3", password=self.password)
        self.user2.groups.add(self.delivery_crew_group)
        self.user3.groups.add(self.delivery_crew_group)
        # Make self.user1 a manager and give staff status
        self.user1.groups.add(self.manager_group)
        self.give_user_staff_status(self.user1)
        # Authenticate client with testuser1 token
        token = self.get_auth_token()
        self.authenticate_client(token)
        
    # === View All Users in the Delivery Crew Group Tests ===
        
    def test_manager_views_all_users_in_delivery_crew_group(self):
        response = self.client.get(DELIVERY_CREW)
        self.assertEqual(response.status_code, 200) # type: ignore
        # Check that all users in the Delivery Crew group are returned
        delivery_crew = Group.objects.get(name = "Delivery Crew")
        delivery_crew_usernames = [user.username for user in delivery_crew.user_set.all()]    # type: ignore
        response_usernames = [user["username"] for user in response.data] # type: ignore
        for username in delivery_crew_usernames:
            self.assertIn(username, response_usernames) 
            
    def test_unauthorized_authenticated_user_cannot_view_all_delivery_crew_users(self):
        # Create a user who is not in the manager group
        user_non_manager = User.objects.create_user(username="notmanager", password=self.password)
        token = self.get_auth_token(username="notmanager", password=self.password)
        self.authenticate_client(token)
        response = self.client.get(DELIVERY_CREW)
        self.assertEqual(response.status_code, 403) # Forbidden for non-managers # type: ignore
        
    def test_anonymous_user_cannot_view_delivery_crew_users(self):
        # Unauthenticate the client
        self.client.logout()
        response = self.client.get(DELIVERY_CREW)
        self.assertEqual(response.status_code, 401) # Unauthorized for anonymous users # type: ignore
        
# === Add Users to the Delivery Crew Group Tests ===
        
    def test_manager_adds_user_to_delivery_crew_group(self):
        response = self.client.post(DELIVERY_CREW, {"username": self.user2.username}, format = "json")
        self.assertEqual(response.status_code, 201) # type: ignore
        self.assertTrue(self.user2.groups.filter(name = "Delivery Crew").exists())
        
    def test_unsupported_http_methods_for_delivery_crew_endpoint_return_405(self):
        response = self.client.put(DELIVERY_CREW, {"username": self.user2.username}, format = "json")
        self.assertEqual(response.status_code, 405) # type: ignore
        
    def test_unauthorized_authenticated_user_cannot_add_user_to_delivery_crew_group(self):
        # Create and authenticate a non-manager user
        User.objects.create_user(username="unauthorized", password=self.password)
        token = self.get_auth_token(username="unauthorized", password=self.password)
        self.authenticate_client(token)
        response = self.client.post(DELIVERY_CREW, {"username": self.user3.username}, format="json")
        self.assertEqual(response.status_code, 403) # Forbidden for non-managers # type: ignore
        self.assertFalse(self.user3.groups.filter(name="Manager").exists())

    def test_anonymous_user_cannot_add_user_to_delivery_crew_group(self):
        # Unauthenticate the client
        self.client.logout()
        response = self.client.post(DELIVERY_CREW, {"username": "nonexistentuser"}, format = "json")
        self.assertEqual(response.status_code, 401) # Should return 401 Unauthenticated # type: ignore
        
    # === Remove Users from the Manager Group Tests ===

    def test_manager_removes_user_from_delivery_crew_group(self):
        # Add user2 to manager group first
        response = self.client.post(DELIVERY_CREW, {"username": self.user2.username}, format = "json")
        response = self.client.delete(DELIVERY_CREW, {"username": self.user2.username}, format = "json")
        self.assertEqual(response.status_code, 200) # type: ignore
        self.assertFalse(self.user2.groups.filter(name = "Manager").exists())

    def test_manager_cannot_remove_missing_user_from_delivery_crew_group(self):
        # Create a user not in the manager group
        missing_user = User.objects.create_user(username = "missinguser", password = self.password)
        response = self.client.delete(DELIVERY_CREW, {"username": missing_user.username}, format = "json")
        self.assertEqual(response.status_code, 200) # Should still return 200 OK    # type: ignore
        self.assertFalse(missing_user.groups.filter(name = "Manager").exists())
        
    def test_unauthorized_user_cannot_remove_user_from_delivery_crew_group(self):
        # Add user2 to manager group first
        self.user2.groups.add(self.manager_group)
        # Create and authenticate as non-manager user
        User.objects.create_user(username="unauthorized2", password=self.password)
        token = self.get_auth_token(username="unauthorized2", password=self.password)
        self.authenticate_client(token)
        response = self.client.delete(DELIVERY_CREW, {"username": self.user2.username}, format="json")
        self.assertEqual(response.status_code, 403) # Forbidden for non-managers # type: ignore
        self.assertTrue(self.user2.groups.filter(name="Manager").exists())
        
    def test_anonymous_user_cannot_remove_user_from_delivery_crew_group(self):
        # Add user2 to manager group first
        self.user2.groups.add(self.manager_group)
        # Unauthenticate the client
        self.client.logout()
        response = self.client.delete(DELIVERY_CREW, {"username": "nonexistentuser"}, format = "json")
        self.assertEqual(response.status_code, 401) # Should return 401 Unauthenticated # type: ignore
        
    # === Delivery Crew Input Validation Tests ===

    def test_add_user_to_delivery_crew_missing_username(self):
        response = self.client.post(DELIVERY_CREW, {}, format="json")
        self.assertEqual(response.status_code, 400)  # Bad Request # type: ignore

    def test_add_user_to_delivery_crew_empty_username(self):
        response = self.client.post(DELIVERY_CREW, {"username": ""}, format="json")
        self.assertEqual(response.status_code, 400)  # Bad Request # type: ignore

    def test_add_user_to_delivery_crew_nonexistent_username(self):
        response = self.client.post(DELIVERY_CREW, {"username": "nonexistentuser"}, format="json")
        self.assertEqual(response.status_code, 404)  # Not Found # type: ignore

    def test_add_user_to_delivery_crew_invalid_field_name(self):
        response = self.client.post(DELIVERY_CREW, {"user": self.user2.username}, format="json")
        self.assertEqual(response.status_code, 400)  # Bad Request # type: ignore

    def test_remove_user_from_delivery_crew_missing_username(self):
        response = self.client.delete(DELIVERY_CREW, {}, format="json")
        self.assertEqual(response.status_code, 400)  # Bad Request # type: ignore

    def test_remove_user_from_delivery_crew_empty_username(self):
        response = self.client.delete(DELIVERY_CREW, {"username": ""}, format="json")
        self.assertEqual(response.status_code, 400)  # Bad Request # type: ignore

    def test_remove_user_from_delivery_crew_nonexistent_username(self):
        response = self.client.delete(DELIVERY_CREW, {"username": "nonexistentuser"}, format="json")
        self.assertEqual(response.status_code, 404)  # Not Found # type: ignore

    def test_remove_user_from_delivery_crew_invalid_field_name(self):
        response = self.client.delete(DELIVERY_CREW, {"user": self.user2.username}, format="json")
        self.assertEqual(response.status_code, 400)  # Bad Request # type: ignore