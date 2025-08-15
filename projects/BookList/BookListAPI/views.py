from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

@api_view(['GET', 'POST'])
def books(request):
    return Response('List of the books', status = status.HTTP_200_OK)