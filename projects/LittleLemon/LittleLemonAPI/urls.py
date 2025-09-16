from django.urls import path, include  
from rest_framework.decorators import action 
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, CategoriesViewSet, MenuItemsViewSet
from . import views

router = DefaultRouter()
router.register('carts', CartViewSet, basename = 'cart')
router.register('categories', CategoriesViewSet, basename = 'category')
router.register('menu-items', MenuItemsViewSet, basename = 'menuitem')

urlpatterns = [
    path('groups/manager/users/', views.managers),
    path('groups/delivery-crew/users/', views.delivery_crew),
    path('users/', views.users),
    path('', include(router.urls)),
]