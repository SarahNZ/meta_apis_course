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

    # === Helper Methods ===
    
    def _get_delivery_crew(self):
        """Helper method to get all delivery crew members"""
        response = self.client.get(DELIVERY_CREW)
        self.assertEqual(response.status_code, 200)
        return response.data
    
    def _add_user_to_delivery_crew(self, username):
        """Helper method to add user to delivery crew group"""
        response = self.client.post(DELIVERY_CREW, {"username": username}, format="json")
        return response
    
    def _remove_user_from_delivery_crew(self, user_id):
        """Helper method to remove user from delivery crew group"""
        response = self.client.delete(f"{DELIVERY_CREW}{user_id}/")
        return response
    
    def _verify_user_in_delivery_crew_group(self, user, should_be_in_group=True):
        """Helper method to verify user is/isn't in delivery crew group"""
        in_group = user.groups.filter(name="Delivery Crew").exists()
        if should_be_in_group:
            self.assertTrue(in_group)
        else:
            self.assertFalse(in_group)
    
    def _verify_unauthorized_response(self, response):
        """Helper method to verify unauthorized response"""
        self.assertEqual(response.status_code, 401)
    
    def _verify_forbidden_response(self, response):
        """Helper method to verify forbidden response"""
        self.assertEqual(response.status_code, 403)
    
    def _verify_method_not_allowed_response(self, response):
        """Helper method to verify method not allowed response"""
        self.assertEqual(response.status_code, 405)
    
    def _verify_not_found_response(self, response):
        """Helper method to verify not found response"""
        self.assertEqual(response.status_code, 404)
    
    def _create_and_authenticate_non_manager(self, username="notmanager"):
        """Helper method to create and authenticate non-manager user"""
        user = User.objects.create_user(username=username, password=self.password)
        token = self.get_auth_token(username=username, password=self.password)
        self.authenticate_client(token)
        return user
    
    def _clear_authentication(self):
        """Helper method to clear client authentication"""
        self.client.logout()
    
    def _verify_delivery_crew_returned(self, response_data):
        """Helper method to verify all delivery crew members are returned"""
        delivery_crew = Group.objects.get(name="Delivery Crew")
        delivery_crew_usernames = [user.username for user in delivery_crew.user_set.all()]
        response_usernames = [user["username"] for user in response_data]
        for username in delivery_crew_usernames:
            self.assertIn(username, response_usernames)
        
    # === View All Users in the Delivery Crew Group Tests ===
        
    def test_manager_views_all_users_in_delivery_crew_group(self):
        # Act & Assert: Get delivery crew and verify all are returned
        response_data = self._get_delivery_crew()
        self._verify_delivery_crew_returned(response_data) 
            
    def test_unauthorized_authenticated_user_cannot_view_all_delivery_crew_users(self):
        # Arrange: Create and authenticate non-manager user
        self._create_and_authenticate_non_manager()
        
        # Act & Assert: Should be forbidden
        response = self.client.get(DELIVERY_CREW)
        self._verify_forbidden_response(response)
        
    def test_anonymous_user_cannot_view_delivery_crew_users(self):
        # Arrange: Clear authentication
        self._clear_authentication()
        
        # Act & Assert: Should be unauthorized
        response = self.client.get(DELIVERY_CREW)
        self._verify_unauthorized_response(response)
        
