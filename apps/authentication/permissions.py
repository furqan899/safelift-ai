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
        # Check if user is admin
        if request.user.is_admin:
            return True

        # For User objects, check if it's the same user
        if isinstance(obj, User):
            return obj == request.user

        # Check ownership - try common fields
        owner_fields = ['user', 'owner', 'created_by', 'user_id', 'owner_id']
        for field in owner_fields:
            if hasattr(obj, field):
                owner = getattr(obj, field)
                if isinstance(owner, User):
                    return owner == request.user
                elif owner == request.user.id:
                    return True

        # Fallback to direct id comparison (for User objects)
        return hasattr(obj, 'id') and obj.id == request.user.id