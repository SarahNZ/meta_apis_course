from django.shortcuts import get_object_or_404
from rest_framework import status
from base_test import BaseAPITestCase
from endpoints import CATEGORIES
from LittleLemonAPI.models import Category, MenuItem


class CategoriesTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()

        # Create categories
        self.category_pizza = Category.objects.create(slug="pizza", title="Pizza")
        self.category_dessert = Category.objects.create(slug="dessert", title="Dessert")

        # Authenticate default user
        token = self.get_auth_token()
        self.authenticate_client(token)

    # === Helper Methods ===
    
    def _get_categories(self):
        """Helper method to get categories list"""
        response = self.client.get(CATEGORIES)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.json()
    
    def _get_category_detail(self, category_id):
        """Helper method to get category detail"""
        url = f"{CATEGORIES}{category_id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.json()
    
    def _create_category(self, data):
        """Helper method to create category"""
        response = self.client.post(CATEGORIES, data, format="json")
        return response
    
    def _verify_category_created(self, response, expected_title):
        """Helper method to verify category was created"""
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Category.objects.filter(title=expected_title).exists())
    
    def _verify_unauthorized_response(self, response):
        """Helper method to verify unauthorized response"""
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def _verify_forbidden_response(self, response):
        """Helper method to verify forbidden response"""
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def _clear_authentication(self):
        """Helper method to clear client authentication"""
        self.client.credentials()
    
    def _make_user_staff(self):
        """Helper method to make user staff"""
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
    
    def _verify_categories_contain_all_expected(self, categories):
        """Helper method to verify categories contain all expected items"""
        titles = [c["title"] for c in categories]
        for category in Category.objects.all():
            self.assertIn(category.title, titles)

    # === View List Tests ===
    def test_authenticated_user_can_view_categories(self):
        # Act & Assert: Get categories and verify contents
        categories = self._get_categories()
        self._verify_categories_contain_all_expected(categories)

    def test_anon_user_cannot_view_categories(self):
        # Arrange: Clear authentication
        self._clear_authentication()

        # Act & Assert: Should be unauthorized
        response = self.client.get(CATEGORIES)
        self._verify_unauthorized_response(response)

    # === Detail Tests ===
    def test_authenticated_user_can_view_category_detail(self):
        # Arrange: Get category
        category = get_object_or_404(Category, id=self.category_pizza.id)

        # Act & Assert: Get category detail and verify
        data = self._get_category_detail(category.id)
        self.assertEqual(data["title"], category.title)

    def test_anon_user_cannot_view_category_detail(self):
        # Arrange: Clear authentication and get category
        self._clear_authentication()
        category = get_object_or_404(Category, id=self.category_pizza.id)

        # Act & Assert: Should be unauthorized
        response = self.client.get(f"{CATEGORIES}{category.id}/")
        self._verify_unauthorized_response(response)

    # === Create / POST Tests ===
    def test_admin_user_can_create_category(self):
        # Arrange: Make user staff and prepare data
        self._make_user_staff()
        data = {"slug": "salads", "title": "Salads"}

        # Act & Assert: Create category and verify
        response = self._create_category(data)
        self._verify_category_created(response, "Salads")

    def test_non_staff_user_cannot_create_category(self):
        # Arrange: Ensure user is not staff and prepare data
        self.user1.is_staff = False
        self.user1.save()
        token = self.get_auth_token()
        self.authenticate_client(token)
        data = {"slug": "soups", "title": "Soups"}

        # Act & Assert: Should be forbidden
        response = self._create_category(data)
        self._verify_forbidden_response(response)
        self.assertFalse(Category.objects.filter(title="Soups").exists())

    def test_anon_user_cannot_create_category(self):
        # Arrange: Clear authentication and prepare data
        self._clear_authentication()
        data = {"slug": "drinks", "title": "Drinks"}

        # Act & Assert: Should be unauthorized
        response = self._create_category(data)
        self._verify_unauthorized_response(response)
        self.assertFalse(Category.objects.filter(title="Drinks").exists())  # type: ignore

    # === Update / PATCH Tests ===
    def test_admin_user_can_patch_category(self):
        # AAA

        # Arrange
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        category = get_object_or_404(Category, id=self.category_pizza.id)
        url = f"{CATEGORIES}{category.id}/"  # type: ignore
        data = {"title": "Updated Pizza"}

        # Act
        response = self.client.patch(url, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        category.refresh_from_db()
        self.assertEqual(category.title, "Updated Pizza")  # type: ignore

    def test_non_staff_user_cannot_patch_category(self):
        # AAA

        # Arrange
        self.user1.is_staff = False
        self.user1.save()
        token = self.get_auth_token()
        self.authenticate_client(token)
        category = get_object_or_404(Category, id=self.category_pizza.id)
        url = f"{CATEGORIES}{category.id}/"  # type: ignore
        data = {"title": "Should Not Update"}

        # Act
        response = self.client.patch(url, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type: ignore
        category.refresh_from_db()
        self.assertNotEqual(category.title, "Should Not Update")  # type: ignore

    def test_anon_user_cannot_patch_category(self):
        # AAA

        # Arrange
        self.client.credentials()
        category = get_object_or_404(Category, id=self.category_pizza.id)
        url = f"{CATEGORIES}{category.id}/"  # type: ignore
        data = {"title": "Should Not Update"}

        # Act
        response = self.client.patch(url, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore
        category.refresh_from_db()
        self.assertNotEqual(category.title, "Should Not Update")  # type: ignore

    # === Delete / DELETE Tests ===
    def test_admin_user_cannot_delete_category(self):
        # AAA

        # Arrange
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        category = get_object_or_404(Category, id=self.category_pizza.id)
        url = f"{CATEGORIES}{category.id}/"  # type: ignore

        # Act
        response = self.client.delete(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type: ignore
        self.assertTrue(Category.objects.filter(id=category.id).exists())  # type: ignore

    def test_non_staff_user_cannot_delete_category(self):
        # AAA

        # Arrange
        token = self.get_auth_token()
        self.authenticate_client(token)
        category = get_object_or_404(Category, id=self.category_pizza.id)
        url = f"{CATEGORIES}{category.id}/"  # type: ignore

        # Act
        response = self.client.delete(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type: ignore
        self.assertTrue(Category.objects.filter(id=category.id).exists())  # type: ignore

    def test_anon_user_cannot_delete_category(self):
        # AAA

        # Arrange
        self.client.credentials()
        category = get_object_or_404(Category, id=self.category_pizza.id)
        url = f"{CATEGORIES}{category.id}/"  # type: ignore

        # Act
        response = self.client.delete(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore
        self.assertTrue(Category.objects.filter(id=category.id).exists())  # type: ignore

    # === Validation Tests ===
    def test_create_category_missing_title(self):
        # AAA

        # Arrange
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        data = {"slug": "invalid"}

        # Act
        response = self.client.post(CATEGORIES, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore
        self.assertIn("title", response.json())  # type: ignore

    def test_cannot_create_category_duplicate_title(self):
        # AAA

        # Arrange
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        Category.objects.create(slug="unique", title="Unique")
        data = {"slug": "unique2", "title": "Unique"}

        # Act
        response = self.client.post(CATEGORIES, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore
        self.assertEqual(Category.objects.filter(title="Unique").count(), 1)  # type: ignore

    def test_create_category_duplicate_slug(self):
        # AAA

        # Arrange
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        Category.objects.create(slug="unique", title="Unique")
        data = {"slug": "unique", "title": "Duplicate"}

        # Act
        response = self.client.post(CATEGORIES, data, format="json")
        print(response.status_code, response.json())

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore
        self.assertEqual(Category.objects.filter(slug="unique").count(), 1)  # type: ignore

    # === Performance & Scalability Tests ===
    
    def test_categories_large_dataset_performance(self):
        """Test categories API performance with many categories."""
        # Arrange: Create many categories to test query performance
        bulk_categories = []
        for i in range(100):
            bulk_categories.append(Category(
                slug=f"performance-category-{i}",
                title=f"Performance Category {i}"
            ))
        
        Category.objects.bulk_create(bulk_categories)
        
        # Act: Request all categories
        response = self.client.get(CATEGORIES)
        
        # Assert: Should handle large datasets gracefully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 100)  # At least our test categories

    def test_category_creation_field_limits(self):
        """Test category creation with field boundary values."""
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        
        # Test maximum title length (CharField max_length=255)
        max_length_title = "A" * 255
        data = {
            "slug": "max-length-test",
            "title": max_length_title
        }
        
        response = self.client.post(CATEGORIES, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the category was created correctly
        created_category = Category.objects.get(slug="max-length-test")
        self.assertEqual(created_category.title, max_length_title)

    def test_category_creation_exceeding_title_length_limit(self):
        """Test category creation with title exceeding field limits."""
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        
        # Test title exceeding CharField limits (> 255 chars)
        too_long_title = "A" * 256
        data = {
            "slug": "overflow-test",
            "title": too_long_title
        }
        
        response = self.client.post(CATEGORIES, data, format="json")
        # Should return 400 Bad Request due to CharField validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
        
        # Verify no category was created
        self.assertFalse(Category.objects.filter(slug="overflow-test").exists())

    def test_category_slug_validation_limits(self):
        """Test category slug validation with various formats."""
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        
        # Test valid slug patterns
        valid_slugs = [
            "simple",
            "with-dashes",
            "with123numbers", 
            "a" * 50  # SlugField default max_length is 50
        ]
        
        for i, slug in enumerate(valid_slugs):
            with self.subTest(slug=slug):
                data = {
                    "slug": slug,
                    "title": f"Valid Slug Test {i}"
                }
                response = self.client.post(CATEGORIES, data, format="json")
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test invalid slug patterns  
        invalid_slugs = [
            "with spaces",  # Spaces not allowed
            "with@symbols",  # Special characters not allowed
            "a" * 51  # Exceeds default SlugField max_length
        ]
        
        for slug in invalid_slugs:
            with self.subTest(slug=slug):
                data = {
                    "slug": slug,
                    "title": f"Invalid Slug Test {slug[:10]}"
                }
                response = self.client.post(CATEGORIES, data, format="json")
                # Should return 400 Bad Request due to slug validation
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('slug', response.data)

        # Test that underscores ARE allowed (per Django SlugField default)
        data = {
            "slug": "with_underscores",
            "title": "Underscores Are Valid"
        }
        response = self.client.post(CATEGORIES, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_categories_concurrent_creation_simulation(self):
        """Test categories API under simulated concurrent creation."""
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        
        # Simulate multiple rapid category creations
        operations_data = []
        for i in range(20):
            operations_data.append({
                "slug": f"concurrent-cat-{i}",
                "title": f"Concurrent Category {i}"
            })
        
        # Perform rapid sequential operations (simulating concurrent load)
        created_categories = []
        for data in operations_data:
            response = self.client.post(CATEGORIES, data, format="json")
            if response.status_code == status.HTTP_201_CREATED:
                created_categories.append(response.data['id'])
        
        # Assert: All operations should succeed (no uniqueness conflicts in this case)
        self.assertEqual(len(created_categories), 20)
        
        # Verify categories exist in database
        existing_count = Category.objects.filter(id__in=created_categories).count()
        self.assertEqual(existing_count, len(created_categories))

    def test_category_deletion_prevention_validation(self):
        """Test that category deletion is properly prevented to maintain data integrity."""
        # Note: Based on your copilot instructions, category deletion is deliberately blocked
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        
        # Create a category with associated menu items
        test_category = Category.objects.create(slug="test-delete", title="Test Delete Category")
        MenuItem.objects.create(
            title="Test Item",
            price=10.00,
            featured=False,
            category=test_category
        )
        
        # Attempt to delete the category
        url = f"{CATEGORIES}{test_category.id}/"
        response = self.client.delete(url)
        
        # Should be prevented (likely 405 Method Not Allowed or 400 Bad Request)
        self.assertIn(response.status_code, [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN
        ])
        
        # Verify category still exists
        self.assertTrue(Category.objects.filter(id=test_category.id).exists())