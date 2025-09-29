from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status  
from rest_framework.test import APIClient  

from base_test import BaseAPITestCase
from endpoints import CART, ORDERS  
from LittleLemonAPI.models import Cart, Category, MenuItem, Order  

class OrderTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()

        # Categories
        self.category_pizza = Category.objects.create(slug="pizza", title="Pizza")
        self.category_dessert = Category.objects.create(slug="dessert", title="Dessert")

        # Menu items
        MenuItem.objects.create(
            title="Margherita",
            price=10,
            featured=True,
            category=self.category_pizza
        )
        MenuItem.objects.create(
            title="Pepperoni",
            price=12,
            featured=False,
            category=self.category_pizza
        )
        MenuItem.objects.create(
            title="Apple Pie",
            price=11,
            featured=False,
            category=self.category_dessert
        )

        # Authenticate default user
        token = self.get_auth_token()
        self.authenticate_client(token)
    
    def test_view_empty_list_of_orders(self):
        response = self.client.get(ORDERS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
    
    # def test_place_an_order(self):
    #     # Arrange: Get menu item
    #     menu_item = get_object_or_404(MenuItem, title="Margherita")
    #     data = {"menuitem": menu_item.id, "quantity": 1}  # type: ignore

    #     # Act: Add item to cart
    #     response = self.client.post(CART, data, format="json")
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore

    #     # Act: Create order items from cart items