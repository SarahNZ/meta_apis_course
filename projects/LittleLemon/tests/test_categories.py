from django.shortcuts import get_object_or_404
from rest_framework import status
from base_test import BaseAPITestCase
from endpoints import CATEGORIES
from LittleLemonAPI.models import Category


class CategoriesTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()

        # Create categories
        self.category_pizza = Category.objects.create(slug="pizza", title="Pizza")
        self.category_dessert = Category.objects.create(slug="dessert", title="Dessert")

        # Authenticate default user
        token = self.get_auth_token()
        self.authenticate_client(token)

    # === View List Tests ===
    def test_authenticated_user_can_view_categories(self):
        # AAA: Arrange-Act-Assert

        # Act
        response = self.client.get(CATEGORIES)

        # Assert: Status and contents
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        categories = response.json()  # type: ignore
        titles = [c["title"] for c in categories]  # type: ignore
        for c in Category.objects.all():
            self.assertIn(c.title, titles)

    def test_anon_user_cannot_view_categories(self):
        # AAA

        # Arrange
        self.client.credentials()

        # Act
        response = self.client.get(CATEGORIES)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore

    # === Detail Tests ===
    def test_authenticated_user_can_view_category_detail(self):
        # AAA

        # Arrange
        category = get_object_or_404(Category, id=self.category_pizza.id)
        url = f"{CATEGORIES}{category.id}/"  # type: ignore

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        data = response.json()  # type: ignore
        self.assertEqual(data["title"], category.title)  # type: ignore

    def test_anon_user_cannot_view_category_detail(self):
        # AAA

        # Arrange
        self.client.credentials()
        category = get_object_or_404(Category, id=self.category_pizza.id)
        url = f"{CATEGORIES}{category.id}/"  # type: ignore

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore

    # === Create / POST Tests ===
    def test_admin_user_can_create_category(self):
        # AAA

        # Arrange
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        data = {"slug": "salads", "title": "Salads"}

        # Act
        response = self.client.post(CATEGORIES, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        self.assertTrue(Category.objects.filter(title="Salads").exists())  # type: ignore

    def test_non_staff_user_cannot_create_category(self):
        # AAA

        # Arrange
        self.user1.is_staff = False
        self.user1.save()
        token = self.get_auth_token()
        self.authenticate_client(token)
        data = {"slug": "soups", "title": "Soups"}

        # Act
        response = self.client.post(CATEGORIES, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type: ignore
        self.assertFalse(Category.objects.filter(title="Soups").exists())  # type: ignore

    def test_anon_user_cannot_create_category(self):
        # AAA

        # Arrange
        self.client.credentials()
        data = {"slug": "drinks", "title": "Drinks"}

        # Act
        response = self.client.post(CATEGORIES, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore
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