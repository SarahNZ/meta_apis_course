E.g.
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework import viewsets
from rest_framework import generics

@api_view(['GET','POST'])
def books(request):
    return Response('List of the books', status = status.HTTP_200_OK)

class MenuItemViewSet(viewsets.ModelViewSet)
    queryset
    serializer
class ReadOnlyMenuItemView(viewsets.ReadOnlyModelViewSet)
    CreateAPIView
    ListAPIView etc.

class MenuItemView(generics.ListCreateAPIView)
    Permission_classes = [IsAuthenicated]
    
    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET'
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permissin_classes]

class OrderView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenicated]

    def get_queryset(self):
        return Order.objects.all().filter(user = self.request.user)