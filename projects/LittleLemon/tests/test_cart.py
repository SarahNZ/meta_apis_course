from django.contrib.auth.models import User
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
        
    # === Cart Isolation Tests ===  
      
    def test_authenticated_user_cannot_view_another_users_cart(self):
        # Arrange: Setup menu items
        menu_item_1 = get_object_or_404(MenuItem, title="Margherita")
        
        # Arrange: User1 adds items to their cart
        data_1 = {"menuitem": menu_item_1.id, "quantity": 1}    # type: ignore
        self.client.post(CART, data_1, format="json")
        
        # Verify user1's cart has 1 item
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(len(response.json()), 1)  # type: ignore
        
        # Arrange: Create user2 and authenticate as user2
        self.user2 = User.objects.create_user(username="user2", password="password123")
        user2_client = APIClient()
        user2_token = self.get_auth_token(username="user2", password="password123")
        user2_client.credentials(HTTP_AUTHORIZATION=f'Token {user2_token}')
        
        # Act & Assert: User2 cannot view user1's cart (should see empty cart)
        response = user2_client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(response.json(), [])  # type: ignore, user2's cart should be empty

    def test_user_cannot_have_duplicate_cart_entries_for_same_menu_item(self):
        # Arrange: Get menu item
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        
        # Act: Add the same item multiple times with different quantities
        data_1 = {"menuitem": menu_item.id, "quantity": 2}    # type: ignore
        response = self.client.post(CART, data_1, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        data_2 = {"menuitem": menu_item.id, "quantity": 3}    # type: ignore
        response = self.client.post(CART, data_2, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Act: Retrieve cart
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        cart_items = response.json()  # type: ignore
        
        # Assert: Only ONE cart entry exists for this menu item
        self.assertEqual(len(cart_items), 1)  # type: ignore, should be only one cart entry
        
        # Assert: Quantity should be cumulative (2 + 3 = 5)
        item = cart_items[0]
        self.assertEqual(item["menuitem"], menu_item.id)  # type: ignore
        self.assertEqual(item["quantity"], 5)  # type: ignore, 2 + 3 = 5
        self.assertEqual(item["unit_price"], str(menu_item.price))  # type: ignore
        self.assertEqual(item["price"], str(menu_item.price * 5))  # type: ignore
        
        # Database-level check: Verify only one Cart entry exists
        self.assertEqual(
            Cart.objects.filter(user=self.user1, menuitem=menu_item).count(), 1
        )
        self.assertEqual(
            Cart.objects.get(user=self.user1, menuitem=menu_item).quantity, 5
        )
        
    # === View and Create Cart - Input Validation Tests ===
    
    def test_add_cart_item_invalid_menuitem_id(self):
        # Arrange: Use a non-existent menuitem ID
        invalid_menuitem_id = 9999
        data = {
            "menuitem": invalid_menuitem_id,
            "quantity": 1
        }

        # Act: Try to add invalid menu item to cart
        response = self.client.post(CART, data, format="json")

        # Assert: Should return 404 Not Found because the menu item doesn't exist
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # type: ignore

        # Database-level check: No cart item should be created
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())

    def test_add_cart_item_quantity_zero(self):
        # Arrange: Use valid menuitem but quantity of 0
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {
            "menuitem": menu_item.id,
            "quantity": 0
        }

        # Act: Try to add item with zero quantity
        response = self.client.post(CART, data, format="json")

        # Assert: Should return 400 Bad Request or handle according to business logic
        # Note: Based on your views.py, this might succeed with quantity 0, 
        # but let's test what actually happens
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Verify the cart item was created with quantity 0
        cart_item = Cart.objects.get(user=self.user1, menuitem=menu_item)
        self.assertEqual(cart_item.quantity, 0)

    def test_add_cart_item_negative_quantity(self):
        # Arrange: Use valid menuitem but negative quantity
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {
            "menuitem": menu_item.id,
            "quantity": -1
        }

        # Act: Try to add item with negative quantity
        response = self.client.post(CART, data, format="json")

        # Assert: Based on your current implementation, this might succeed
        # but ideally should be validated
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Verify the cart item was created with negative quantity
        cart_item = Cart.objects.get(user=self.user1, menuitem=menu_item)
        self.assertEqual(cart_item.quantity, -1)

    def test_add_cart_item_missing_menuitem(self):
        # Arrange: Missing menuitem field
        data = {
            "quantity": 1
        }

        # Act: Try to add item without menuitem
        response = self.client.post(CART, data, format="json")

        # Assert: Currently returns 404 because get_object_or_404(MenuItem, id=None) fails
        # This could be improved to return 400 with proper validation
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # type: ignore

        # Database-level check: No cart item should be created
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())

    def test_add_cart_item_missing_quantity(self):
        # Arrange: Missing quantity field (should default to 1 based on views.py)
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {
            "menuitem": menu_item.id
        }

        # Act: Try to add item without quantity
        response = self.client.post(CART, data, format="json")

        # Assert: Should succeed with default quantity of 1
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Verify the cart item was created with default quantity
        cart_item = Cart.objects.get(user=self.user1, menuitem=menu_item)
        self.assertEqual(cart_item.quantity, 1)

    def test_add_cart_item_invalid_quantity_format(self):
        # Arrange: Use valid menuitem but invalid quantity format
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {
            "menuitem": menu_item.id,
            "quantity": "invalid"
        }

        # Act & Assert: Currently causes a server error due to int() conversion
        # This test documents the current behavior - ideally should return 400
        with self.assertRaises(ValueError):  # type: ignore
            response = self.client.post(CART, data, format="json")

        # Database-level check: No cart item should be created due to the error
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())

    def test_add_cart_item_invalid_menuitem_format(self):
        # Arrange: Use invalid menuitem format
        data = {
            "menuitem": "invalid",
            "quantity": 1
        }

        # Act: Try to add item with invalid menuitem format
        response = self.client.post(CART, data, format="json")

        # Assert: Should return 404 Not Found (get_object_or_404 will handle the invalid ID)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # type: ignore

        # Database-level check: No cart item should be created
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())

    def test_add_cart_item_null_menuitem(self):
        # Arrange: Use null menuitem
        data = {
            "menuitem": None,
            "quantity": 1
        }

        # Act: Try to add item with null menuitem
        response = self.client.post(CART, data, format="json")

        # Assert: Should return 404 Not Found (get_object_or_404 handles None as non-existent)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # type: ignore

        # Database-level check: No cart item should be created
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())

    def test_add_cart_item_null_quantity(self):
        # Arrange: Use valid menuitem but null quantity
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {
            "menuitem": menu_item.id,
            "quantity": None
        }

        # Act: Try to add item with null quantity
        response = self.client.post(CART, data, format="json")

        # Assert: Should use default quantity of 1 (based on views.py logic)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Verify the cart item was created with default quantity
        cart_item = Cart.objects.get(user=self.user1, menuitem=menu_item)
        self.assertEqual(cart_item.quantity, 1)

    def test_add_cart_item_empty_data(self):
        # Arrange: Empty data
        data = {}

        # Act: Try to add item with empty data
        response = self.client.post(CART, data, format="json")

        # Assert: Should return 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore

        # Database-level check: No cart item should be created
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())
        
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
        
    # === Cart Isolation Tests ===  
      
    # def test_authenticated_user_cannot_access_another_users_cart(self):
    #     # Arrange: Setup menu items
    #     menu_item_1 = get_object_or_404(MenuItem, title="Margherita")
    #     menu_item_2 = get_object_or_404(MenuItem, title="Pepperoni")
        
    #     # Arrange: User1 adds items to their cart
    #     self.client.force_authenticate(user=self.user1)
    #     data_1 = {"menuitem": menu_item_1.id, "quantity": 2}    # type: ignore
    #     data_2 = {"menuitem": menu_item_2.id, "quantity": 1}    # type: ignore
    #     self.client.post(CART, data_1, format="json")
    #     self.client.post(CART, data_2, format="json")
        
    #     # Verify user1's cart has 2 items
    #     response = self.client.get(CART)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
    #     self.assertEqual(len(response.json()), 2)  # type: ignore
        
    #     # Arrange: Create and authenticate as user2
    #     user2_client.credentials()
    #     user2_token = self.get_auth_token(username="user2", password="password123")
    #     user2_client.credentials(HTTP_AUTHORIZATION=f'Token {user2_token}')
        
    #     # Act & Assert: User2 cannot view user1's cart (should see empty cart)
    #     response = user2_client.get(CART)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
    #     self.assertEqual(response.json(), [])  # type: ignore, user2's cart should be empty
        
    #     # Act & Assert: User2 can add their own items (cart isolation)
    #     data_3 = {"menuitem": menu_item_1.id, "quantity": 3}    # type: ignore
    #     response = user2_client.post(CART, data_3, format="json")
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
    #     # Act & Assert: User2's cart only shows their own item
    #     response = user2_client.get(CART)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
    #     user2_cart = response.json()  # type: ignore
    #     self.assertEqual(len(user2_cart), 1)  # type: ignore
    #     self.assertEqual(user2_cart[0]["quantity"], 3)  # type: ignore
        
    #     # Act & Assert: User2 cannot delete user1's cart items by ID
    #     url = f"{CART}{menu_item_1.id}/"
    #     response = user2_client.delete(url)
    #     # This should either delete user2's item or return 404 (depending on implementation)
    #     # But it should NOT delete user1's item
        
    #     # Act & Assert: User1's cart remains unchanged
    #     self.client.force_authenticate(user=self.user1)
    #     response = self.client.get(CART)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
    #     user1_cart = response.json()  # type: ignore
    #     # User1 should still have their original items (unless user2 deleted their own)
    #     user1_margherita = next((item for item in user1_cart if item["menuitem"] == menu_item_1.id), None)    # type: ignore
    #     if user1_margherita:  # If user1's Margherita item still exists
    #         self.assertEqual(user1_margherita["quantity"], 2)  # type: ignore, should be unchanged
        
    #     # Act & Assert: User2 cannot clear user1's entire cart
    #     user2_client.delete(f"{CART}clear/")
        
    #     # Verify user1's cart is still intact after user2's clear attempt
    #     self.client.force_authenticate(user=self.user1)
    #     response = self.client.get(CART)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        
    #     # Database-level checks: Verify cart isolation
    #     user1_cart_count = Cart.objects.filter(user=self.user1).count()
    #     user2_cart_count = Cart.objects.filter(user=self.user2).count()
        
    #     # User1 should have their original items (2 initially, minus any that user2 might have "deleted" of their own)
    #     self.assertGreaterEqual(user1_cart_count, 1)  # type: ignore, at least one item should remain
    #     # User2 should have at most 1 item (what they added, minus what they might have deleted)
    #     self.assertLessEqual(user2_cart_count, 1)  # type: ignore