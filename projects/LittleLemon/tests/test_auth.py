from base_test import BaseAPITestCase
from endpoints import LOGIN

class AuthTests(BaseAPITestCase):
    def test_login_success(self):
        token = self.get_auth_token()
        self.assertIsNotNone(token)
        
    def test_login_failure(self):
        response = self.client.post(LOGIN, {"username": "wrong", "password": "wrong"}, format = "json")
        self.assertEqual(response.status_code, 400) # type: ignore
