from django.urls import path
from . import views

urlpatterns = [
    path('numbers', views.display_even_numbers),
]