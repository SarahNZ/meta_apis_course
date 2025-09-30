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
    
    def test_view_empty_list_of_orders(self):
        # Arrange: Check there are no orders for this authorized user in the db
        order_db = Order.objects.filter(user = self.user1)
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
        cart_data = {"menuitem": menu_item.id, "quantity": 2}  # type: ignore

        # Act: Add item to cart
        cart_response = self.client.post(CART, cart_data, format="json")
        self.assertEqual(cart_response.status_code, status.HTTP_201_CREATED)  # type: ignore

        # Act: Place the order
        order_response = self.client.post(ORDERS, format="json")
        
        # Assert: Order creation was successful
        self.assertEqual(order_response.status_code, status.HTTP_201_CREATED)  # type: ignore
        self.assertIsNotNone(order_response.data)  # type: ignore
        self.assertIn("id", order_response.data)  # type: ignore
        
        # Assert: Cart is cleared after order placement
        cart_check_response = self.client.get(CART)
        self.assertEqual(len(cart_check_response.data), 0)  # type: ignore
        
        # Database-level check: Order and OrderItem were created
        self.assertTrue(Order.objects.filter(user=self.user1).exists())
        order = Order.objects.get(user=self.user1)
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)
        
        # Database-level check: Cart was cleared
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())

    def test_place_order_with_detailed_validation(self):
        """Comprehensive test that validates all order response fields and correctness"""
        # Arrange: Add multiple items to cart
        margherita = get_object_or_404(MenuItem, title="Margherita")
        apple_pie = get_object_or_404(MenuItem, title="Apple Pie")
        
        # Add first item
        cart_data1 = {"menuitem": margherita.id, "quantity": 2}  # type: ignore
        response1 = self.client.post(CART, cart_data1, format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Add second item
        cart_data2 = {"menuitem": apple_pie.id, "quantity": 1}  # type: ignore
        response2 = self.client.post(CART, cart_data2, format="json")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)  # type: ignore

        # Calculate expected total (2 × $10 + 1 × $11 = $31)
        expected_total = (margherita.price * 2) + (apple_pie.price * 1)

        # Act: Place the order
        order_response = self.client.post(ORDERS, format="json")
        
        # Assert: Order creation successful
        self.assertEqual(order_response.status_code, status.HTTP_201_CREATED)  # type: ignore
        order_data = order_response.data

        # Validate main order fields
        self.assertIn("id", order_data)  # type: ignore
        self.assertEqual(order_data["user"], self.user1.id)  # type: ignore
        self.assertEqual(order_data["user_name"], self.user1.username)  # type: ignore
        self.assertEqual(order_data["status"], 0)  # Default status  # type: ignore
        self.assertEqual(float(order_data["total"]), float(expected_total))  # type: ignore
        self.assertIsNotNone(order_data["date"])  # type: ignore
        self.assertIsNone(order_data["delivery_crew"])  # type: ignore
        # delivery_crew_name is not included when delivery_crew is null
        self.assertNotIn("delivery_crew_name", order_data)  # type: ignore

        # Validate order items
        order_items = order_data["order_items"]  # type: ignore
        self.assertEqual(len(order_items), 2)  # type: ignore

        # Find and validate Margherita order item
        margherita_item = next((item for item in order_items if item["menuitem"] == margherita.id), None)  # type: ignore
        self.assertIsNotNone(margherita_item)  # type: ignore
        self.assertEqual(margherita_item["menuitem_title"], "Margherita")  # type: ignore
        self.assertEqual(margherita_item["menuitem_category"], "Pizza")  # type: ignore
        self.assertEqual(margherita_item["quantity"], 2)  # type: ignore
        self.assertEqual(float(margherita_item["unit_price"]), float(margherita.price))  # type: ignore
        self.assertEqual(float(margherita_item["price"]), float(margherita.price * 2))  # type: ignore

        # Find and validate Apple Pie order item
        apple_pie_item = next((item for item in order_items if item["menuitem"] == apple_pie.id), None)  # type: ignore
        self.assertIsNotNone(apple_pie_item)  # type: ignore
        self.assertEqual(apple_pie_item["menuitem_title"], "Apple Pie")  # type: ignore
        self.assertEqual(apple_pie_item["menuitem_category"], "Dessert")  # type: ignore
        self.assertEqual(apple_pie_item["quantity"], 1)  # type: ignore
        self.assertEqual(float(apple_pie_item["unit_price"]), float(apple_pie.price))  # type: ignore
        self.assertEqual(float(apple_pie_item["price"]), float(apple_pie.price * 1))  # type: ignore

        # Verify the order appears in user's order list
        orders_list_response = self.client.get(ORDERS)
        self.assertEqual(orders_list_response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(len(orders_list_response.data), 1)  # type: ignore
        self.assertEqual(orders_list_response.data[0]["id"], order_data["id"])  # type: ignore
        
        # Database-level checks: Verify order and order items were created correctly
        order = Order.objects.get(user=self.user1)
        self.assertEqual(order.total, expected_total)
        self.assertEqual(order.status, 0)
        self.assertIsNone(order.delivery_crew)
        
        # Database-level check: Verify OrderItem records
        order_items_db = OrderItem.objects.filter(order=order)
        self.assertEqual(order_items_db.count(), 2)
        
        margherita_order_item = OrderItem.objects.get(order=order, menuitem=margherita)
        self.assertEqual(margherita_order_item.quantity, 2)
        self.assertEqual(margherita_order_item.unit_price, margherita.price)
        self.assertEqual(margherita_order_item.price, margherita.price * 2)
        
        apple_pie_order_item = OrderItem.objects.get(order=order, menuitem=apple_pie)
        self.assertEqual(apple_pie_order_item.quantity, 1)
        self.assertEqual(apple_pie_order_item.unit_price, apple_pie.price)
        self.assertEqual(apple_pie_order_item.price, apple_pie.price * 1)
        
        # Database-level check: Cart was cleared
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())

    def test_place_order_with_empty_cart_fails(self):
        """Test that placing an order with empty cart returns appropriate error"""
        # Arrange: Ensure cart is empty
        Cart.objects.filter(user=self.user1).delete()
        
        # Act: Try to place order with empty cart
        response = self.client.post(ORDERS, format="json")
        
        # Assert: Should fail with 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore
        self.assertIn("detail", response.data)  # type: ignore
        self.assertIn("empty cart", response.data["detail"])  # type: ignore
        
        # Database-level check: No order should be created
        self.assertFalse(Order.objects.filter(user=self.user1).exists())
        self.assertFalse(OrderItem.objects.filter(order__user=self.user1).exists())

    # === Authentication & Authorization Tests ===
    
    def test_unauthenticated_user_cannot_place_order(self):
        """Test that unauthenticated users cannot place orders"""
        # Arrange: Add item to cart as authenticated user first, then clear authentication
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        cart_data = {"menuitem": menu_item.id, "quantity": 1}  # type: ignore
        
        # Add item while authenticated
        response = self.client.post(CART, cart_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Clear authentication
        self.client.credentials()
        
        # Act: Try to place order as unauthenticated user
        response = self.client.post(ORDERS, format="json")
        
        # Assert: Should return 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore
        
        # Database-level check: No order should be created
        self.assertFalse(Order.objects.filter(user=self.user1).exists())
    
    def test_unauthenticated_user_cannot_view_orders(self):
        """Test that unauthenticated users cannot view order list"""
        # Arrange: Clear authentication
        self.client.credentials()
        
        # Act: Try to view orders as unauthenticated user
        response = self.client.get(ORDERS)
        
        # Assert: Should return 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore

    # === User Isolation Tests ===
    
    def test_user_cannot_view_another_users_orders(self):
        """Test that users can only see their own orders"""
        # Arrange: User1 creates an order
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        cart_data = {"menuitem": menu_item.id, "quantity": 1}  # type: ignore
        
        # User1 adds item and places order
        self.client.post(CART, cart_data, format="json")
        order_response = self.client.post(ORDERS, format="json")
        self.assertEqual(order_response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Arrange: Create user2 and authenticate
        self.user2 = User.objects.create_user(username="testuser2", password="pass1234")
        user2_client = APIClient()
        user2_token = self.get_auth_token(username="testuser2", password="pass1234")
        user2_client.credentials(HTTP_AUTHORIZATION=f'Token {user2_token}')
        
        # Act: User2 tries to view orders
        response = user2_client.get(ORDERS)
        
        # Assert: User2 should see empty order list (cannot see user1's orders)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(response.data, [])  # type: ignore
        
        # Database-level check: User1's order exists, but user2 has no orders
        self.assertEqual(Order.objects.filter(user=self.user1).count(), 1)
        self.assertEqual(Order.objects.filter(user=self.user2).count(), 0)

    # === Order Workflow Integration Tests ===
    
    def test_multiple_orders_from_same_user(self):
        """Test that a user can place multiple orders sequentially"""
        # Arrange & Act: Place first order
        menu_item1 = get_object_or_404(MenuItem, title="Margherita")
        cart_data1 = {"menuitem": menu_item1.id, "quantity": 1}  # type: ignore
        
        self.client.post(CART, cart_data1, format="json")
        order1_response = self.client.post(ORDERS, format="json")
        self.assertEqual(order1_response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Arrange & Act: Place second order
        menu_item2 = get_object_or_404(MenuItem, title="Apple Pie")
        cart_data2 = {"menuitem": menu_item2.id, "quantity": 2}  # type: ignore
        
        self.client.post(CART, cart_data2, format="json")
        order2_response = self.client.post(ORDERS, format="json")
        self.assertEqual(order2_response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Assert: Both orders should be in user's order list
        orders_response = self.client.get(ORDERS)
        self.assertEqual(orders_response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(len(orders_response.data), 2)  # type: ignore
        
        # Database-level check: Two separate orders exist
        user_orders = Order.objects.filter(user=self.user1).order_by('id')
        self.assertEqual(user_orders.count(), 2)
        
        # Verify order totals are different
        self.assertNotEqual(user_orders[0].total, user_orders[1].total)
        
        # Database-level check: Cart should be empty after each order
        self.assertFalse(Cart.objects.filter(user=self.user1).exists())
    
    def test_place_order_with_single_item_multiple_quantities(self):
        """Test placing order with high quantity of single item"""
        # Arrange: Add item with multiple quantities
        menu_item = get_object_or_404(MenuItem, title="Margherita")
        large_quantity = 10
        cart_data = {"menuitem": menu_item.id, "quantity": large_quantity}  # type: ignore
        
        # Act: Add to cart and place order
        cart_response = self.client.post(CART, cart_data, format="json")
        self.assertEqual(cart_response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        order_response = self.client.post(ORDERS, format="json")
        self.assertEqual(order_response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Assert: Order total should reflect quantity
        order_data = order_response.data
        expected_total = menu_item.price * large_quantity
        self.assertEqual(float(order_data["total"]), float(expected_total))  # type: ignore
        
        # Assert: Order item should have correct quantity
        order_item = order_data["order_items"][0]  # type: ignore
        self.assertEqual(order_item["quantity"], large_quantity)  # type: ignore
        self.assertEqual(float(order_item["price"]), float(expected_total))  # type: ignore
        
        # Database-level check: Verify database record accuracy
        order = Order.objects.get(user=self.user1)
        order_item_db = OrderItem.objects.get(order=order)
        self.assertEqual(order_item_db.quantity, large_quantity)
        self.assertEqual(order_item_db.price, expected_total)