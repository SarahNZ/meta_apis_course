from django.contrib.auth.models import User
from rest_framework import status

from base_test import BaseAPITestCase
from endpoints import ORDERS
from LittleLemonAPI.models import Category, MenuItem, Order


class ManagerOrderFilteringTests(BaseAPITestCase):
    """Test cases for manager order status filtering functionality"""
    
    def setUp(self):
        super().setUp()
        
        # Create test users
        self.manager = User.objects.create_user(
            username='manager1',
            password='testpass123'
        )
        self.customer1 = User.objects.create_user(
            username='customer1',
            password='testpass123'
        )
        self.customer2 = User.objects.create_user(
            username='customer2',
            password='testpass123'
        )
        
        # Add manager to Manager group and give staff status
        self.add_user_to_manager_group(self.manager)
        
        # Create categories and menu items
        self.category_pizza = Category.objects.create(slug="pizza", title="Pizza")
        self.menu_item = MenuItem.objects.create(
            title="Margherita",
            price=10.00,
            featured=True,
            category=self.category_pizza
        )
        
        # Create orders with different statuses
        # Customer1 orders
        self.order1_customer1 = Order.objects.create(
            user=self.customer1,
            total=10.00,
            status=0  # pending
        )
        self.order2_customer1 = Order.objects.create(
            user=self.customer1,
            total=20.00,
            status=1  # delivered
        )
        
        # Customer2 orders
        self.order1_customer2 = Order.objects.create(
            user=self.customer2,
            total=15.00,
            status=0  # pending
        )
        self.order2_customer2 = Order.objects.create(
            user=self.customer2,
            total=25.00,
            status=1  # delivered
        )
        
        # Authenticate as manager
        token = self.get_auth_token('manager1', 'testpass123')
        self.authenticate_client(token)
    
    def test_manager_can_view_all_orders_without_filter(self):
        """Test that manager can view all orders when no status filter is applied"""
        # Act
        response = self.client.get(ORDERS)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # All 4 orders
        
        # Verify all orders are present
        order_ids = [order['id'] for order in response.data]
        self.assertIn(self.order1_customer1.id, order_ids)
        self.assertIn(self.order2_customer1.id, order_ids)
        self.assertIn(self.order1_customer2.id, order_ids)
        self.assertIn(self.order2_customer2.id, order_ids)
    
    def test_manager_can_filter_orders_by_pending_status(self):
        """Test that manager can filter orders by pending status"""
        # Act
        response = self.client.get(f"{ORDERS}?status=pending")
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only pending orders
        
        # Verify only pending orders are returned
        for order in response.data:
            self.assertEqual(order['status'], 0)
        
        # Verify correct orders are returned
        order_ids = [order['id'] for order in response.data]
        self.assertIn(self.order1_customer1.id, order_ids)
        self.assertIn(self.order1_customer2.id, order_ids)
        self.assertNotIn(self.order2_customer1.id, order_ids)
        self.assertNotIn(self.order2_customer2.id, order_ids)
    
    def test_manager_can_filter_orders_by_delivered_status(self):
        """Test that manager can filter orders by delivered status"""
        # Act
        response = self.client.get(f"{ORDERS}?status=delivered")
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only delivered orders
        
        # Verify only delivered orders are returned
        for order in response.data:
            self.assertEqual(order['status'], 1)
        
        # Verify correct orders are returned
        order_ids = [order['id'] for order in response.data]
        self.assertIn(self.order2_customer1.id, order_ids)
        self.assertIn(self.order2_customer2.id, order_ids)
        self.assertNotIn(self.order1_customer1.id, order_ids)
        self.assertNotIn(self.order1_customer2.id, order_ids)
    
    def test_manager_filter_with_invalid_status_returns_all_orders(self):
        """Test that manager gets all orders when using invalid status filter"""
        # Act
        response = self.client.get(f"{ORDERS}?status=invalid")
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # All orders returned
    
    def test_customer_cannot_use_status_filter(self):
        """Test that regular customers cannot use status filtering"""
        # Arrange: Authenticate as customer
        token = self.get_auth_token('customer1', 'testpass123')
        self.authenticate_client(token)
        
        # Act
        response = self.client.get(f"{ORDERS}?status=pending")
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Customer should only see their own orders regardless of filter
        self.assertEqual(len(response.data), 2)  # Only customer1's orders
        
        # Verify only customer1's orders are returned
        for order in response.data:
            self.assertEqual(order['user'], self.customer1.id)
    
    def test_delivery_crew_cannot_use_status_filter(self):
        """Test that delivery crew members cannot use status filtering"""
        # Arrange: Create delivery crew user
        delivery_crew = User.objects.create_user(
            username='delivery1',
            password='testpass123'
        )
        self.add_user_to_delivery_crew_group(delivery_crew)
        
        # Assign an order to delivery crew
        self.order1_customer1.delivery_crew = delivery_crew
        self.order1_customer1.save()
        
        # Authenticate as delivery crew
        token = self.get_auth_token('delivery1', 'testpass123')
        self.authenticate_client(token)
        
        # Act
        response = self.client.get(f"{ORDERS}?status=pending")
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Delivery crew should only see assigned orders regardless of filter
        self.assertEqual(len(response.data), 1)  # Only assigned order
        
        # Verify only assigned order is returned
        self.assertEqual(response.data[0]['id'], self.order1_customer1.id)
    
    def test_manager_status_filter_case_sensitivity(self):
        """Test that status filter is case sensitive"""
        # Act: Try with uppercase status
        response = self.client.get(f"{ORDERS}?status=PENDING")
        
        # Assert: Should return all orders (case sensitive)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # All orders returned
    
    def test_manager_status_filter_with_multiple_parameters(self):
        """Test that status filter works with other query parameters"""
        # Act: Use status filter with other parameters
        response = self.client.get(f"{ORDERS}?status=pending&ordering=total")
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only pending orders
        
        # Verify orders are sorted by total
        totals = [order['total'] for order in response.data]
        self.assertEqual(totals, sorted(totals))
    
    def test_manager_filter_empty_result(self):
        """Test manager filtering when no orders match the criteria"""
        # Arrange: Delete all pending orders
        Order.objects.filter(status=0).delete()
        
        # Act
        response = self.client.get(f"{ORDERS}?status=pending")
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No pending orders
