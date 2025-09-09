from base_test_utils import BaseAPITestCase 
from test_managers import ManagerGroupTests

class PermissionTests(BaseAPITestCase):
    def test_unauthenticated_access(self):
        url = "/api/groups/manager/users/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401) # 401 Unauthorized for unauthenticated users # type: ignore

    def test_authenticated_but_not_authorized_access(self):
        token = self.get_auth_token()
        self.authenticate_client(token)
        url = "/api/groups/manager/users/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403) # type: ignore
    
    def test_authenticated_and_authorized_access(self):
        self.add_user_to_manager_group(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        url = "/api/groups/manager/users/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200) # type: ignore