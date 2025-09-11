from rest_framework.permissions import BasePermission, SAFE_METHODS  

class IsStaffOrReadOnly(BasePermission):
    """
    Allow read-only access for authenticated users,
    but write access only for staff users
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff
    