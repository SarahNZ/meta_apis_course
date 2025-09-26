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
        # AAA: Arrange-Act-Assert
        # Arrange: Clear the cart
        Cart.objects.filter(user=self.user1).delete()

        # Act: View cart
        response = self.client.get(CART)

        # Assert: Cart is empty
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(response.json(), [])  # type: ignore

        # Database-level check
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())  # type: ignore

    def test_authenticated_user_can_add_and_retrieve_single_cart_item(self):
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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        response = self.client.post(CART, data_2, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore

        # Act: Retrieve cart
        response = self.client.get(CART)

        # Assert: Cart has exactly two correct items
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        cart_items = response.json()  # type: ignore
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
        data = {"menuitem": menu_item.id,"quantity": 1}

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
        
    # === List and Create Cart - Input Validation Tests ===
    
    def test_add_cart_item_empty_data(self):
        # Arrange: Empty data
        data = {}

        # Act: Try to add item with empty data
        response = self.client.post(CART, data, format="json")

        # Assert: Should return 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore

        # Database-level check: No cart item should be created
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())
    
    def test_add_cart_item_missing_menuitem(self):
        # Arrange: Missing menuitem field
        data = {
            "quantity": 1
        }

        # Act: Try to add item without menuitem
        response = self.client.post(CART, data, format="json")

        # Assert: Should return 400 Bad Request because the data validation failed
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore

        # Database-level check: No cart item should be created
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())
        
        
    def test_add_cart_item_missing_quantity(self):
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {"menuitem": menu_item.id}

        # Act: Try to add item without quantity
        response = self.client.post(CART, data, format="json")

        # Assert: Should succeed with default quantity of 1
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore
        
        # Database-level check: No cart item should be created
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())

    def test_add_cart_item_with_extra_fields_are_ignored(self):
        # Arrange: Use valid data but include extra fields that aren't in the model/serializer
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {
            "menuitem": menu_item.id,  # type: ignore
            "quantity": 2,
            "extra_field": "should be ignored",
            "another_field": 123,
            "nested_object": {"key": "value"}
        }

        # Act: Try to add item with extra fields
        response = self.client.post(CART, data, format="json")

        # Assert: Should succeed - extra fields are ignored by DRF serializer
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Assert: Response should only contain expected fields (no extra fields returned)
        response_data = response.json()  # type: ignore
        expected_fields = {"id", "menuitem", "menuitem_title", "quantity", "unit_price", "price"}
        actual_fields = set(response_data.keys())
        self.assertEqual(actual_fields, expected_fields)  # type: ignore
        
        # Assert: Only the valid data was saved
        self.assertEqual(response_data["menuitem"], menu_item.id)  # type: ignore
        self.assertEqual(response_data["quantity"], 2)  # type: ignore
        self.assertEqual(response_data["unit_price"], str(menu_item.price))  # type: ignore

        # Database-level check: Cart item should be created with correct data
        cart_item = Cart.objects.get(user=self.user1, menuitem=menu_item)
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart_item.unit_price, menu_item.price)
        
    def test_add_cart_item_cannot_set_price_or_unit_price(self):
        # Arrange: Attempt to set the price and unit price, which are fields in the Cart model through the HTTP 
        # request body
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {
            "menuitem": menu_item.id,  # type: ignore
            "quantity": 2,
            "price": 1.00,
            "unit_price": 2.00
        }

        # Act: Try to add item with price and unit price set by the client
        response = self.client.post(CART, data, format="json")

        # Assert: Should succeed - Price and unit_price fields are ignored, as they are configured as read-only 
        # by the serializer
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Assert: Response should only contain expected fields (no extra fields returned)
        response_data = response.json()  # type: ignore
        expected_fields = {"id", "menuitem", "menuitem_title", "quantity", "unit_price", "price"}
        actual_fields = set(response_data.keys())
        self.assertEqual(actual_fields, expected_fields)  # type: ignore
        
        # Assert: Only the valid data was saved
        self.assertEqual(response_data["menuitem"], menu_item.id)  # type: ignore
        self.assertEqual(response_data["quantity"], 2)  # type: ignore
        self.assertEqual(response_data["unit_price"], str(menu_item.price))  # type: ignore

        # Database-level check: Cart item should be created with correct data
        cart_item = Cart.objects.get(user=self.user1, menuitem=menu_item)
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart_item.unit_price, menu_item.price)

    def test_add_cart_item_no_matching_menuitem_id(self):
        # Arrange: Use a non-existent menuitem ID I.e. 9999. Same result for 0 or negative numbers
        invalid_menuitem_id = 9999
        data = {
            "menuitem": invalid_menuitem_id,
            "quantity": 1
        }

        # Act: Try to add invalid menu item to cart
        response = self.client.post(CART, data, format="json")

        # Assert: Should return 400 Bad Request because the data validation failed
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore
        
        # Assert: Response should contain validation error details
        self.assertIn("menuitem", response.json())  # type: ignore

        # Database-level check: No cart item should be created
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())

    def test_add_cart_item_decimal_menuitem_id(self):
        # Arrange: Use a decimal menuitem ID (should this be allowed?)
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        decimal_id = float(menu_item.id) + 0.7  # e.g., if ID is 2, this becomes 2.7
        data = {
            "menuitem": decimal_id,  # type: ignore
            "quantity": 1
        }

        # Act: Try to add item with decimal menuitem ID
        response = self.client.post(CART, data, format="json")

        # Assert: Currently succeeds because DRF truncates the decimal to int
        # This may not be ideal behavior - should probably return 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Assert: The decimal was truncated to the integer part
        response_data = response.json()  # type: ignore
        self.assertEqual(response_data["menuitem"], menu_item.id)  # type: ignore, truncated to original ID
        
        # Database-level check: Cart item was created with truncated ID
        cart_item = Cart.objects.get(user=self.user1, menuitem=menu_item)
        self.assertEqual(cart_item.menuitem.id, menu_item.id)
        
    def test_add_cart_item_decimal_quantity_fails_validation(self):
        # Arrange: Use a decimal quantity
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {
            "menuitem": menu_item.id,  # type: ignore
            "quantity": 2.7  # Decimal quantities should fail validation
        }

        # Act: Try to add item with decimal quantity
        response = self.client.post(CART, data, format="json")

        # Assert: Fails because quantity field expects integer, not float
        # This is GOOD behavior - quantities should be whole numbers
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore
        
        # Assert: Response contains validation error
        response_data = response.json()  # type: ignore
        self.assertIn("quantity", response_data)  # type: ignore
        self.assertIn("valid integer", str(response_data["quantity"]))  # type: ignore
        
        # Database-level check: No cart item should be created
        self.assertFalse(Cart.objects.filter(user=self.user1, menuitem=menu_item).exists())
        
        
    def test_add_cart_item_quantity_zero(self):
        # Arrange: Use valid menuitem but quantity of 0
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {
            "menuitem": menu_item.id,
            "quantity": 0
        }

        # Act: Try to add item with zero quantity
        response = self.client.post(CART, data, format="json")

        # Assert: Should return 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore
        
        # Database-level check: No cart item should be created
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())

    def test_add_cart_item_negative_quantity(self):
        # Arrange: Use valid menuitem but negative quantity
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {
            "menuitem": menu_item.id,
            "quantity": -1
        }

        # Act: Try to add item with negative quantity
        response = self.client.post(CART, data, format="json")

        # Assert: Should return 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore
        
        # Database-level check: No cart item should be created
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())
        
    def test_add_cart_item_invalid_menuitem_format(self):
        # Arrange: Use invalid menuitem format
        data = {
            "menuitem": "invalid",
            "quantity": 1
        }

        # Act: Try to add item with invalid menuitem format
        response = self.client.post(CART, data, format="json")

        # Assert: Should return 400 Bad Request (as input data validation failed)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore

        # Database-level check: No cart item should be created
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())

    def test_add_cart_item_invalid_quantity_format(self):
        # Arrange: Use valid menuitem but invalid quantity format
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {
            "menuitem": menu_item.id,
            "quantity": "invalid"
        }

        # Act: Try to add item with invalid quantity format
        response = self.client.post(CART, data, format="json")

        # Assert: Should return 400 Bad Request (as input data validation failed)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore

        # Database-level check: No cart item should be created
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())
        
    # === Update Cart Tests ===

    """
    Note: PUT and PATCH HTTP actions are not allowed.
    A user can increase the quantity of a menu item in their cart using POST.
    But they can't decrease the quantity of a menu item using a negative integer, as quantity must be at least 1
    """
    def test_patch_action_not_allowed(self):
        # Arrange: Get menu item
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data_1 = {"menuitem": menu_item.id, "quantity": 1}
        data_2 = {"menuitem": menu_item.id, "quantity": 2}
        
        # Act: Add item to cart
        response = self.client.post(CART, data_1, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Act: Attempt to partially update cart using HTTP PATCH action
        response = self.client.patch(CART, data_2, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Assert: Cart has not changed (Database-level check)
        cart_item = Cart.objects.get(user=self.user1, menuitem=menu_item)
        self.assertEqual(cart_item.quantity, 1)
        self.assertEqual(cart_item.unit_price, menu_item.price)
        self.assertEqual(cart_item.price, menu_item.price)
        
    def test_put_action_not_allowed(self):
        # Arrange: Get menu items
        menu_item_1 = get_object_or_404(MenuItem, title="Margherita")
        menu_item_2 = get_object_or_404(MenuItem, title="Apple Pie")
        data_1 = {"menuitem": menu_item_1.id, "quantity": 1}
        data_2 = {"menuitem": menu_item_2.id, "quantity": 2}
        
        # Act: Add first item to cart
        response = self.client.post(CART, data_1, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Act: Attempt to fully update cart using HTTP PUT action
        response = self.client.put(CART, data_2, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Assert: Cart has not changed (Database-level check)
        cart_item = Cart.objects.get(user=self.user1, menuitem=menu_item_1)
        self.assertEqual(cart_item.quantity, 1)
        self.assertEqual(cart_item.unit_price, menu_item_1.price)
        self.assertEqual(cart_item.price, menu_item_1.price)
 
        
#     # === Delete Cart Tests ===
   
    def test_authenticated_user_deletes_single_cart_item_leaving_cart_empty(self):
        # Arrange: Get menu items
        menu_item = get_object_or_404(MenuItem, title = "Margherita")
        data = {"menuitem": menu_item.id, "quantity": 1}
        
        # Act: Add one item to cart
        response = self.client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Act: Delete one item in cart
        response = self.client.delete(f"{CART}{menu_item.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Database level check that the cart is now empty
        self.assertFalse(Cart.objects.filter(user = self.user1).exists())

    
    def test_authenticated_user_deletes_multiple_quantities_of_same_item(self):
        # Arrange: Get menu items
        menu_item = get_object_or_404(MenuItem, title = "Margherita")
        data = {"menuitem": menu_item.id, "quantity": 2}
        
        # Act: Add quantity 2 of the menu item to the cart
        response = self.client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Act: Delete the menu item from the cart (entire quantity)
        response = self.client.delete(f"{CART}{menu_item.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Database level check that the cart is now empty
        self.assertFalse(Cart.objects.filter(user = self.user1).exists())
    
    def test_authenticated_user_deletes_one_item_of_two_different_items_in_cart(self):
        # Arrange: Get menu items
        menu_item_1 = get_object_or_404(MenuItem, title = "Margherita")
        menu_item_2 = get_object_or_404(MenuItem, title = "Apple Pie")
        data_1 = {"menuitem": menu_item_1.id, "quantity": 1}
        data_2 = {"menuitem": menu_item_2.id, "quantity": 1}
        
        # Act: Add two items to cart
        response = self.client.post(CART, data_1, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(CART, data_2, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Act: Delete one item in cart
        response = self.client.delete(f"{CART}{menu_item_1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Act: Get cart
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert: Only one item now in the cart
        cart_items = response.json()  # type: ignore
        self.assertEqual(len(cart_items), 1)  # type: ignore

        item = cart_items[0]
        self.assertEqual(item["menuitem"], menu_item_2.id)  # type: ignore
        self.assertEqual(item["menuitem_title"], menu_item_2.title)  # type: ignore
        self.assertEqual(item["quantity"], data_2["quantity"])  # type: ignore
        self.assertEqual(item["unit_price"], str(menu_item_2.price))  # type: ignore
        self.assertEqual(item["price"], str(menu_item_2.price * data_2["quantity"]))  # type: ignore

        # Database-level check
        self.assertEqual(
            Cart.objects.filter(user=self.user1, menuitem=menu_item_2).count(), 1
        )
          
        
    def test_authenticated_user_cannot_delete_item_from_empty_cart(self):
        # Arrange: Get menu item id, but leave cart empty
        menu_item = get_object_or_404(MenuItem, title = "Margherita")
        data = {"menuitem": menu_item.id, "quantity": 1}

        # Act: Attempt to delete item that is not in cart
        response = self.client.delete(f"{CART}{menu_item.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        
    def test_auth_user_cannot_delete_item_that_does_not_exist(self):
        # Arrange: Get menu items
        menu_item = get_object_or_404(MenuItem, title = "Margherita")
        data = {"menuitem": menu_item.id, "quantity": 2}
        
        # Act: Add two of the menu items to the cart
        response = self.client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Act: Try to delete an item with invalid id from the cart. 
        # Note: This test uses id = 0, but negative numbers and high numbers that don't match menu items produce the same response
        response = self.client.delete(f"{CART}0/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Database level check that the cart is now empty
        self.assertEqual(Cart.objects.filter(user = self.user1).count(), 1)
    
    
    def test_auth_user_cannot_delete_item_with_decimal_id(self):
        # Arrange: Get menu items
        menu_item = get_object_or_404(MenuItem, title = "Margherita")
        menu_item_dec_id = menu_item.id + 0.2
        data_1 = {"menuitem": menu_item.id, "quantity": 2}
        data_2 = {"menuitem": menu_item_dec_id, "quantity": 2}
        
        # Act: Add two of the menu items to the cart
        response = self.client.post(CART, data_1, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Act: Try to delete an item with invalid id from the cart. I.e. A decimal number
        response = self.client.delete(f"{CART}{data_2}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Database level check that the cart is now empty
        self.assertEqual(Cart.objects.filter(user = self.user1).count(), 1)
    
    def test_auth_user_cannot_delete_item_with_string_id(self):
        # Arrange: Get menu items and add to cart
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {"menuitem": menu_item.id, "quantity": 2}
        
        # Act: Add item to cart
        response = self.client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Act: Try to delete an item with string id from the cart
        response = self.client.delete(f"{CART}invalid_string/")
        
        # Assert: Should return 400 Bad Request for invalid ID format
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Assert: Response should contain error message about invalid ID format
        response_data = response.json()
        self.assertIn("detail", response_data)
        self.assertIn("Invalid cart item ID format", response_data["detail"])
        
        # Database level check that the cart item still exists (wasn't affected)
        self.assertEqual(Cart.objects.filter(user=self.user1).count(), 1)
    
    
    def test_anon_user_cannot_delete_authorized_users_item_in_cart(self):
        # Arrange: Authenticated user adds item to cart
        self.client.force_authenticate(user=self.user1)  # Temporarily authenticate
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {"menuitem": menu_item.id, "quantity": 1}    # type: ignore
        response = self.client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore

        # Verify user1's cart has 1 item
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(len(response.json()), 1)  # type: ignore
        
        # Use a fresh anonymous client
        anon_client = APIClient()

        # Act & Assert: Anonymous user cannot delete item from authenticated user's cart
        response = anon_client.delete(f"{CART}{menu_item.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore

        # Database-level check: Cart item remains unchanged
        self.assertEqual(Cart.objects.filter(user=self.user1, menuitem=menu_item).count(), 1)
        cart_item = Cart.objects.get(user=self.user1, menuitem=menu_item)
        self.assertEqual(cart_item.quantity, 1)
    
    def test_auth_user_1_cannot_delete_auth_user_2_cart(self):
        # Arrange: User1 adds item to their cart
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {"menuitem": menu_item.id, "quantity": 1}    # type: ignore
        response = self.client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Verify user1's cart has 1 item
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(len(response.json()), 1)  # type: ignore
        
        # Arrange: Create user2 and authenticate as user2
        self.user2 = User.objects.create_user(username="user2", password="password123")
        user2_client = APIClient()
        user2_token = self.get_auth_token(username="user2", password="password123")
        user2_client.credentials(HTTP_AUTHORIZATION=f'Token {user2_token}')

        # Act: User2 tries to delete item from user1's cart
        response = user2_client.delete(f"{CART}{menu_item.id}/")
        
        # Assert: Should return 404 NOT FOUND (cart item doesn't exist in user2's cart)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # type: ignore

        # Database-level check: User1's cart item remains unchanged
        self.assertEqual(Cart.objects.filter(user=self.user1, menuitem=menu_item).count(), 1)
        cart_item = Cart.objects.get(user=self.user1, menuitem=menu_item)
        self.assertEqual(cart_item.quantity, 1)
        
        # Database-level check: User2 has no cart items
        self.assertEqual(Cart.objects.filter(user=self.user2).count(), 0)


# === Clear Cart Tests ===
    
    def test_authenticated_user_clears_cart_single_item(self):
        # Arrange: Add single item to cart
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {"menuitem": menu_item.id, "quantity": 1}    # type: ignore
        response = self.client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Verify cart has 1 item
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(len(response.json()), 1)  # type: ignore
        
        # Act: Clear the cart
        response = self.client.delete(f"{CART}clear/")
        
        # Assert: Should return 204 No Content
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)  # type: ignore
        
        # Assert: Cart should now be empty
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(response.json(), [])  # type: ignore
        
        # Database-level check: Cart should be empty
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())
    
    def test_authenticated_user_clears_cart_of_multiple_quantities_of_same_item(self):
        # Arrange: Add multiple quantities of same item to cart
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {"menuitem": menu_item.id, "quantity": 3}    # type: ignore
        response = self.client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Verify cart has 1 item with quantity 3
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        cart_items = response.json()  # type: ignore
        self.assertEqual(len(cart_items), 1)  # type: ignore
        self.assertEqual(cart_items[0]["quantity"], 3)  # type: ignore
        
        # Act: Clear the cart
        response = self.client.delete(f"{CART}clear/")
        
        # Assert: Should return 204 No Content
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)  # type: ignore
        
        # Assert: Cart should now be empty
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(response.json(), [])  # type: ignore
        
        # Database-level check: Cart should be empty
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())
    
    def test_authenticated_user_clears_cart_of_two_different_cart_items(self):
        # Arrange: Add two different items to cart
        menu_item_1 = get_object_or_404(MenuItem, title="Margherita")
        menu_item_2 = get_object_or_404(MenuItem, title="Apple Pie")
        
        data_1 = {"menuitem": menu_item_1.id, "quantity": 1}    # type: ignore
        data_2 = {"menuitem": menu_item_2.id, "quantity": 1}    # type: ignore
        
        response = self.client.post(CART, data_1, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        response = self.client.post(CART, data_2, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Verify cart has 2 items
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(len(response.json()), 2)  # type: ignore
        
        # Act: Clear the cart
        response = self.client.delete(f"{CART}clear/")
        
        # Assert: Should return 204 No Content
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)  # type: ignore
        
        # Assert: Cart should now be empty
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(response.json(), [])  # type: ignore
        
        # Database-level check: Cart should be empty
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())
    
    def test_authenticated_user_clears_cart_of_multiple_quantities_of_multiple_items(self):
        # Arrange: Add multiple items with varying quantities to cart
        menu_item_1 = get_object_or_404(MenuItem, title="Margherita")
        menu_item_2 = get_object_or_404(MenuItem, title="Apple Pie")
        menu_item_3 = get_object_or_404(MenuItem, title="Pepperoni")
        
        data_1 = {"menuitem": menu_item_1.id, "quantity": 2}    # type: ignore
        data_2 = {"menuitem": menu_item_2.id, "quantity": 1}    # type: ignore
        data_3 = {"menuitem": menu_item_3.id, "quantity": 3}    # type: ignore
        
        response = self.client.post(CART, data_1, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        response = self.client.post(CART, data_2, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        response = self.client.post(CART, data_3, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Verify cart has 3 items with correct quantities
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        cart_items = response.json()  # type: ignore
        self.assertEqual(len(cart_items), 3)  # type: ignore
        
        # Verify total quantities in database
        total_cart_items = Cart.objects.filter(user=self.user1).count()
        self.assertEqual(total_cart_items, 3)
        
        # Act: Clear the cart
        response = self.client.delete(f"{CART}clear/")
        
        # Assert: Should return 204 No Content
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)  # type: ignore
        
        # Assert: Cart should now be empty
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(response.json(), [])  # type: ignore
        
        # Database-level check: Cart should be empty
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())

    # === Clear Cart - Isolation Tests ===
    
    def test_anon_user_cannot_clear_auth_users_cart(self):
        # Arrange: Authenticated user adds item to cart
        self.client.force_authenticate(user=self.user1)  # Temporarily authenticate
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {"menuitem": menu_item.id, "quantity": 2}    # type: ignore
        response = self.client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore

        # Verify user1's cart has 1 item
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(len(response.json()), 1)  # type: ignore
        
        # Use a fresh anonymous client
        anon_client = APIClient()

        # Act & Assert: Anonymous user cannot clear authenticated user's cart
        response = anon_client.delete(f"{CART}clear/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore

        # Database-level check: Cart items remain unchanged
        self.assertEqual(Cart.objects.filter(user=self.user1, menuitem=menu_item).count(), 1)
        cart_item = Cart.objects.get(user=self.user1, menuitem=menu_item)
        self.assertEqual(cart_item.quantity, 2)
    
    def test_auth_user_1_cannot_clear_auth_user_2_cart(self):
        # Arrange: User1 adds items to their cart
        menu_item_1 = get_object_or_404(MenuItem, title="Margherita")
        menu_item_2 = get_object_or_404(MenuItem, title="Apple Pie")
        data_1 = {"menuitem": menu_item_1.id, "quantity": 1}    # type: ignore
        data_2 = {"menuitem": menu_item_2.id, "quantity": 2}    # type: ignore
        
        response = self.client.post(CART, data_1, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        response = self.client.post(CART, data_2, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Verify user1's cart has 2 items
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(len(response.json()), 2)  # type: ignore
        
        # Arrange: Create user2 and authenticate as user2
        self.user2 = User.objects.create_user(username="user2", password="password123")
        user2_client = APIClient()
        user2_token = self.get_auth_token(username="user2", password="password123")
        user2_client.credentials(HTTP_AUTHORIZATION=f'Token {user2_token}')

        # Act: User2 tries to clear user1's cart (but this actually clears user2's own empty cart)
        response = user2_client.delete(f"{CART}clear/")
        
        # Assert: Should return 204 No Content (user2 successfully cleared their own empty cart)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)  # type: ignore

        # Database-level check: User1's cart items remain unchanged
        self.assertEqual(Cart.objects.filter(user=self.user1).count(), 2)
        self.assertTrue(Cart.objects.filter(user=self.user1, menuitem=menu_item_1).exists())
        self.assertTrue(Cart.objects.filter(user=self.user1, menuitem=menu_item_2).exists())
        
        # Database-level check: User2 still has no cart items (cleared empty cart)
        self.assertEqual(Cart.objects.filter(user=self.user2).count(), 0)

    # === Clear Cart - Input Validation Tests ===
    
    def test_auth_user_can_clear_empty_cart(self):
        # Arrange: Ensure cart is empty
        Cart.objects.filter(user=self.user1).delete()
        
        # Verify cart is empty
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(response.json(), [])  # type: ignore
        
        # Act: Clear empty cart
        response = self.client.delete(f"{CART}clear/")
        
        # Assert: Should return 204 No Content (clearing empty cart is allowed)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)  # type: ignore
        
        # Assert: Cart should still be empty
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(response.json(), [])  # type: ignore
        
        # Database-level check: Cart should still be empty
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())
    
    def test_clear_cart_ignores_request_body(self):
        # Arrange: Add item to cart
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        data = {"menuitem": menu_item.id, "quantity": 1}    # type: ignore
        response = self.client.post(CART, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Verify cart has 1 item
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(len(response.json()), 1)  # type: ignore
        
        # Act: Clear cart with request body (should be ignored)
        invalid_body = {
            "menuitem": "invalid_data",
            "quantity": "this_should_be_ignored",
            "extra_field": "also_ignored"
        }
        response = self.client.delete(f"{CART}clear/", data=invalid_body, format="json")
        
        # Assert: Should return 204 No Content (body is ignored)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)  # type: ignore
        
        # Assert: Cart should be cleared regardless of invalid body
        response = self.client.get(CART)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(response.json(), [])  # type: ignore
        
        # Database-level check: Cart should be empty
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())