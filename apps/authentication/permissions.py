from rest_framework import permissions
from apps.users.models import User


class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admin users.
    """
    
    message = 'Only administrators can access this resource'
    
    def has_permission(self, request, view):
        """Check if user is authenticated and has admin role."""
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_admin
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow users to access their own data or admins.
    """

    message = 'You do not have permission to access this resource'

    def has_object_permission(self, request, view, obj):
        """Check if user is owner or admin."""
        if request.user.is_admin:
            return True
        if isinstance(obj, User):
            return obj == request.user
        # Preferred explicit fields
        for field in ("created_by", "owner", "user"):
            if hasattr(obj, field):
                owner = getattr(obj, field)
                if isinstance(owner, User):
                    return owner == request.user
                if owner == request.user.id:
                    return True
        return False


class IsAdminUser(permissions.IsAuthenticated):
    """Authenticated and admin users only."""

    message = 'Only administrators can access this resource'

    def has_permission(self, request, view):
        return super().has_permission(request, view) and getattr(request.user, "is_admin", False)