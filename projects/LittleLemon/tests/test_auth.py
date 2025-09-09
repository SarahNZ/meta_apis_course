from base_test_utils import BaseAPITestCase

class AuthTests(BaseAPITestCase):
    def test_login_success(self):
        token = self.get_auth_token()
        self.assertIsNotNone(token)
        
    def test_login_failure(self):
        login_url = "/auth/token/login"
        response = self.client.post(login_url, {"username": "wrong", "password": "wrong"}, format = "json")
        self.assertEqual(response.status_code, 400) # type: ignore
