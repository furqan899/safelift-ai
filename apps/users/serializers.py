from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class AdminLoginSerializer(serializers.Serializer):
    """
    Serializer for admin login credentials.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate admin credentials."""
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            # Authenticate user
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError(
                        "User account is disabled."
                    )
                if not user.is_admin:
                    raise serializers.ValidationError(
                        "Access denied. Admin privileges required."
                    )
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError(
                    "Invalid credentials."
                )
        else:
            raise serializers.ValidationError(
                "Username and password are required."
            )


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for basic user operations.
    """
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'role']
        read_only_fields = ['id']

    def create(self, validated_data):
        """Create new user with encrypted password."""
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        """Update user."""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
