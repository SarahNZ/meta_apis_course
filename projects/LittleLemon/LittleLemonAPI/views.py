from django.contrib.auth.models import User, Group
from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .permissions import IsManager
from .serializers import UserSerializer

# Endpoint /api/groups/manager/users/
@api_view(['GET','POST', 'DELETE'])
@permission_classes([IsManager])
def managers(request):
        managers_group = get_object_or_404(Group, name = "Manager")
        
        if request.method == 'GET':
            manager_users = managers_group.user_set.all()
            serializer = UserSerializer(manager_users, many = True)
            return Response(serializer.data)
        elif request.method in ['POST', 'DELETE']:
            username = request.data.get('username')
            if username:
                user = get_object_or_404(User, username = username)
                if request.method == 'POST':
                    managers_group.user_set.add(user)
                    return Response({"message": "ok"}, status.HTTP_201_CREATED)
                elif request.method == 'DELETE':
                    managers_group.user_set.remove(user)
                    return Response({"message": "ok"}, status.HTTP_200_OK)

        return Response({"message": "error"}, status.HTTP_400_BAD_REQUEST)