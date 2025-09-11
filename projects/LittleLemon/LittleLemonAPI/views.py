from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
from .models import MenuItem
from .permissions import IsStaffOrReadOnly
from .serializers import MenuItemSerializer, UserSerializer

# === Delivery Crew views ===
    
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
    
# === Manager views ===

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
    
# === Menu Item views ===

# Endpoint /api/menu-items/
class MenuItemsViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsStaffOrReadOnly]  
    
# === Custom user views (the rest are handled by Djsoer) ===
    
# Endpoint /api/users/
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def users(request):
    all_users = User.objects.all()
    serializer = UserSerializer(all_users, many = True)
    return Response(serializer.data)