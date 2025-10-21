from rest_framework import serializers
from apps.users.models import User


class LoginSerializer(serializers.Serializer):
    """
    Serializer for admin login credentials validation.
    
    Validates username and password for admin authentication.
    Does not include user object in response data.
    """
    
    username = serializers.CharField(
        max_length=150,
        required=True,
        error_messages={
            'required': 'Username is required',
            'blank': 'Username cannot be blank'
        }
    )
    password = serializers.CharField(
        max_length=128,
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Password is required',
            'blank': 'Password cannot be blank'
        }
    )

    def validate(self, attrs):
        """
        Validate credentials but don't authenticate here.
        Authentication logic should be in the service layer.
        """
        return attrs


class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response data."""
    
    message = serializers.CharField()
    user = serializers.DictField()
    tokens = serializers.DictField()


class LogoutSerializer(serializers.Serializer):
    """Serializer for logout response."""
    
    message = serializers.CharField()
