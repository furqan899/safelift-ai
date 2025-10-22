from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user operations with enhanced validation.
    """
    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8,
        style={'input_type': 'password'},
        help_text="Password must be at least 8 characters long"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
        help_text="Confirm password (required when setting password)"
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'password_confirm', 'role', 'is_active']
        read_only_fields = ['id']
        extra_kwargs = {
            'username': {
                'required': True,
                'help_text': 'Unique username for the user'
            },
            'role': {
                'required': False,
                'help_text': 'User role (USER or ADMIN)'
            },
            'is_active': {
                'required': False,
                'help_text': 'Whether the user account is active'
            }
        }

    def validate_username(self, value):
        """Validate username uniqueness."""
        queryset = User.objects.filter(username=value)
        if self.instance:
            # Exclude current instance when updating
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate(self, attrs):
        """Validate password confirmation and admin role restrictions."""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        # Check if this is a creation (no instance) or update
        is_creation = self.instance is None

        # Check password confirmation for creation
        if is_creation and password:  # Creating new user
            if not password_confirm:
                raise serializers.ValidationError({
                    'password_confirm': 'Password confirmation is required when setting a password.'
                })
            if password != password_confirm:
                raise serializers.ValidationError({
                    'password': 'Passwords do not match.',
                    'password_confirm': 'Passwords do not match.'
                })

        # Check role restrictions
        role = attrs.get('role')
        if is_creation and role and role == User.Role.ADMIN:
            # Check if current user is admin (for creation)
            request = self.context.get('request')
            if request and not request.user.is_admin:
                raise serializers.ValidationError({
                    'role': 'Only administrators can create admin users.'
                })

        return attrs

    def create(self, validated_data):
        """Create new user with encrypted password."""
        validated_data.pop('password_confirm', None)  # Remove confirmation field
        password = validated_data.pop('password', None)

        user = User(**validated_data)
        if password:
            # Validate password strength
            validate_password(password, user)
            user.set_password(password)
        else:
            # Set unusable password if no password provided
            user.set_unusable_password()

        user.save()
        return user

    def update(self, instance, validated_data):
        """Update user with proper field handling."""
        validated_data.pop('password_confirm', None)  # Remove confirmation field
        password = validated_data.pop('password', None)

        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Handle password separately
        if password:
            # Validate password strength
            validate_password(password, instance)
            instance.set_password(password)

        instance.save()
        return instance
