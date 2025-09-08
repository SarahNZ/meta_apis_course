from django.urls import reverse  
from rest_framework.test import APITestCase, APIClient 
from rest_framework import status
from django.contrib.auth.models import User

# Run the tests from the project-level directory using "pytest tests/test_api.py -v"

class UserAPITestCase(APITestCase):
    def setUp(self): 
        self.client = APIClient()
        self.username1 = "testuser1"
        self.password = "pass1234"
        self.user1 = User.objects.create_user(username = self.username1, password = self.password)
    
    def test_login(self):
        url = "/auth/token/login/"
        data = {
            "username": self.username1,
            "password": self.password
        }
        
        response = self.client.post(url, data, format ='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertIn('auth_token', response_json)