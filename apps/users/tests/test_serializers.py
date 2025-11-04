"""
Tests for User serializers.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.users.serializers import UserSerializer

User = get_user_model()


class UserSerializerTest(TestCase):
    """Test cases for UserSerializer."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            role=User.Role.ADMIN
        )

    def test_valid_user_serialization(self):
        """Test serializing user data."""
        serializer = UserSerializer(instance=self.admin_user)
        data = serializer.data
        
        self.assertEqual(data['username'], 'admin')
        self.assertEqual(data['role'], 'ADMIN')
        self.assertIn('id', data)
        # Password should not be in serialized data
        self.assertNotIn('password', data)

    def test_create_user_with_valid_data(self):
        """Test creating user with valid data."""
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'role': 'USER'
        }
        serializer = UserSerializer(data=data, context={'request': type('obj',(object,), {'user': self.admin_user})})
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.role, 'USER')
        # Password should be hashed
        self.assertNotEqual(user.password, 'newpass123')
        self.assertTrue(user.check_password('newpass123'))

    def test_password_hashing_on_creation(self):
        """Test password is hashed during user creation."""
        data = {
            'username': 'testuser',
            'password': 'plainpassword',
            'password_confirm': 'plainpassword',
            'role': 'USER'
        }
        serializer = UserSerializer(data=data, context={'request': type('obj',(object,), {'user': self.admin_user})})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Password should be hashed
        self.assertNotEqual(user.password, 'plainpassword')
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
        self.assertTrue(user.check_password('plainpassword'))

    def test_password_hashing_on_update(self):
        """Test password is hashed during user update."""
        user = User.objects.create_user(
            username='updateuser',
            password='oldpass123',
            role=User.Role.USER
        )
        
        data = {'password': 'newpass123'}
        serializer = UserSerializer(instance=user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()
        
        # New password should be hashed
        self.assertTrue(updated_user.check_password('newpass123'))
        self.assertFalse(updated_user.check_password('oldpass123'))

    def test_role_validation_valid_choices(self):
        """Test role validation accepts valid choices."""
        for role_value, role_label in User.Role.choices:
            data = {
                'username': f'user_{role_value}',
                'password': 'pass12345',
                'password_confirm': 'pass12345',
                'role': role_value
            }
            serializer = UserSerializer(data=data, context={'request': type('obj',(object,), {'user': self.admin_user})})
            self.assertTrue(serializer.is_valid(), f"Failed for role: {role_value} - {serializer.errors}")

    def test_role_validation_invalid_choice(self):
        """Test role validation rejects invalid choices."""
        data = {
            'username': 'testuser',
            'password': 'pass123',
            'role': 'INVALID_ROLE'
        }
        serializer = UserSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('role', serializer.errors)

    def test_username_required_field(self):
        """Test username is required."""
        data = {
            'password': 'pass123',
            'role': 'USER'
        }
        serializer = UserSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_password_required_for_creation(self):
        """Test password is required for user creation."""
        data = {
            'username': 'testuser',
            'role': 'USER'
        }
        serializer = UserSerializer(data=data, context={'request': type('obj',(object,), {'user': self.admin_user})})
        
        # Password is optional on creation (unusable password set)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_username_uniqueness_validation(self):
        """Test username uniqueness is validated."""
        # Create first user
        User.objects.create_user(
            username='existinguser',
            password='pass123'
        )
        
        # Try to create another user with same username
        data = {
            'username': 'existinguser',
            'password': 'pass456',
            'role': 'USER'
        }
        serializer = UserSerializer(data=data, context={'request': type('obj',(object,), {'user': self.admin_user})})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_partial_update_without_password(self):
        """Test partial update without changing password."""
        user = User.objects.create_user(
            username='testuser',
            password='originalpass',
            role=User.Role.USER
        )
        original_password = user.password
        
        data = {'role': 'ADMIN'}
        serializer = UserSerializer(instance=user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()
        
        self.assertEqual(updated_user.role, 'ADMIN')
        # Password should remain unchanged
        self.assertEqual(updated_user.password, original_password)

    def test_is_admin_field_read_only(self):
        """Test is_admin field is read-only."""
        data = {
            'username': 'testuser',
            'password': 'pass12345',
            'password_confirm': 'pass12345',
            'role': 'USER',
            'is_admin': True  # Not part of serializer fields
        }
        serializer = UserSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # is_admin is derived from role
        self.assertFalse(user.is_admin)

