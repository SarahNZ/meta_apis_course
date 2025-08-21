from rest_framework import generics
from .models import MenuItem
from .models import Category
from .serializers import MenuItemSerializer
from .serializers import CategorySerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404

@api_view()
def menu_items(request):
    items = MenuItem.objects.select_related('category').all()
    serialized_item = MenuItemSerializer(items, many = True, context = {'request': request})
    return Response(serialized_item.data)

@api_view()
def single_item(request, id):
    item = get_object_or_404(MenuItem, pk = id)
    serialized_item = MenuItemSerializer(item)
    return Response(serialized_item.data)

@api_view()
def category_detail(request, pk):
    category = get_object_or_404(Category, pk = pk)
    serialized_category = CategorySerializer(category)
    return Response(serialized_category.data)

class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

class SingleMenuItemView(generics.RetrieveUpdateAPIView, generics.DestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    
