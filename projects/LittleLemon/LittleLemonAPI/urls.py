from django.urls import path
from . import views

urlpatterns = [
    path('groups/manager/users/', views.managers),
    path('groups/delivery-crew/users/', views.delivery_crew),
    path('users/', views.users),
    path('menu-items/', views.menu_items),
]