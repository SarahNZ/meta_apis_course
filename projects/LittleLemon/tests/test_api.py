from django.urls import reverse  
from rest_framework.test import APITestCase, APIClient 
from rest_framework import status
from django.contrib.auth.models import User

# To run all the tests in the project use "pytest tests/ -v" from the project-level directory,
# or run all the tests in a single test file use "pytest tests/test_api.py -v",
# or run one method such as the login test use "pytest tests/test_api.py::UserAPITestCase::test_login -v"
# Note: "-v" shows each test name and result, and --tb=short shows short tracebacks on failure
# "--maxfail=1 --disable-warnings" are useful to stop after the first failure, and hide warning messages
# pytest will automatically set up a temporary test database

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
        print(response.json())  # Will show the dict in the terminal if run with "-s"
        self.assertIn('auth_token', response_json)
        # self.assertIn('auth_token', response.json(), msg=f"Response JSON: {response.json()}") # pytest will print the JSON if the test fails