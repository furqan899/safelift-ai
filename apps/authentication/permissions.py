from rest_framework import permissions


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
        return (
            request.user.is_admin or 
            obj.id == request.user.id
        )