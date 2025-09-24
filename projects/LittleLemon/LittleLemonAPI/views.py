from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import filters, status, viewsets
from .filters import MenuItemFilter
from .models import Cart, Category, MenuItem
from .pagination import CustomPageNumberPagination
from .permissions import IsStaffOrReadOnly
from .serializers import CartSerializer, CategorySerializer, MenuItemSerializer, UserSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for authorized, staff users to view all users: GET /api/users/

    Note: User creation and token-based login handled by Djoser via /auth/ endpoint. I.e.
    - Create user: POST /auth/users (username and password in body, email optional)
    - Get authorized user token: POST /auth/token/login/ (username and password in body)

    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class DeliveryCrewViewSet(viewsets.ViewSet):
    """
    ViewSet for managing users in the Delivery Crew group. 
    Requires admin privileges
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def list(self, request):
        """
        List all users in the Delivery Crew group
        GET /api/groups/delivery-crew/users/
        """
        delivery_crew = get_object_or_404(Group, name="Delivery Crew")
        delivery_users = delivery_crew.user_set.all()
        serializer = UserSerializer(delivery_users, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """
        Add authorized user to delivery crew group
        POST /api/groups/delivery-crew/users/ (username in body)
        """
        username = request.data.get('username', '').strip()
        if not username:  # This catches both None and empty/whitespace strings
            return Response(
                {"username": "This field is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        delivery_crew = get_object_or_404(Group, name="Delivery Crew")
        user = get_object_or_404(User, username=username)
        delivery_crew.user_set.add(user)
        return Response({"message": f"User '{username}' was successfully added to Delivery Crew group"}, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, pk=None):
        """
        Remove a user from the delivery crew group
        DELETE /api/groups/delivery-crew/users/{id}/
        Use the pk (id) parameter from the URL to identify the user
        """
        if not pk:
            return Response(
                {"detail": "User ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Handle non-integer IDs gracefully
        try:
            user_id = int(pk)
        except ValueError:
            return Response(
                {"detail": f"Invalid user ID format: {pk}"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        delivery_crew = get_object_or_404(Group, name="Delivery Crew")
        user = get_object_or_404(User, id=user_id)
        
        # Check if user is actually in the delivery crew group
        if not user.groups.filter(name="Delivery Crew").exists():
            return Response(
                {"detail": "User is not in the Delivery Crew group"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        delivery_crew.user_set.remove(user)
        return Response({"message": f"User with id '{user_id}' was successfully removed from the Delivery Crew group"}, status=status.HTTP_204_NO_CONTENT)


class ManagerViewSet(viewsets.ViewSet):
    """
    ViewSet for managing users in the Manager group. 
    Requires admin privileges
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def list(self, request):
        """
        List all users in the Manager group.
        GET /api/groups/manager/users/
        """
        managers_group = get_object_or_404(Group, name = "Manager")
        manager_users = managers_group.user_set.all()
        serializer = UserSerializer(manager_users, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """
        Add a user to the Manager group
        POST /api/groups/manager/users/ (include username in body)
        """
        username = request.data.get('username', '').strip()
        if not username:  # This catches both None and empty/whitespace strings
            return Response(
                {"username": "This field is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        managers_group = get_object_or_404(Group, name="Manager")
        user = get_object_or_404(User, username=username)
        managers_group.user_set.add(user)
        user.is_staff = True
        user.save()
        return Response({"message": f"User '{username}' was successfully added to the Manager group"}, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, pk=None):
        """
        Remove a user from the Manager group
        DELETE /api/groups/manager/users/{id}
        Use the pk (id) parameter from the URL to identify the user
        """
        if not pk:
            return Response(
                {"detail": "User ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Handle non-integer IDs gracefully
        try:
            user_id = int(pk)
        except ValueError:
            return Response(
                {"detail": f"Invalid user ID format: {pk}"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        managers_group = get_object_or_404(Group, name="Manager")
        user = get_object_or_404(User, id=user_id)
        
        # Check if user is actually in the manager group
        if not user.groups.filter(name="Manager").exists():
            return Response(
                {"detail": "User is not in the Manager group"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        managers_group.user_set.remove(user)
        user.is_staff = False
        user.save()
        return Response({"message": f"User with id '{user_id}' was successfully removed from the Delivery Crew group"}, status=status.HTTP_204_NO_CONTENT)

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
        
# Endpoint /api/cart/
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
        serializer = CartSerializer(queryset, many = True)
        return Response(serializer.data)
    
    def create(self, request):
        """
        Add menu item to the authenticated user's cart
        """
        # Use serializer for validation
        serializer = CartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract validated data
        menu_item = serializer.validated_data['menuitem']
        quantity = serializer.validated_data['quantity']
        
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
            # Update quantity instead of creating duplicate
            cart_item.quantity += quantity  
            # Recalculate the total price for the row
            cart_item.price = cart_item.unit_price * cart_item.quantity
            # Save the updated values to the db
            cart_item.save()
            
        # Use serializer for response
        response_serializer = CartSerializer(cart_item)
        return Response(response_serializer.data, status = status.HTTP_201_CREATED)
    
    def destroy(self, request, pk = None):
        """
        Remove a specific menu item from the cart
        """
        cart_item = get_object_or_404(Cart, user = request.user, pk = pk)
        cart_item.delete()
        return Response(status = status.HTTP_204_NO_CONTENT)
    
    @action(detail = False, methods = ['delete'])
    def clear(self, request):
        """
        Clear all items from the user's cart
        
        """
        Cart.objects.filter(user = request.user).delete()
        return Response(status = status.HTTP_204_NO_CONTENT)