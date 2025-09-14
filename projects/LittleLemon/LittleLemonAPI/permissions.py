from rest_framework.permissions import BasePermission, SAFE_METHODS  

class IsStaffOrReadOnly(BasePermission):
    """
    Only authenticated users can read (GET, HEAD, OPTIONS).
    Only staff/admin users can create, update, delete.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            # Only allow authenticated users to read
            return bool(request.user and request.user.is_authenticated)

        # Otherwise (POST, PUT, PATCH, DELETE) → only staff allowed
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)