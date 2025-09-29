from django.urls import path, include  
from rest_framework.decorators import action 
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, CategoriesViewSet, DeliveryCrewViewSet, ManagerViewSet, MenuItemsViewSet, UserViewSet, OrderViewSet

router = DefaultRouter()
router.register('cart', CartViewSet, basename = 'cart')
router.register('categories', CategoriesViewSet, basename = 'category')
router.register('groups/delivery-crew/users', DeliveryCrewViewSet, basename = 'delivery-crew')
router.register('groups/manager/users', ManagerViewSet, basename = 'manager')
router.register('menu-items', MenuItemsViewSet, basename = 'menuitem')
router.register('users', UserViewSet, basename = 'user')
router.register('orders', OrderViewSet, basename = 'order')

urlpatterns = [
    path('', include(router.urls)),
]