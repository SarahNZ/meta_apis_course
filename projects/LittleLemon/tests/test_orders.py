from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status  
from rest_framework.test import APIClient  

from base_test import BaseAPITestCase
from endpoints import CART, ORDERS  
from LittleLemonAPI.models import Cart, Category, MenuItem, Order, OrderItem  

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

    # === Helper Methods ===
    
    def _add_item_to_cart(self, menu_item, quantity):
        """Helper method to add items to cart"""
        cart_data = {"menuitem": menu_item.id, "quantity": quantity}
        response = self.client.post(CART, cart_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response
    
    def _place_order(self):
        """Helper method to place an order"""
        response = self.client.post(ORDERS, format="json")
        return response
    
    def _verify_order_created(self, order_response, expected_total=None):
        """Helper method to verify order was created correctly"""
        self.assertEqual(order_response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(order_response.data)
        self.assertIn("id", order_response.data)
        
        if expected_total is not None:
            self.assertEqual(float(order_response.data["total"]), float(expected_total))
        
        return order_response.data
    
    def _verify_cart_cleared(self):
        """Helper method to verify cart is empty after order placement"""
        cart_response = self.client.get(CART)
        self.assertEqual(len(cart_response.data), 0)
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())
    
    def _verify_database_order_created(self, expected_total=None):
        """Helper method to verify order exists in database"""
        self.assertTrue(Order.objects.filter(user=self.user1).exists())
        order = Order.objects.get(user=self.user1)
        
        if expected_total is not None:
            self.assertEqual(order.total, expected_total)
        
        return order
    
    def _verify_order_items_created(self, order, expected_items):
        """Helper method to verify order items were created correctly"""
        order_items = OrderItem.objects.filter(order=order)
        self.assertEqual(order_items.count(), len(expected_items))
        
        for expected_item in expected_items:
            order_item = OrderItem.objects.get(order=order, menuitem=expected_item['menuitem'])
            self.assertEqual(order_item.quantity, expected_item['quantity'])
            self.assertEqual(order_item.unit_price, expected_item['menuitem'].price)
            self.assertEqual(order_item.price, expected_item['menuitem'].price * expected_item['quantity'])
    
    def _add_multiple_items_to_cart(self, items):
        """Helper method to add multiple items to cart"""
        for item in items:
            self._add_item_to_cart(item['menuitem'], item['quantity'])
    
    def _validate_order_response_fields(self, order_data, expected_user, expected_status=0):
        """Helper method to validate order response fields"""
        self.assertEqual(order_data["user"], expected_user.id)
        self.assertEqual(order_data["user_name"], expected_user.username)
        self.assertEqual(order_data["status"], expected_status)
        self.assertIsNotNone(order_data["date"])
        self.assertIsNone(order_data["delivery_crew"])
        self.assertNotIn("delivery_crew_name", order_data)
    
    def _validate_order_item(self, order_item, menuitem, expected_quantity):
        """Helper method to validate individual order item"""
        self.assertEqual(order_item["menuitem"], menuitem.id)
        self.assertEqual(order_item["menuitem_title"], menuitem.title)
        self.assertEqual(order_item["menuitem_category"], menuitem.category.title)
        self.assertEqual(order_item["quantity"], expected_quantity)
        self.assertEqual(float(order_item["unit_price"]), float(menuitem.price))
        self.assertEqual(float(order_item["price"]), float(menuitem.price * expected_quantity))
    
    def _clear_authentication(self):
        """Helper method to clear client authentication"""
        self.client.credentials()
    
    def _create_and_authenticate_user2(self):
        """Helper method to create and authenticate a second user"""
        self.user2 = User.objects.create_user(username="testuser2", password="pass1234")
        user2_client = APIClient()
        user2_token = self.get_auth_token(username="testuser2", password="pass1234")
        user2_client.credentials(HTTP_AUTHORIZATION=f'Token {user2_token}')
        return user2_client
    
    # === Basic Order Tests ===
    
    def test_view_empty_list_of_orders(self):
        # Arrange: Check there are no orders for this authorized user in the db
        order_db = Order.objects.filter(user=self.user1)
        self.assertEqual(len(order_db), 0)

        # Act: View empty list of orders
        response = self.client.get(ORDERS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert: 
        self.assertEqual(response.data, [])
    
    def test_place_an_order_success(self):
        """Basic test for placing an order - reusable for other test scenarios"""
        # Arrange: Get menu item and add to cart
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        expected_total = menu_item.price * 2

        # Act: Add item to cart and place order
        self._add_item_to_cart(menu_item, 2)
        order_response = self._place_order()
        
        # Assert: Order creation was successful
        order_data = self._verify_order_created(order_response, expected_total)
        
        # Assert: Cart is cleared after order placement
        self._verify_cart_cleared()
        
        # Database-level check: Order and OrderItem were created
        order = self._verify_database_order_created(expected_total)
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)

    def test_place_order_with_detailed_validation(self):
        """Comprehensive test that validates all order response fields and correctness"""
        # Arrange: Add multiple items to cart
        margherita = get_object_or_404(MenuItem, title="Margherita")
        apple_pie = get_object_or_404(MenuItem, title="Apple Pie")
        
        # Add items to cart
        self._add_item_to_cart(margherita, 2)
        self._add_item_to_cart(apple_pie, 1)

        # Calculate expected total (2 × $10 + 1 × $11 = $31)
        expected_total = (margherita.price * 2) + (apple_pie.price * 1)

        # Act: Place the order
        order_response = self._place_order()
        
        # Assert: Order creation successful
        order_data = self._verify_order_created(order_response, expected_total)

        # Validate main order fields
        self._validate_order_response_fields(order_data, self.user1)

        # Validate order items
        order_items = order_data["order_items"]
        self.assertEqual(len(order_items), 2)

        # Find and validate Margherita order item
        margherita_item = next((item for item in order_items if item["menuitem"] == margherita.id), None)
        self.assertIsNotNone(margherita_item)
        self._validate_order_item(margherita_item, margherita, 2)

        # Find and validate Apple Pie order item
        apple_pie_item = next((item for item in order_items if item["menuitem"] == apple_pie.id), None)
        self.assertIsNotNone(apple_pie_item)
        self._validate_order_item(apple_pie_item, apple_pie, 1)

        # Verify the order appears in user's order list
        orders_list_response = self.client.get(ORDERS)
        self.assertEqual(orders_list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(orders_list_response.data), 1)
        self.assertEqual(orders_list_response.data[0]["id"], order_data["id"])
        
        # Database-level checks: Verify order and order items were created correctly
        order = self._verify_database_order_created(expected_total)
        self.assertEqual(order.status, 0)
        self.assertIsNone(order.delivery_crew)
        
        # Database-level check: Verify OrderItem records
        expected_items = [
            {'menuitem': margherita, 'quantity': 2},
            {'menuitem': apple_pie, 'quantity': 1}
        ]
        self._verify_order_items_created(order, expected_items)
        
        # Database-level check: Cart was cleared
        self._verify_cart_cleared()

    def test_place_order_with_empty_cart_fails(self):
        """Test that placing an order with empty cart returns appropriate error"""
        # Arrange: Ensure cart is empty
        Cart.objects.filter(user=self.user1).delete()
        
        # Act: Try to place order with empty cart
        response = self._place_order()
        
        # Assert: Should fail with 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertIn("empty cart", response.data["detail"])
        
        # Database-level check: No order should be created
        self.assertFalse(Order.objects.filter(user=self.user1).exists())
        self.assertFalse(OrderItem.objects.filter(order__user=self.user1).exists())

    # === Authentication & Authorization Tests ===
    
    def test_unauthenticated_user_cannot_place_order(self):
        """Test that unauthenticated users cannot place orders"""
        # Arrange: Add item to cart as authenticated user first, then clear authentication
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        self._add_item_to_cart(menu_item, 1)
        
        # Clear authentication
        self._clear_authentication()
        
        # Act: Try to place order as unauthenticated user
        response = self._place_order()
        
        # Assert: Should return 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Database-level check: No order should be created
        self.assertFalse(Order.objects.filter(user=self.user1).exists())
    
    def test_unauthenticated_user_cannot_view_orders(self):
        """Test that unauthenticated users cannot view order list"""
        # Arrange: Clear authentication
        self._clear_authentication()
        
        # Act: Try to view orders as unauthenticated user
        response = self.client.get(ORDERS)
        
        # Assert: Should return 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # === User Isolation Tests ===
    
    def test_user_cannot_view_another_users_orders(self):
        """Test that users can only see their own orders"""
        # Arrange: User1 creates an order
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        self._add_item_to_cart(menu_item, 1)
        order_response = self._place_order()
        self.assertEqual(order_response.status_code, status.HTTP_201_CREATED)
        
        # Arrange: Create user2 and authenticate
        user2_client = self._create_and_authenticate_user2()
        
        # Act: User2 tries to view orders
        response = user2_client.get(ORDERS)
        
        # Assert: User2 should see empty order list (cannot see user1's orders)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        
        # Database-level check: User1's order exists, but user2 has no orders
        self.assertEqual(Order.objects.filter(user=self.user1).count(), 1)
        self.assertEqual(Order.objects.filter(user=self.user2).count(), 0)

    # === Order Workflow Integration Tests ===
    
    def test_multiple_orders_from_same_user(self):
        """Test that a user can place multiple orders sequentially"""
        # Arrange & Act: Place first order
        menu_item1 = get_object_or_404(MenuItem, title="Margherita")
        self._add_item_to_cart(menu_item1, 1)
        order1_response = self._place_order()
        self.assertEqual(order1_response.status_code, status.HTTP_201_CREATED)
        
        # Arrange & Act: Place second order
        menu_item2 = get_object_or_404(MenuItem, title="Apple Pie")
        self._add_item_to_cart(menu_item2, 2)
        order2_response = self._place_order()
        self.assertEqual(order2_response.status_code, status.HTTP_201_CREATED)
        
        # Assert: Both orders should be in user's order list
        orders_response = self.client.get(ORDERS)
        self.assertEqual(orders_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(orders_response.data), 2)
        
        # Database-level check: Two separate orders exist
        user_orders = Order.objects.filter(user=self.user1).order_by('id')
        self.assertEqual(user_orders.count(), 2)
        
        # Verify order totals are different
        self.assertNotEqual(user_orders[0].total, user_orders[1].total)
        
        # Database-level check: Cart should be empty after each order
        self._verify_cart_cleared()
    
    def test_place_order_with_single_item_multiple_quantities(self):
        """Test placing order with high quantity of single item"""
        # Arrange: Add item with multiple quantities
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        large_quantity = 10
        expected_total = menu_item.price * large_quantity
        
        # Act: Add to cart and place order
        self._add_item_to_cart(menu_item, large_quantity)
        order_response = self._place_order()
        self.assertEqual(order_response.status_code, status.HTTP_201_CREATED)
        
        # Assert: Order total should reflect quantity
        order_data = self._verify_order_created(order_response, expected_total)
        
        # Assert: Order item should have correct quantity
        order_item = order_data["order_items"][0]
        self.assertEqual(order_item["quantity"], large_quantity)
        self.assertEqual(float(order_item["price"]), float(expected_total))
        
        # Database-level check: Verify database record accuracy
        order = self._verify_database_order_created(expected_total)
        order_item_db = OrderItem.objects.get(order=order)
        self.assertEqual(order_item_db.quantity, large_quantity)
        self.assertEqual(order_item_db.price, expected_total)