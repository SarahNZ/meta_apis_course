from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User, Group

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

# Create your views here.
# Managers can view a list of all the users in the Manager group GET /api/groups/manager/users
@api_view(['POST', 'DELETE'])
@permission_classes([IsAdminUser])
def managers(request):
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username = username)
            managers = Group.objects.get(name = 'Manager')
            if request.method == 'POST':
                managers.user_set.add(user)
                return Response({"message": "ok"}, status.HTTP_201_CREATED)
            elif request.method == 'DELETE':
                managers.user_set.remove(user)
                return Response({"message": "ok"}, status.HTTP_200_OK)

        return Response({"message": "error"}, status.HTTP_400_BAD_REQUEST)