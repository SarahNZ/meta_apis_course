from django.urls import path
from . import views

urlpatterns = [
    path('groups/manager/users/', views.managers)
]