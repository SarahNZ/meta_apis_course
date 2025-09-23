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

# === User Management Views ===

# Note: A lot of the user management functionality is handled by Django and Djoser (token-based authentication)
    
# Endpoint /api/groups/delivery-crew/users/
class DeliveryCrewViewSet(viewsets.ViewSet):
    """
    ViewSet for managing users in the Delivery Crew group.
    Requires admin privileges.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def list(self, request):
        """List all users in the Delivery Crew group"""
        delivery_crew = get_object_or_404(Group, name="Delivery Crew")
        delivery_users = delivery_crew.user_set.all()
        serializer = UserSerializer(delivery_users, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """Add a user to the Delivery Crew group"""
        username = request.data.get('username')
        if not username:
            return Response(
                {"username": "This field is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        delivery_crew = get_object_or_404(Group, name="Delivery Crew")
        user = get_object_or_404(User, username=username)
        delivery_crew.user_set.add(user)
        return Response({"message": "ok"}, status=status.HTTP_201_CREATED)
    
    # Endpoint DELETE /api/groups/delivery-crew/users/{id}/
    def destroy(self, request, pk=None):
        # Use the pk parameter from the URL to identify the user
        # Remove a user from the Delivery Crew group
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
        return Response({"message": "ok"}, status=status.HTTP_200_OK)

# Endpoint /api/groups/manager/users/
class ManagerViewSet(viewsets.ViewSet):
    """
    ViewSet for managing users in the Manager group.
    Requires admin privileges.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def list(self, request):
        """List all users in the Manager group"""
        managers_group = get_object_or_404(Group, name = "Manager")
        manager_users = managers_group.user_set.all()
        serializer = UserSerializer(manager_users, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """Add a user to the Manager group"""
        username = request.data.get('username')
        if not username:
            return Response(
                {"username": "This field is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        managers_group = get_object_or_404(Group, name="Manager")
        user = get_object_or_404(User, username=username)
        managers_group.user_set.add(user)
        user.is_staff = True
        user.save()
        return Response({"message": "ok"}, status=status.HTTP_201_CREATED)
    
    # Endpoint DELETE /api/groups/manager/users/{id}/
    def destroy(self, request, pk=None):
        # Use the pk parameter from the URL to identify the user
        # Remove a user from the Manager group
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
        return Response({"message": "ok"}, status=status.HTTP_200_OK)
    

# Endpoint /api/users/
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
# === Menu Item Views ===

# Endpoint /api/menu-items/
class MenuItemsViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsStaffOrReadOnly] 
    pagination_class = CustomPageNumberPagination 
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title']
    ordering_fields = ['price', 'title', 'category__title'] # allow client to specify ordering by price
    filterset_class = MenuItemFilter

# Endpoint /api/categories/
class CategoriesViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly] 
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title']
    ordering_fields = ['title']
    
    # Override delete/destroy(), so no-one can delete categories (as they are a related field in the MenuItem model)
    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Deleting categories is not allowed."}, 
            status = status.HTTP_403_FORBIDDEN
        )
        
# Endpoint /api/cart/
class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        # Return all cart items for the authenticated user. If empty, returns []
        queryset = Cart.objects.filter(user = request.user)
        serializer = CartSerializer(queryset, many = True)
        return Response(serializer.data)
    
    def create(self, request):
        # Use serializer for validation
        serializer = CartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract validated data
        menu_item = serializer.validated_data['menuitem']
        quantity = serializer.validated_data['quantity']
        
        unit_price = menu_item.price 
        total_price = unit_price * quantity  
        
        cart_item, created = Cart.objects.get_or_create(
            user = request.user, 
            menuitem = menu_item,
            defaults = {
                "quantity": quantity,
                "unit_price": unit_price,
                "price": total_price,
            },
        )
        
        if not created:
            # Update quantity instead of creating duplicate
            cart_item.quantity += quantity  
            # Also recalculate the total price for the row
            cart_item.price = cart_item.unit_price * cart_item.quantity
            # Save the updated values to the db
            cart_item.save()
            
        # Use serializer for response
        response_serializer = CartSerializer(cart_item)
        return Response(response_serializer.data, status = status.HTTP_201_CREATED)
    
    def destroy(self, request, pk = None):
        # Remove a specific item from the cart (I.e. Delete row from the Cart table)
        cart_item = get_object_or_404(Cart, user = request.user, pk = pk)
        cart_item.delete()
        return Response(status = status.HTTP_204_NO_CONTENT)
    
    # endpoint /api/cart/clear/
    @action(detail = False, methods = ['delete'])
    def clear(self, request):
        # Clear all items from the user's cart (I.e. Delete all rows in the Cart table for that user)
        Cart.objects.filter(user = request.user).delete()
        return Response(status = status.HTTP_204_NO_CONTENT)