from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from typing import Dict, Any


class AuthenticationService:
    """
    Service class handling authentication business logic.
    
    Separates business logic from views following clean architecture.
    """
    
    @staticmethod
    def authenticate_admin(username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate admin user and generate tokens.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            Dictionary containing user info and JWT tokens
            
        Raises:
            ValidationError: If credentials are invalid or user is not admin
        """
        if not username or not password:
            raise ValidationError({
                'detail': 'Username and password are required'
            })

        user = authenticate(username=username, password=password)
        
        if not user:
            raise AuthenticationFailed({
                'detail': 'Invalid credentials'
            })
        
        if not user.is_active:
            raise ValidationError({
                'detail': 'User account is disabled'
            })
        
        if not user.is_admin:
            raise ValidationError({
                'detail': 'Access denied. Admin privileges required'
            })
        
        return AuthenticationService._generate_auth_response(user)
    
    @staticmethod
    def _generate_auth_response(user) -> Dict[str, Any]:
        """
        Generate authentication response with tokens and user info.
        
        Args:
            user: Authenticated user instance
            
        Returns:
            Dictionary with user data and tokens
        """
        refresh = RefreshToken.for_user(user)
        
        return {
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.get_role_display(),
                'role_code': user.role,
                'is_admin': user.is_admin,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }