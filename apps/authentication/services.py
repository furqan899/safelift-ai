from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.models import User


class AuthenticationService:
    @staticmethod
    def authenticate_admin(username: str, password: str) -> dict:
        """
        Authenticate an admin user and generate JWT tokens.

        Args:
            username (str): User's username
            password (str): User's password

        Returns:
            dict: Authentication data including user info and tokens

        Raises:
            AuthenticationFailed: If credentials are invalid
            PermissionDenied: If user is not an admin
        """
        user = authenticate(username=username, password=password)
        if not user:
            raise AuthenticationFailed("Invalid username or password")

        if not user.is_admin:
            raise PermissionDenied("Only administrators can access this system")

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "is_admin": user.is_admin,
            },
            "tokens": {"refresh": str(refresh), "access": str(access)},
        }
