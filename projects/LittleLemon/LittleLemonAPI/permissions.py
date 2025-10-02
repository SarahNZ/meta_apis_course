from rest_framework.permissions import BasePermission, SAFE_METHODS  

def is_manager(user):
    """
    Helper function to check if a user belongs to the Manager group.
    """
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name='Manager').exists()

class IsStaffOrReadOnly(BasePermission):
    """
    Only authenticated users can read (GET, HEAD, OPTIONS).
    Only staff users can create, update, delete.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            # Only allow authenticated users to read
            return bool(request.user and request.user.is_authenticated)

        # Otherwise (POST, PUT, PATCH, DELETE) → only staff users allowed
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)