from base_test_utils import BaseAPITestCase
from endpoints import MENU_ITEMS
from rest_framework import status
from LittleLemonAPI.models import Category, MenuItem

class MenuItemsTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        
        """
        Create category and menu items for view tests. Don't delete or modify them
        """
        self.category = Category.objects.create(slug="pizza", title="Pizza")
        MenuItem.objects.create(
            title="Margherita", price=10, featured=True, category=self.category
        )
        MenuItem.objects.create(
            title="Pepperoni", price=12, featured=False, category=self.category
        )
        
        # Authenticate client as default test user (self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        
    # === List Menu Items Tests ===
        
    def test_list_auth_user_can_view(self):
        response = self.client.get(MENU_ITEMS)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # type: ignore
        all_menu_items = [menu_item.title for menu_item in MenuItem.objects.all()]
        response_menu_items = [menu_item["title"] for menu_item in response.json()] # type: ignore
        for menu_item in all_menu_items:
            self.assertIn(menu_item, response_menu_items) 
            
    def test_list_anon_user_cannot_view(self):
        self.client.credentials()  # remove authentication
        response = self.client.get(MENU_ITEMS)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) # type: ignore
       
    # === Detail Menu Item Tests ===
                
    def test_detail_auth_user_can_view(self):
        margherita = MenuItem.objects.get(title="Margherita")
        url = f"{MENU_ITEMS}{margherita.id}/" # type: ignore
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # type: ignore
        self.assertEqual(response.json()["title"], margherita.title) # type: ignore
        
    def test_detail_anon_user_cannot_view(self):
        margherita = MenuItem.objects.get(title="Margherita")
        self.client.credentials()  # remove authentication
        url = f"{MENU_ITEMS}{margherita.id}/" # type: ignore
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) # type: ignore