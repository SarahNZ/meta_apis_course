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
   
#     def test_authenticated_user_deletes_single_cart_item(self):
#         # Arrange: Get menu item
#         menu_item = get_object_or_404(MenuItem, title="Margherita")
#         data = {
#             "menuitem": menu_item.id,  # type: ignore
#             "quantity": 1
#         }

#         # Act: Add item to cart
#         response = self.client.post(CART, data, format="json")
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore

#         # Act: Delete single item in cart
#         url = f"{CART}{menu_item.id}/"  # type: ignore
#         response = self.client.delete(url)

#         # Assert: Cart is now empty
#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)  # type: ignore

#         # Database-level check
#         self.assertEqual(
#             Cart.objects.filter(user=self.user1, menuitem=menu_item).count(), 0
#         )

    # test_authenticated_user_cannot_delete_item_not_in_cart - TODO
    # test_authenticated_user_deletes_single_cart_item 
    # test_anon_user_cannot_delete_another_users_item_in_cart - TODO
    # test_auth_user_1_cannot_delete_auth_user_2_cart - TODO
    # test_authenticated_user_deletes_one_item_of_two_in_cart - TODO
    # test_authenticated_user_deletes_multiple_quantities_of_same_item - TODO
   
#     # === Clear Cart Tests ===
       
#     def test_authenticated_user_clears_cart_single_item(self):
#         # Arrange: Get menu item
#         menu_item = get_object_or_404(MenuItem, title="Margherita")
#         data = {
#             "menuitem": menu_item.id,  # type: ignore
#             "quantity": 1
#         }

#         # Act: Add item to cart
#         response = self.client.post(CART, data, format="json")
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore

#         # Act: Clear cart
#         url = f"{CART}clear/"
#         response = self.client.delete(url)

#         # Assert: Cart is now empty
#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)  # type: ignore

#         # Database-level check
#         self.assertEqual(
#             Cart.objects.filter(user=self.user1, menuitem=menu_item).count(), 0
#         )

    # test_authenticated_user_clears_cart_single_item 
    # test_anon_user_cannot_clear_auth_users_cart - TODO
    # test_auth_user_1_cannot_clear_auth_user_2_cart - TODO
    # test_authenticated_user_clears_cart_of_two_different_cart_items - TODO
    # test_authenticated_user_clears_cart_of_multiple_quantities_of_same_item - TODO
    # test_authenticated_user_clears_cart_of_multiple_quantities_of_multiple_items - TODO