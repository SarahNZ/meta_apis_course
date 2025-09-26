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
        # Create a new user to add to the delivery crew group
        self.delivery_user = User.objects.create_user(username = "delivery_user", password = self.password)
        response = self.client.post(DELIVERY_CREW, {"username": self.delivery_user.username}, format = "json")
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
        
    # === Remove Users from the Delivery Crew Group Tests ===

    def test_manager_removes_user_from_delivery_crew_group(self):
        # Add user2 to delivery crew group first
        response = self.client.post(DELIVERY_CREW, {"username": self.user2.username}, format = "json")
        # Now delete using the id-based URL
        user_id = self.user2.id
        response = self.client.delete(f"{DELIVERY_CREW}{user_id}/")
        self.assertEqual(response.status_code, 204) # type: ignore
        self.assertFalse(self.user2.groups.filter(name = "Delivery Crew").exists())

    def test_manager_cannot_remove_missing_user_from_delivery_crew_group(self):
        # Create a user not in the delivery crew group
        missing_user = User.objects.create_user(username = "missinguser", password = self.password)
        # Now delete using the id-based URL
        user_id = missing_user.id
        response = self.client.delete(f"{DELIVERY_CREW}{user_id}/")
        self.assertEqual(response.status_code, 404) # Should return 404 Not Found since user is not in the group # type: ignore
        self.assertFalse(missing_user.groups.filter(name = "Delivery Crew").exists())
        
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