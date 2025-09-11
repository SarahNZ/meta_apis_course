from base_test import BaseAPITestCase
from endpoints import MENU_ITEMS
from rest_framework import status
from LittleLemonAPI.models import Category, MenuItem

class MenuItemsTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        
        """
        Create category and menu items for read access only. Don't delete or modify them
        """
        self.category_pizza = Category.objects.create(slug="pizza", title="Pizza")
        self.category_dessert = Category.objects.create(slug="pizza", title="Dessert")
        MenuItem.objects.create(
            title="Margherita", price=10, featured=True, category=self.category_pizza
        )
        MenuItem.objects.create(
            title="Pepperoni", price=12, featured=False, category=self.category_pizza
        )
        MenuItem.objects.create(
            title="Apple Pie", price=11, featured=False, category=self.category_dessert
        )
        
        # Authenticate client as default test user (self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        
    # === List Menu Items Tests ===
        
    def test_list_auth_user_can_view(self):
        response = self.client.get(MENU_ITEMS)
        self.print_json(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # type: ignore
        all_menu_items = [menu_item.title for menu_item in MenuItem.objects.all()]
        response_menu_items = [menu_item["title"] for menu_item in response.json()] # type: ignore
        for menu_item in all_menu_items:
            self.assertIn(menu_item, response_menu_items) 
            
    def test_list_anon_user_cannot_view(self):
        self.client.credentials()  # remove authentication
        response = self.client.get(MENU_ITEMS)
        self.print_json(response)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) # type: ignore
        
    def test_list_filter_by_category(self):
        url = f"{MENU_ITEMS}?category__title=Pizza"
        response = self.client.get(url)
        self.print_json(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # type: ignore
        
        pizza_items = [menu_item.title for menu_item in MenuItem.objects.filter(category__title = "Pizza")]
        non_pizza_items = [menu_item.title for menu_item in MenuItem.objects.exclude(category__title = "Pizza")]
        response_titles = [menu_item["title"] for menu_item in response.json()] # type: ignore
        
        for item in pizza_items:
            self.assertIn(item, response_titles)
            
        for item in non_pizza_items:
            self.assertNotIn(item, response_titles)
       
    # === Detail Menu Item Tests ===
                
    def test_detail_auth_user_can_view(self):
        margherita = MenuItem.objects.get(title="Margherita")
        url = f"{MENU_ITEMS}{margherita.id}/" # type: ignore
        response = self.client.get(url)
        self.print_json(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # type: ignore
        self.assertEqual(response.json()["title"], margherita.title) # type: ignore
        
    def test_detail_anon_user_cannot_view(self):
        margherita = MenuItem.objects.get(title="Margherita")
        self.client.credentials()  # remove authentication
        url = f"{MENU_ITEMS}{margherita.id}/" # type: ignore
        response = self.client.get(url)
        self.print_json(response)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) # type: ignore