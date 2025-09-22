from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.test import APIClient

from base_test import BaseAPITestCase
from endpoints import CART
from LittleLemonAPI.models import Cart, Category, MenuItem


class CartTests(BaseAPITestCase):
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

    # === View and Create Cart Tests ===

    def test_authenticated_user_can_view_empty_cart(self):
        # Arrange: Clear the cart
        Cart.objects.filter(user=self.user1).delete()

        # Act: View cart
        response = self.client.get(CART)

        # Assert: Cart is empty
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(response.json(), [])  # type: ignore

        # Database-level check
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())  # type: ignore

    def test_authenticated_user_can_add_and_view_single_cart_item(self):
        # AAA: Arrange-Act-Assert
        # Arrange: Get menu item
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {
            "menuitem": menu_item.id,  # type: ignore
            "quantity": 1
        }

        # Act: Add item to cart
        response = self.client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore

        # Act: View cart
        response = self.client.get(CART)

        # Assert: Cart has exactly one correct item
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        cart_items = response.json()  # type: ignore
        self.assertEqual(len(cart_items), 1)  # type: ignore

        item = cart_items[0]
        self.assertEqual(item["menuitem"], menu_item.id)  # type: ignore
        self.assertEqual(item["menuitem_title"], menu_item.title)  # type: ignore
        self.assertEqual(item["quantity"], data["quantity"])  # type: ignore
        self.assertEqual(item["unit_price"], str(menu_item.price))  # type: ignore
        self.assertEqual(item["price"], str(menu_item.price * data["quantity"]))  # type: ignore

        # Database-level check
        self.assertEqual(
            Cart.objects.filter(user=self.user1, menuitem=menu_item).count(), 1
        )

    def test_authenticated_user_can_add_and_retrieve_two_different_cart_items(self):
        # Arrange: Get menu item
        menu_item_1 = get_object_or_404(MenuItem, title="Margherita")
        data_1 = {
            "menuitem": menu_item_1.id,  # type: ignore
            "quantity": 1
        }
        
        menu_item_2 = get_object_or_404(MenuItem, title="Apple Pie")
        data_2 = {
            "menuitem": menu_item_2.id, # type: ignore
            "quantity": 1
        }

        # Act: Add items to cart
        response = self.client.post(CART, data_1, format="json")
        print("first item:", response.json())   # type: ignore
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        response = self.client.post(CART, data_2, format="json")
        print("second item:", response.json())  # type: ignore
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore

        # Act: Retrieve cart
        response = self.client.get(CART)

        # Assert: Cart has exactly two correct items
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        cart_items = response.json()  # type: ignore
        print("cart items:", response.json())   # type: ignore
        self.assertEqual(len(cart_items), 2)  # type: ignore

        # Assert: The first cart item is correct
        item = cart_items[0]
        self.assertEqual(item["menuitem"], menu_item_1.id)  # type: ignore
        self.assertEqual(item["menuitem_title"], menu_item_1.title)  # type: ignore
        self.assertEqual(item["quantity"], data_1["quantity"])  # type: ignore
        self.assertEqual(item["unit_price"], str(menu_item_1.price))  # type: ignore
        self.assertEqual(item["price"], str(menu_item_1.price * data_1["quantity"]))  # type: ignore
        
        # Assert: The second cart item is correct
        item = cart_items[1]
        self.assertEqual(item["menuitem"], menu_item_2.id)  # type: ignore
        self.assertEqual(item["menuitem_title"], menu_item_2.title)  # type: ignore
        self.assertEqual(item["quantity"], data_2["quantity"])  # type: ignore
        self.assertEqual(item["unit_price"], str(menu_item_2.price))  # type: ignore
        self.assertEqual(item["price"], str(menu_item_2.price * data_2["quantity"]))  # type: ignore

        # Database-level check
        self.assertTrue(Cart.objects.filter(user=self.user1, menuitem=menu_item_1).exists())
        self.assertTrue(Cart.objects.filter(user=self.user1, menuitem=menu_item_2).exists()) 
        
    def test_authenticated_user_can_add_same_item_twice(self):
        # Arrange: Get menu item
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {
            "menuitem": menu_item.id,  # type: ignore
            "quantity": 1
        }

        # Act: Add the same item twice
        response = self.client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        response = self.client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore

        # Act: Retrieve cart
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        cart_items = response.json()  # type: ignore
        self.assertEqual(len(cart_items), 1)  # type: ignore, should still be one item in cart

        # Assert: Quantity has been incremented
        item = cart_items[0]
        self.assertEqual(item["menuitem"], menu_item.id)  # type: ignore
        self.assertEqual(item["quantity"], 2)  # type: ignore
        self.assertEqual(item["unit_price"], str(menu_item.price))  # type: ignore
        self.assertEqual(item["price"], str(menu_item.price * 2))  # type: ignore

        # Database-level check
        self.assertEqual(
            Cart.objects.filter(user=self.user1, menuitem=menu_item).count(), 1
        )
        self.assertEqual(
            Cart.objects.get(user=self.user1, menuitem=menu_item).quantity, 2
        )  
        
    def test_authenticated_user_can_add_multiple_quantities_and_different_items(self):
        # Arrange: Get menu items
        menu_item_1 = get_object_or_404(MenuItem, title="Margherita")
        menu_item_2 = get_object_or_404(MenuItem, title="Apple Pie")

        data_1 = {
            "menuitem": menu_item_1.id,  # type: ignore
            "quantity": 2
        }

        data_2 = {
            "menuitem": menu_item_2.id,  # type: ignore
            "quantity": 1
        }

        # Act: Add items to cart
        response = self.client.post(CART, data_1, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore

        response = self.client.post(CART, data_2, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore

        # Act: Retrieve cart
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        cart_items = response.json()  # type: ignore
        self.assertEqual(len(cart_items), 2)  # type: ignore

        # Assert: First item is correct
        item_1 = next(item for item in cart_items if item["menuitem"] == menu_item_1.id)    # type: ignore
        self.assertEqual(item_1["quantity"], 2)  # type: ignore
        self.assertEqual(item_1["unit_price"], str(menu_item_1.price))  # type: ignore
        self.assertEqual(item_1["price"], str(menu_item_1.price * 2))  # type: ignore

        # Assert: Second item is correct
        item_2 = next(item for item in cart_items if item["menuitem"] == menu_item_2.id)    # type: ignore
        self.assertEqual(item_2["quantity"], 1)  # type: ignore
        self.assertEqual(item_2["unit_price"], str(menu_item_2.price))  # type: ignore
        self.assertEqual(item_2["price"], str(menu_item_2.price * 1))  # type: ignore

        # Database-level checks
        self.assertEqual(
            Cart.objects.get(user=self.user1, menuitem=menu_item_1).quantity, 2
        )
        self.assertEqual(
            Cart.objects.get(user=self.user1, menuitem=menu_item_2).quantity, 1
        )
        
    def test_anon_user_cannot_view_or_add_to_cart(self):
        # Arrange: Ensure the cart has at least one item for the authenticated user
        self.client.force_authenticate(user=self.user1)  # Temporarily authenticate
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {"menuitem": menu_item.id, "quantity": 1}    # type: ignore
        self.client.post(CART, data, format="json")

        # Use a fresh anonymous client
        anon_client = APIClient()

        # Act & Assert: Anonymous user cannot view the cart
        response = anon_client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore

        # Act & Assert: Anonymous user cannot add an item to the cart
        response = anon_client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore

        # Database-level check: Cart remains unchanged
        self.assertEqual(
            Cart.objects.filter(user=self.user1, menuitem=menu_item).count(), 1
        )
        self.assertEqual(
            Cart.objects.get(user=self.user1, menuitem=menu_item).quantity, 1
        )

    # === Delete Cart Tests ===
   
    def test_authenticated_user_deletes_single_cart_item(self):
        # Arrange: Get menu item
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {
            "menuitem": menu_item.id,  # type: ignore
            "quantity": 1
        }

        # Act: Add item to cart
        response = self.client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore

        # Act: Delete single item in cart
        url = f"{CART}{menu_item.id}/"  # type: ignore
        response = self.client.delete(url)

        # Assert: Cart is now empty
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)  # type: ignore

        # Database-level check
        self.assertEqual(
            Cart.objects.filter(user=self.user1, menuitem=menu_item).count(), 0
        )
   
    # === Clear Cart Tests ===
       
    def test_authenticated_user_clears_cart_single_item(self):
        # Arrange: Get menu item
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {
            "menuitem": menu_item.id,  # type: ignore
            "quantity": 1
        }

        # Act: Add item to cart
        response = self.client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore

        # Act: Clear cart
        url = f"{CART}clear/"
        response = self.client.delete(url)

        # Assert: Cart is now empty
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)  # type: ignore

        # Database-level check
        self.assertEqual(
            Cart.objects.filter(user=self.user1, menuitem=menu_item).count(), 0
        )