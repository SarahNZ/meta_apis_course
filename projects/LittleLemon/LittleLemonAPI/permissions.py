from rest_framework.permissions import BasePermission, SAFE_METHODS  

def is_manager(user):
    """
    Helper function to check if a user belongs to the Manager group.
    """
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name='Manager').exists()

def is_delivery_crew(user):
    """
    Helper function to check if a user belongs to the Delivery Crew group.
    """
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name='Delivery Crew').exists()

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

class IsStaffOnly(BasePermission):
    """
    Only staff users can perform any operations (including GET requests).
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)

class IsStaffOrManager(BasePermission):
    """
    Only staff users OR Manager group members can perform any operations (including GET requests).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(request.user.is_staff or is_manager(request.user))