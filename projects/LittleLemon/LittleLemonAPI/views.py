import logging
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import filters, status, viewsets
from .filters import MenuItemFilter, OrderFilter
from .models import Cart, Category, MenuItem, Order, OrderItem
from .pagination import CustomPageNumberPagination
from .permissions import IsStaffOrReadOnly, IsStaffOnly, IsStaffOrManager, is_manager, is_delivery_crew
from .serializers import CartSerializer, CategorySerializer, MenuItemSerializer, OrderItemSerializer, OrderSerializer, OrderUpdateSerializer, UserSerializer

logger = logging.getLogger('LittleLemonAPI')

class UserGroupManagementMixin:
    """
    Mixin that provides common functionality for managing users in groups.
    Subclasses must define group_name attribute.
    """
    group_name = None  # Must be set by subclass
    updates_staff_status = False  # Set to True for Manager group
    
    def get_group(self):
        """Helper method to get the group object"""
        if not self.group_name:
            raise ValueError("group_name must be set in subclass")
        return get_object_or_404(Group, name=self.group_name)
    
    def validate_user_id(self, pk):
        """Helper method to validate and convert user ID"""
        if not pk:
            logger.warning(f"Group management attempt with missing user ID for group: {self.group_name}")
            return None, Response(
                {"detail": "User ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            return int(pk), None
        except ValueError:
            logger.warning(f"Invalid user ID format '{pk}' for group: {self.group_name}")
            return None, Response(
                {"detail": f"Invalid user ID format: {pk}"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def validate_username(self, request):
        """Helper method to validate username from request data"""
        username = request.data.get('username', '').strip()
        if not username:
            logger.warning(f"Group management attempt with missing username for group: {self.group_name}")
            return None, Response(
                {"username": "This field is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        return username, None
    
    def list_group_users(self, request):
        """List all users in the group"""
        group = self.get_group()
        users = group.user_set.all()
        user_count = users.count()
        
        logger.info(f"User '{request.user.username}' viewed {user_count} users in {self.group_name} group")
        
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    def add_user_to_group(self, request):
        """Add a user to the group"""
        username, error_response = self.validate_username(request)
        if error_response:
            return error_response
        
        try:
            group = self.get_group()
            user = get_object_or_404(User, username=username)
            
            # Check if user is already in group
            if user.groups.filter(name=self.group_name).exists():
                logger.info(f"User '{request.user.username}' attempted to add '{username}' to {self.group_name} group, but user was already in group")
                return Response({"message": f"User '{username}' is already in the {self.group_name} group"}, status=status.HTTP_200_OK)
            
            group.user_set.add(user)
            
            # Update staff status if needed (for Manager group)
            if self.updates_staff_status:
                user.is_staff = True
                user.save()
                logger.info(f"User '{username}' granted staff status")
            
            logger.info(f"SUCCESS: User '{request.user.username}' added '{username}' to {self.group_name} group")
            
            return Response({"message": "ok"}, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"ERROR: Failed to add user '{username}' to {self.group_name} group by '{request.user.username}': {str(e)}")
            raise
    
    def remove_user_from_group(self, request, pk=None):
        """Remove a user from the group"""
        user_id, error_response = self.validate_user_id(pk)
        if error_response:
            return error_response
        
        try:
            group = self.get_group()
            user = get_object_or_404(User, id=user_id)
            
            # Check if user is in the group
            if not user.groups.filter(name=self.group_name).exists():
                logger.warning(f"User '{request.user.username}' attempted to remove user ID {user_id} ('{user.username}') from {self.group_name} group, but user was not in group")
                return Response(
                    {"detail": f"User is not in the {self.group_name} group"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            group.user_set.remove(user)
            
            # Update staff status if needed (for Manager group)
            if self.updates_staff_status:
                user.is_staff = False
                user.save()
                logger.info(f"User '{user.username}' staff status revoked")
            
            logger.info(f"SUCCESS: User '{request.user.username}' removed '{user.username}' (ID: {user_id}) from {self.group_name} group")
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.error(f"ERROR: Failed to remove user ID {user_id} from {self.group_name} group by '{request.user.username}': {str(e)}")
            raise


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for authorized, staff users or Manager group members to view all users: GET /api/users/

    Note: User creation and token-based login handled by Djoser via /auth/ endpoint. I.e.
    - Create user: POST /auth/users (username and password in body, email optional)
    - Get authorized user token: POST /auth/token/login/ (username and password in body)

    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsStaffOrManager]

class DeliveryCrewViewSet(UserGroupManagementMixin, viewsets.ViewSet):
    """
    ViewSet for managing users in the Delivery Crew group. 
    Requires staff privileges or Manager group membership
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]
    group_name = "Delivery Crew"
    updates_staff_status = False  # Delivery crew doesn't get staff status
    
    def list(self, request):
        """
        List all users in the Delivery Crew group
        GET /api/groups/delivery-crew/users/
        """
        return self.list_group_users(request)
    
    def create(self, request):
        """
        Add authorized user to delivery crew group
        POST /api/groups/delivery-crew/users/ (username in body)
        """
        return self.add_user_to_group(request)
    
    def destroy(self, request, pk=None):
        """
        Remove a user from the delivery crew group
        DELETE /api/groups/delivery-crew/users/{id}/
        Use the pk (id) parameter from the URL to identify the user
        """
        return self.remove_user_from_group(request, pk)


class ManagerViewSet(UserGroupManagementMixin, viewsets.ViewSet):
    """
    ViewSet for managing users in the Manager group. 
    Requires staff privileges
    """
    permission_classes = [IsAuthenticated, IsStaffOnly]
    group_name = "Manager"
    updates_staff_status = True  # Managers get staff status when added to group
    
    def list(self, request):
        """
        List all users in the Manager group.
        GET /api/groups/manager/users/
        """
        return self.list_group_users(request)
    
    def create(self, request):
        """
        Add a user to the Manager group
        POST /api/groups/manager/users/ (include username in body)
        """
        return self.add_user_to_group(request)
    
    def destroy(self, request, pk=None):
        """
        Remove a user from the Manager group
        DELETE /api/groups/manager/users/{id}
        Use the pk (id) parameter from the URL to identify the user
        """
        return self.remove_user_from_group(request, pk)

class MenuItemsViewSet(viewsets.ModelViewSet):
    """
    Viewset for managing menu items.
    All actions require authorization (only staff can add or remove menu items)
    
    View all menu items: GET /api/menu-items/
    Specify number of items listed per page: GET /api/menu-items/?page_size={int}
    Search menu items by title: GET /api/menu-items/?search={string}
    Sort (order) menu items by price, title or category title. 
        E.g. Sort by category and price GET /api/menu-items/?ordering=category__title&ordering=price
    Filter menu items by category e.g. Desserts: GET /api/menu-items/?category_title=Desserts
    Add menu item: POST /api/menu-items/ (include title, price, featured and category_id in body)
    Remove menu item: DELETE /api/menu-items/{id}/
    """
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsStaffOrReadOnly] 
    pagination_class = CustomPageNumberPagination 
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title']
    ordering_fields = ['price', 'title', 'category__title'] # allow client to specify ordering by price
    filterset_class = MenuItemFilter
    
    def perform_create(self, serializer):
        """Override to add logging when menu items are created"""
        menu_item = serializer.save()
        logger.info(f"SUCCESS: User '{self.request.user.username}' created menu item '{menu_item.title}' (ID: {menu_item.id}, Price: ${menu_item.price})")
    
    def perform_destroy(self, instance):
        """Override to add logging when menu items are deleted"""
        item_title = instance.title
        item_id = instance.id
        instance.delete()
        logger.info(f"SUCCESS: User '{self.request.user.username}' deleted menu item '{item_title}' (ID: {item_id})")


class CategoriesViewSet(viewsets.ModelViewSet):
    """
    Viewset for managing menu item categories
    All actions require authorization (only staff can add categories)
    Categories can't be deleted, as they are related to the MenuItem model
    
    View all categories: GET /api/categories/
    Search by title: GET /api/categories/?search={string}
    Sort categories by title: GET /api/categories/?ordering=title
    Add category: POST /api/categories/ (include slug and title in body)
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly] 
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title']
    ordering_fields = ['title']
    
    # Override delete/destroy(), so no-one can delete categories
    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Deleting categories is not allowed."}, 
            status = status.HTTP_403_FORBIDDEN
        )
        
        
class CartViewSet(viewsets.ViewSet):
    """
    Viewset for managing user's cart.
    
    View cart: GET /api/cart/
    Add menu item to cart: POST /api/cart/ (include menuitem and quantity in body)
    Remove menu item from cart: DELETE /api/cart/{id}/
    Clear cart (of all menu items): DELETE /api/cart/clear/
    """
    
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """
        List all menu items in the authenticated user's cart. If empty, return []
        """
        queryset = Cart.objects.filter(user = request.user)
        item_count = queryset.count()
        
        logger.info(f"User '{request.user.username}' viewed cart with {item_count} items")
        
        serializer = CartSerializer(queryset, many = True)
        return Response(serializer.data)
    
    def create(self, request):
        """
        Add menu item to the authenticated user's cart
        """
        # Use serializer for validation
        serializer = CartSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"User '{request.user.username}' attempted to add invalid item to cart: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract validated data
        menu_item = serializer.validated_data['menuitem']
        quantity = serializer.validated_data['quantity']
        
        logger.info(f"User '{request.user.username}' adding {quantity}x '{menu_item.title}' to cart")
        
        unit_price = menu_item.price 
        total_price = unit_price * quantity  
        
        # Add menu item to the cart (if menu item does not already exist in this user's cart)
        cart_item, created = Cart.objects.get_or_create(
            user = request.user, 
            menuitem = menu_item,
            defaults = {
                "quantity": quantity,
                "unit_price": unit_price,
                "price": total_price,
            },
        )
        
        # If this menu item already existed in the user's cart
        if not created:
            old_quantity = cart_item.quantity
            # Update quantity instead of creating duplicate
            cart_item.quantity += quantity  
            # Recalculate the total price for the row
            cart_item.price = cart_item.unit_price * cart_item.quantity
            # Save the updated values to the db
            cart_item.save()
            logger.info(f"Updated existing cart item: '{menu_item.title}' quantity from {old_quantity} to {cart_item.quantity}")
        else:
            logger.info(f"Created new cart item: {quantity}x '{menu_item.title}'")
            
        logger.info(f"SUCCESS: User '{request.user.username}' added {quantity}x '{menu_item.title}' to cart")
        
        # Use serializer for response
        response_serializer = CartSerializer(cart_item)
        return Response(response_serializer.data, status = status.HTTP_201_CREATED)
    
    def destroy(self, request, pk = None):
        """
        Remove a specific menu item from the cart
        """
        try:
            cart_item = get_object_or_404(Cart, user = request.user, pk = pk)
            item_name = cart_item.menuitem.title
            quantity = cart_item.quantity
            
            cart_item.delete()
            
            logger.info(f"SUCCESS: User '{request.user.username}' removed {quantity}x '{item_name}' from cart")
            
            return Response(status = status.HTTP_204_NO_CONTENT)
            
        except ValueError:
            # Handle invalid ID format (e.g., strings that can't be converted to int)
            logger.warning(f"User '{request.user.username}' attempted to delete cart item with invalid ID format: {pk}")
            return Response(
                {"detail": "Invalid cart item ID format"}, 
                status = status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"ERROR: User '{request.user.username}' failed to remove item {pk} from cart: {str(e)}")
            raise
    
    @action(detail = False, methods = ['delete'])
    def clear(self, request):
        """
        Clear all items from the user's cart
        
        """
        items_count = Cart.objects.filter(user = request.user).count()
        Cart.objects.filter(user = request.user).delete()
        
        logger.info(f"SUCCESS: User '{request.user.username}' cleared {items_count} items from cart")
        
        return Response(status = status.HTTP_204_NO_CONTENT)
    

class OrderViewSet(viewsets.ViewSet):
    """
    Viewset for managing user's orders.

    Customers can view their orders: GET /api/orders/
    Customers can view a single order: GET /api/orders/{orderId}/
    Customers can place an order: POST /api/orders/ (include info in body)
    Customers can't modify their order. I.e. Update or delete it (out of scope)
    
    Managers (Manager group members) can view a list of all orders: GET /api/orders/
    Managers can view a single order: GET /api/orders/{orderId}/
    Managers can filter orders by user_id: GET /api/orders/?user_id={user_id}
    Managers can filter orders by status: GET /api/orders/?status=pending or GET /api/orders/?status=delivered
    Managers can assign orders to delivery crew: PATCH /api/orders/{orderId}/ (delivery_crew in body)
    Managers can update order status to 1 (delivered): PATCH /api/orders/{orderId}/ (status in body) - only if order is assigned
    
    Delivery crew members can view orders assigned to them: GET /api/orders/
    Delivery crew members can view single assigned orders: GET /api/orders/{orderId}/
    Delivery crew members can update order status to 1 (delivered): PATCH /api/orders/{orderId}/ (status in body) - only for orders assigned to them
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter

    def list(self, request):
        """
        List orders for the authenticated user.
        Managers (Manager group members) can view all orders.
        Delivery crew members can view orders assigned to them.
        Regular customers only see their own orders.
        """
        # Managers can view all orders
        if is_manager(request.user):
            logger.info(f"Manager '{request.user.username}' viewing all orders")
            queryset = Order.objects.all()
        elif is_delivery_crew(request.user):
            # Delivery crew can view orders assigned to them
            logger.info(f"Delivery crew member '{request.user.username}' viewing assigned orders")
            queryset = Order.objects.filter(delivery_crew=request.user)
        else:
            # Regular customers only see their own orders
            queryset = Order.objects.filter(user=request.user)
        
        # Apply filtering if user is a manager
        if is_manager(request.user):
            filterset = self.filterset_class(request.GET, queryset=queryset, request=request)
            if filterset.is_valid():
                queryset = filterset.qs
                # Log filtering activity
                status_filter = request.GET.get('status')
                if status_filter:
                    logger.info(f"Manager '{request.user.username}' filtered orders by status: {status_filter}")
        
        serializer = OrderSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Retrieve a single order for the authenticated user.
        Managers (Manager group members) can view any order.
        Delivery crew members can view orders assigned to them.
        Regular customers only see their own orders.
        GET /api/orders/{orderId}/
        """
        try:
            # Managers can view any order
            if is_manager(request.user):
                order = get_object_or_404(Order, pk=pk)
                logger.info(f"Manager '{request.user.username}' viewed order {order.id}")
            elif is_delivery_crew(request.user):
                # Delivery crew can view orders assigned to them
                order = get_object_or_404(Order, delivery_crew=request.user, pk=pk)
                logger.info(f"Delivery crew member '{request.user.username}' viewed order {order.id}")
            else:
                # Regular customers only see their own orders
                order = get_object_or_404(Order, user=request.user, pk=pk)
                logger.info(f"User '{request.user.username}' viewed order {order.id}")
            
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        except ValueError:
            logger.warning(f"User '{request.user.username}' attempted to retrieve order with invalid ID format: {pk}")
            return Response(
                {"detail": "Invalid order ID format"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request):
        """
        Create a new order from the user's cart items
        POST /api/orders/
        """
        # Check if user has items in cart
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            logger.warning(f"User '{request.user.username}' attempted to create order with empty cart")
            return Response(
                {"detail": "Cannot create order with empty cart"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate total price from cart items
        total = sum(cart_item.price for cart_item in cart_items)
        
        logger.info(f"User '{request.user.username}' creating order with total ${total}")
        
        # Create the order - date is automatically set by auto_now_add=True
        order = Order.objects.create(
            user=request.user,
            total=total
        )
        
        # Create OrderItem records for each cart item
        order_items_created = 0
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menuitem=cart_item.menuitem,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                price=cart_item.price
            )
            order_items_created += 1
        
        # Clear the cart after successfully creating the order and order items
        cart_items.delete()
        
        logger.info(f"SUCCESS: User '{request.user.username}' created order {order.id} with {order_items_created} items and total ${total}")
        
        # Return the created order
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        """
        Update an order (PATCH operation).
        
        Managers can:
        - Assign orders to delivery crew members
        - Update order status to 1 (delivered) if order is already assigned
        
        Delivery crew members can:
        - Update order status to 1 (delivered) if the order is assigned to them
        
        PATCH /api/orders/{orderId}/
        """
        try:
            # Get the order
            order = get_object_or_404(Order, pk=pk)
            
            # Determine what fields are being updated
            has_delivery_crew = 'delivery_crew' in request.data
            has_status = 'status' in request.data
            
            # Check permissions based on what's being updated
            if has_delivery_crew:
                # Only managers can assign delivery crew
                if not is_manager(request.user):
                    logger.warning(f"User '{request.user.username}' attempted to assign order {pk} but is not a manager")
                    return Response(
                        {"detail": "Only managers can assign orders to delivery crew"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            if has_status:
                # Check if user can update status
                if is_manager(request.user):
                    # Managers can update status if order is assigned to someone
                    # If delivery_crew is being updated in the same request, check the new value
                    if has_delivery_crew:
                        # If both fields are being updated, the order will be assigned by the delivery_crew update
                        # So we allow the status update
                        pass
                    elif not order.delivery_crew:
                        logger.warning(f"Manager '{request.user.username}' attempted to update status for unassigned order {pk}")
                        return Response(
                            {"detail": "Cannot update status for unassigned order"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                elif is_delivery_crew(request.user):
                    # Delivery crew can only update status if order is assigned to them
                    if order.delivery_crew != request.user:
                        logger.warning(f"Delivery crew member '{request.user.username}' attempted to update status for order {pk} not assigned to them")
                        return Response(
                            {"detail": "You can only update status for orders assigned to you"},
                            status=status.HTTP_403_FORBIDDEN
                        )
                else:
                    # Regular users cannot update orders
                    logger.warning(f"User '{request.user.username}' attempted to update order {pk} but is not a manager or delivery crew member")
                    return Response(
                        {"detail": "Only managers and delivery crew members can update orders"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # If no delivery_crew or status fields, deny the request
            if not has_delivery_crew and not has_status:
                logger.warning(f"User '{request.user.username}' attempted to update order {pk} with invalid fields")
                return Response(
                    {"detail": "Only delivery_crew and status fields can be updated"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Use the general update serializer
            serializer = OrderUpdateSerializer(order, data=request.data, partial=True)
            
            if not serializer.is_valid():
                logger.warning(f"User '{request.user.username}' attempted invalid order update for order {pk}: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Save the update
            updated_order = serializer.save()
            
            # Log the successful update
            if has_delivery_crew:
                delivery_crew_name = updated_order.delivery_crew.username if updated_order.delivery_crew else "None"
                logger.info(f"SUCCESS: Manager '{request.user.username}' assigned order {pk} to delivery crew member '{delivery_crew_name}'")
            
            if has_status:
                logger.info(f"SUCCESS: User '{request.user.username}' updated order {pk} status to {updated_order.status}")
            
            # Return the updated order using the full OrderSerializer
            response_serializer = OrderSerializer(updated_order)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except ValueError:
            logger.warning(f"User '{request.user.username}' attempted to update order with invalid ID format: {pk}")
            return Response(
                {"detail": "Invalid order ID format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"ERROR: User '{request.user.username}' failed to update order {pk}: {str(e)}")
            raise