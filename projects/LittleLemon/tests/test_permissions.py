from base_test import BaseAPITestCase
from endpoints import MANAGERS

class ManagersPermissionTests(BaseAPITestCase):
    def test_manager_views_list_of_users_in_manager_group(self):
        self.add_user_to_manager_group(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        response = self.client.get(MANAGERS)
        self.assertEqual(response.status_code, 200) # type: ignore
        
    def test_authenticated_and_authorized_admin_access(self):
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        response = self.client.get(MANAGERS)
        self.assertEqual(response.status_code, 200) # type: ignore
        
    def test_unauthenticated_access(self):
        response = self.client.get(MANAGERS)
        self.assertEqual(response.status_code, 401) # 401 Unauthorized for unauthenticated users # type: ignore

    def test_authenticated_but_not_authorized_access(self):
        token = self.get_auth_token()
        self.authenticate_client(token)
        response = self.client.get(MANAGERS)
        self.assertEqual(response.status_code, 403) # type: ignore