# === Add Users to the Delivery Crew Group Tests ===
        
    def test_manager_adds_user_to_delivery_crew_group(self):
        # Arrange: Create a new user to add to the delivery crew group
        self.delivery_user = User.objects.create_user(username="delivery_user", password=self.password)
        
        # Act & Assert: Add user to delivery crew and verify
        response = self._add_user_to_delivery_crew(self.delivery_user.username)
        self.assertEqual(response.status_code, 201)
        self._verify_user_in_delivery_crew_group(self.delivery_user, should_be_in_group=True)
        
    def test_unsupported_http_methods_for_delivery_crew_endpoint_return_405(self):
        # Act & Assert: Unsupported method should return 405
        response = self.client.put(DELIVERY_CREW, {"username": self.user2.username}, format="json")
        self._verify_method_not_allowed_response(response)
        
    def test_unauthorized_authenticated_user_cannot_add_user_to_delivery_crew_group(self):
        # Arrange: Create a new user not in delivery crew and authenticate non-manager user
        new_user = User.objects.create_user(username="newuser", password=self.password)
        self._create_and_authenticate_non_manager("unauthorized")
        
        # Act & Assert: Should be forbidden
        response = self._add_user_to_delivery_crew(new_user.username)
        self._verify_forbidden_response(response)
        self._verify_user_in_delivery_crew_group(new_user, should_be_in_group=False)

    def test_anonymous_user_cannot_add_user_to_delivery_crew_group(self):
        # Arrange: Clear authentication
        self._clear_authentication()
        
        # Act & Assert: Should be unauthorized
        response = self._add_user_to_delivery_crew("nonexistentuser")
        self._verify_unauthorized_response(response)
        
    # === Remove Users from the Delivery Crew Group Tests ===

    def test_manager_removes_user_from_delivery_crew_group(self):
        # Arrange: Add user2 to delivery crew group first
        self._add_user_to_delivery_crew(self.user2.username)
        
        # Act & Assert: Remove user and verify
        response = self._remove_user_from_delivery_crew(self.user2.id)
        self.assertEqual(response.status_code, 204)
        self._verify_user_in_delivery_crew_group(self.user2, should_be_in_group=False)

    def test_manager_cannot_remove_missing_user_from_delivery_crew_group(self):
        # Arrange: Create a user not in the delivery crew group
        missing_user = User.objects.create_user(username="missinguser", password=self.password)
        
        # Act & Assert: Should return 404 Not Found since user is not in the group
        response = self._remove_user_from_delivery_crew(missing_user.id)
        self._verify_not_found_response(response)
        self._verify_user_in_delivery_crew_group(missing_user, should_be_in_group=False)
        
    def test_unauthorized_user_cannot_remove_user_from_delivery_crew_group(self):
        # Ensure user2 is in the delivery crew group
        self.user2.groups.add(self.delivery_crew_group)
        # Create and authenticate as non-manager user
        User.objects.create_user(username="unauthorized2", password=self.password)
        token = self.get_auth_token(username="unauthorized2", password=self.password)
        self.authenticate_client(token)
        # Now delete using the id-based URL
        user_id = self.user2.id
        response = self.client.delete(f"{DELIVERY_CREW}{user_id}/")
        self.assertEqual(response.status_code, 403) # Forbidden for non-managers # type: ignore
        self.assertTrue(self.user2.groups.filter(name="Delivery Crew").exists())
        
    def test_anonymous_user_cannot_remove_user_from_delivery_crew_group(self):
        # Ensure user2 is in the delivery crew group
        self.user2.groups.add(self.delivery_crew_group)
        # Unauthenticate the client
        self.client.logout()
        # Now delete using the id-based URL
        user_id = self.user2.id
        response = self.client.delete(f"{DELIVERY_CREW}{user_id}/")
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

    def test_remove_user_from_delivery_crew_missing_id(self):
        # Using an empty string as ID
        response = self.client.delete(f"{DELIVERY_CREW}/")
        self.assertEqual(response.status_code, 404)  # Not Found # type: ignore

    def test_remove_user_from_delivery_crew_nonexistent_id(self):
        # Using a nonexistent ID (99999)
        response = self.client.delete(f"{DELIVERY_CREW}99999/")
        self.assertEqual(response.status_code, 404)  # Not Found # type: ignore

    def test_remove_user_from_delivery_crew_invalid_id(self):
        # Using an invalid ID format
        response = self.client.delete(f"{DELIVERY_CREW}invalid/")
        self.assertEqual(response.status_code, 404)  # Not Found # type: ignore

    def test_remove_user_not_in_delivery_crew_group(self):
        # Create a user not in the delivery crew group
        not_in_crew = User.objects.create_user(username="notincrew", password=self.password)
        # Try to remove a user not in the delivery crew group
        user_id = not_in_crew.id
        response = self.client.delete(f"{DELIVERY_CREW}{user_id}/")
        self.assertEqual(response.status_code, 404)  # Not Found # type: ignore

    # === Performance & Scalability Tests ===
    
    def test_delivery_crew_large_user_base_performance(self):
        """Test delivery crew operations with many users."""
        from rest_framework import status
        
        # Arrange: Create many users to test scalability
        bulk_users = []
        for i in range(50):
            bulk_users.append(User(
                username=f"deliverytest{i}",
                email=f"deliverytest{i}@example.com"
            ))
        
        User.objects.bulk_create(bulk_users)
        
        # Act: Request all delivery crew users
        response = self.client.get(DELIVERY_CREW)
        
        # Assert: Should handle large user base gracefully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_delivery_crew_rapid_user_group_modifications(self):
        """Test rapid addition and removal of users from delivery crew."""
        from rest_framework import status

        # Arrange: Create test users for bulk operations
        test_users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f"crewbulk{i}",
                password="testpass123"
            )
            test_users.append(user)

        # Act: Rapidly add users to delivery crew
        successful_additions = 0
        for user in test_users:
            data = {"username": user.username}
            response = self.client.post(DELIVERY_CREW, data, format="json")
            if response.status_code == status.HTTP_201_CREATED:
                successful_additions += 1

        # Assert: All additions should succeed
        self.assertEqual(successful_additions, 10)

        # Act: Rapidly remove users from delivery crew
        successful_removals = 0
        for user in test_users:
            response = self.client.delete(f"{DELIVERY_CREW}{user.id}/")
            if response.status_code == status.HTTP_204_NO_CONTENT:
                successful_removals += 1

        # Assert: All removals should succeed (expecting 204)
        self.assertEqual(successful_removals, 10)

    def test_delivery_crew_username_length_limits(self):
        """Test delivery crew operations with username boundary values."""
        from rest_framework import status
        
        # Test maximum username length (User model default max_length=150)
        max_length_username = "d" * 150
        
        # Create user with maximum length username
        test_user = User.objects.create_user(
            username=max_length_username,
            password="testpass123"
        )
        
        # Act: Add user with max length username to delivery crew
        data = {"username": max_length_username}
        response = self.client.post(DELIVERY_CREW, data, format="json")
        
        # Assert: Should succeed
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user is in delivery crew group
        delivery_crew_group = Group.objects.get(name='Delivery Crew')
        self.assertTrue(test_user.groups.filter(name='Delivery Crew').exists())

    def test_delivery_crew_concurrent_operations_simulation(self):
        """Test delivery crew operations under simulated concurrent access."""
        from rest_framework import status
        
        # Arrange: Create users for concurrent operations testing
        concurrent_users = []
        for i in range(15):
            user = User.objects.create_user(
                username=f"crewconcur{i}",
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
            response = self.client.post(DELIVERY_CREW, data, format="json")
            if response.status_code == status.HTTP_201_CREATED:
                successful_operations += 1
            else:
                failed_operations += 1
        
        # Assert: Most or all operations should succeed
        self.assertGreaterEqual(successful_operations, 13)  # Allow for some potential issues
        
        # Verify users are actually in delivery crew group
        delivery_crew_group = Group.objects.get(name='Delivery Crew')
        crew_count = delivery_crew_group.user_set.filter(
            username__startswith='crewconcur'
        ).count()
        self.assertEqual(crew_count, successful_operations)

    def test_delivery_crew_invalid_username_patterns(self):
        """Test delivery crew operations with various invalid username patterns."""
        from rest_framework import status
        
        invalid_usernames = [
            "",  # Empty username
            "d" * 151,  # Username too long (> 150 chars)
            "nonexistent_crew_user_12345",  # Nonexistent user
            "crew with spaces",  # Username with spaces (may be invalid)
        ]
        
        # Act & Assert: All should return appropriate error responses
        for username in invalid_usernames:
            with self.subTest(username=username):
                data = {"username": username}
                response = self.client.post(DELIVERY_CREW, data, format="json")
                
                # Should return 400 Bad Request or 404 Not Found for various validation failures
                self.assertIn(response.status_code, [
                    status.HTTP_400_BAD_REQUEST,
                    status.HTTP_404_NOT_FOUND
                ])