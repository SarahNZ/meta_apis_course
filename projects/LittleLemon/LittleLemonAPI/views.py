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
@api_view(['GET','POST', 'DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def delivery_crew(request):
    delivery_crew = get_object_or_404(Group, name = "Delivery Crew")
    
    if request.method == 'GET':
        delivery_users = delivery_crew.user_set.all()
        serializer = UserSerializer(delivery_users, many = True)
        return Response(serializer.data)
    elif request.method in ['POST', 'DELETE']:
        username = request.data.get('username')
        if username:
            user = get_object_or_404(User, username = username)
            if request.method == 'POST':
                delivery_crew.user_set.add(user)
                return Response({"message": "ok"}, status.HTTP_201_CREATED)
            elif request.method == 'DELETE':
                delivery_crew.user_set.remove(user)
                return Response({"message": "ok"}, status.HTTP_200_OK)

    # Other HTTP Methods such as PUT and PATCH methods are not supported
    return Response({"message": "error"}, status.HTTP_400_BAD_REQUEST)

# Endpoint /api/groups/manager/users/
@api_view(['GET','POST', 'DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def managers(request):
    username = request.data.get('username')
    managers_group = Group.objects.get(name = "Manager")
    if request.method == 'GET':
        manager_users = managers_group.user_set.all()
        serializer = UserSerializer(manager_users, many = True)
        return Response(serializer.data)
    if username:
        user = get_object_or_404(User, username = username)
        if request.method == 'POST':
            managers_group.user_set.add(user)  
            # Set user as staff when added to managers
            user.is_staff = True
            user.save()    
            return Response({"message": "ok"}, status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            managers_group.user_set.remove(user)
            # Remove staff status when user is removed from Managers group
            user.is_staff = False
            user.save()   
            return Response({"message": "ok"}, status.HTTP_200_OK)

    # Unsupported HTTP methods will return a 405 (and not hit the code below)
    return Response({"message": "error"}, status.HTTP_400_BAD_REQUEST)

# Endpoint /api/users/
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def users(request):
    all_users = User.objects.all()
    serializer = UserSerializer(all_users, many = True)
    return Response(serializer.data)
    
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