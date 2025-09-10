from django.contrib.auth.models import User, Group
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from endpoints import LOGIN   

'''
INSTALL 
To use these tests, install pytest and pytest-django first (using pipenv)

COMMANDS TO RUN TESTS
- To run all the tests in the project use "pytest tests/ -v" from the project-level directory
- To run all the tests in a single test file use e.g. "pytest tests/test_api.py -v"
- To run one method such as the login test use "pytest tests/test_api.py::UserAPITestCase::test_login -v"

FLAGS
-v (verbose) shows each test name and result in the terminal output
--tb=short shows short tracebacks on failure
--maxfail=1 stops after the first failure
--disable-warning hides warning messages
-s to see print() output in the terminal 

PRINT JSON RESPONSE
If you add a msg parameter to the assertion. E.g. "self.assertIn('auth_token', response.json(), msg=f"Response JSON: {response.json()}") "

TEST DB/TRANSACTIONS
In Django's test framework, each test method runs in its own isolated transaction and uses a separate test database that is reset for each test class.

USEFUL COMMAND
pytest tests/test_api.py -v --tb=short --maxfail=1 --disable-warnings   
'''

class BaseAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test user
        self.username1 = "testuser1"
        self.password = "pass1234"
        self.user1 = User.objects.create_user(username=self.username1, password=self.password)

        # Create Managers group
        self.manager_group, _ = Group.objects.get_or_create(name="Manager")   # ", _" avoids a common bug
        
        # Create Delivery Crew group
        self.delivery_crew_group, _ = Group.objects.get_or_create(name="Delivery Crew")   # ", _" avoids a common bug


    def get_auth_token(self, username=None, password=None):
        """
        Logs in a user and returns Djoser token
        """
        username = username or self.username1
        password = password or self.password
        response = self.client.post(LOGIN, {"username": username, "password": password}, format="json")
        self.assertEqual(response.status_code, 200) # type: ignore
        response_json = response.json() # type: ignore
        self.assertIn('auth_token', response_json)
        return response.json()["auth_token"]    # type: ignore

    def authenticate_client(self, token):
        """
        Sets the Authorization header for the test client
        """
        self.client: APIClient = APIClient()    # Type hint for Pylance
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    def add_user_to_manager_group(self, user=None):
        """
        Adds the specified user (or self.user1 if not provided) to the Manager group.
        """
        user = user or self.user1
        user.groups.add(self.manager_group)
        self.give_user_staff_status(user)
        
    def add_user_to_delivery_crew_group(self, user=None):
        """
        Adds the specified user (or self.user1 if not provided) to the Delivery Crew group.
        """
        user = user or self.user1
        user.groups.add(self.delivery_crew_group)
        
    def give_user_staff_status(self, user=None):
        """
        Gives the specified user (or self.user1 if not provided) staff status.
        """
        user = user or self.user1
        user.is_staff = True
        user.save()