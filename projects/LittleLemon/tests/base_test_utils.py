from django.contrib.auth.models import User, Group
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

'''
To use these tests, install pytest and pytest-django first (using pipenv)
To run all the tests in the project use "pytest tests/ -v" from the project-level directory,
or run all the tests in a single test file use e.g. "pytest tests/test_api.py -v",
or run one method such as the login test use "pytest tests/test_api.py::UserAPITestCase::test_login -v"

Note: "-v" shows each test name and result in the terminal output, and --tb=short shows short tracebacks on failure
"--maxfail=1 --disable-warnings" are useful to stop after the first failure, and hide warning messages.

To see print() output in the terminal, run pytest with the "-s" option, or pytest will print the JSON if a test 
fails if you add a msg parameter to the assertion. E.g. "self.assertIn('auth_token', response.json(), msg=f"Response JSON: {response.json()}") "

In Django's test framework, each test method runs in its own isolated transaction and uses a separate test database that is reset for each test class.
'''

class BaseAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
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
        login_url = "/auth/token/login/"  # Djoser login endpoint
        response = self.client.post(login_url, {"username": username, "password": password}, format="json")
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
        
    def add_user_to_delivery_crew_group(self, user=None):
        """
        Adds the specified user (or self.user1 if not provided) to the Delivery Crew group.
        """
        user = user or self.user1
        user.groups.add(self.delivery_crew_group)
