from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated


class IsAdminUser(IsAuthenticated):
    """
    Custom permission to only allow admin users.
    """

    message = 'Only administrators can access this resource'

    def has_permission(self, request, view):
        """Check if user is authenticated and has admin role."""
        return super().has_permission(request, view) and request.user.is_admin


class CanAccessUser(IsAuthenticated):
    """
    Permission to allow users to access their own data or admins to access any user data.
    """

    message = 'You do not have permission to access this user'

    def has_permission(self, request, view):
        """Check basic permission."""
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific user object."""
        # Admins can access any user
        if request.user.is_admin:
            return True

        # Users can access their own data
        return obj == request.user
