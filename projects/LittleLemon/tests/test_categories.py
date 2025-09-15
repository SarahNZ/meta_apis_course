from base_test import BaseAPITestCase
from endpoints import CATEGORIES
from rest_framework import status
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
    def test_list_auth_user_can_view(self):
        response = self.client.get(CATEGORIES)
        self.print_json(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        titles = [item["title"] for item in response.json()]  # type:ignore
        for c in Category.objects.all():
            self.assertIn(c.title, titles)

    def test_list_anon_user_cannot_view(self):
        self.client.credentials()
        response = self.client.get(CATEGORIES)
        self.print_json(response)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type:ignore

    # === Detail Tests ===
    def test_detail_auth_user_can_view(self):
        url = f"{CATEGORIES}{self.category_pizza.id}/"  # type:ignore
        response = self.client.get(url)
        self.print_json(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        self.assertEqual(response.json()["title"], self.category_pizza.title)  # type:ignore

    def test_detail_anon_user_cannot_view(self):
        self.client.credentials()
        url = f"{CATEGORIES}{self.category_pizza.id}/"  # type:ignore
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type:ignore

    # === Create / POST Tests ===
    def test_auth_admin_user_can_add_category(self):
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        data = {"slug": "salads", "title": "Salads"}
        response = self.client.post(CATEGORIES, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type:ignore
        self.assertTrue(Category.objects.filter(title="Salads").exists())  # type:ignore

    def test_auth_non_staff_user_cannot_add_category(self):
        self.user1.is_staff = False
        self.user1.save()
        token = self.get_auth_token()
        self.authenticate_client(token)
        data = {"slug": "soups", "title": "Soups"}
        response = self.client.post(CATEGORIES, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type:ignore
        self.assertFalse(Category.objects.filter(title="Soups").exists())

    def test_anon_user_cannot_add_category(self):
        self.client.credentials()
        data = {"slug": "drinks", "title": "Drinks"}
        response = self.client.post(CATEGORIES, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type:ignore
        self.assertFalse(Category.objects.filter(title="Drinks").exists())

    # === Update / PATCH / PUT Tests ===
    def test_auth_admin_user_can_patch_category(self):
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)

        data = {"title": "Updated Pizza"}
        url = f"{CATEGORIES}{self.category_pizza.id}/"  # type:ignore
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        self.category_pizza.refresh_from_db()
        self.assertEqual(self.category_pizza.title, "Updated Pizza")

    def test_auth_non_staff_user_cannot_update_category(self):
        self.user1.is_staff = False
        self.user1.save()
        token = self.get_auth_token()
        self.authenticate_client(token)

        data = {"title": "Should Not Update"}
        url = f"{CATEGORIES}{self.category_pizza.id}/"  # type:ignore
        response = self.client.patch(url, data, format="json") 
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type:ignore

    def test_anon_user_cannot_update_category(self):
        self.client.credentials()
        data = {"title": "Should Not Update"}
        url = f"{CATEGORIES}{self.category_pizza.id}/"  # type:ignore
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type:ignore

    # === Delete / DELETE Tests ===
    def test_admin_user_cannot_delete_category(self):
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        url = f"{CATEGORIES}{self.category_pizza.id}/"  # type:ignore
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type:ignore
        self.assertTrue(Category.objects.filter(id=self.category_pizza.id).exists())  # type:ignore

    def test_non_staff_user_cannot_delete_category(self):
        token = self.get_auth_token()
        self.authenticate_client(token)
        url = f"{CATEGORIES}{self.category_pizza.id}/"  # type:ignore
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type:ignore
        self.assertTrue(Category.objects.filter(id=self.category_pizza.id).exists())  # type:ignore

    def test_anon_user_cannot_delete_category(self):
        self.client.credentials()
        url = f"{CATEGORIES}{self.category_pizza.id}/"  # type:ignore
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type:ignore
        self.assertTrue(Category.objects.filter(id=self.category_pizza.id).exists())  # type:ignore

    # === Validation Tests ===
    def test_create_category_missing_title(self):
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        data = {"slug": "invalid"}
        response = self.client.post(CATEGORIES, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type:ignore
        self.assertIn("title", response.json())  # type:ignore
        
    # === Validation Tests ===
    def test_cannot_create_category_duplicate_title(self):
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        Category.objects.create(slug="unique", title="Unique")
        data = {"slug": "unique2", "title": "Unique"}
        response = self.client.post(CATEGORIES, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type:ignore

    def test_create_category_duplicate_slug(self):
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        Category.objects.create(slug="unique", title="Unique")
        data = {"slug": "unique", "title": "Duplicate"}
        response = self.client.post(CATEGORIES, data, format="json")
        print(response.status_code, response.json())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type:ignore