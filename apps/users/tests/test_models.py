"""
Tests for User model.
"""
from django.test import TestCase
from apps.users.models import User


class UserModelTest(TestCase):
    """Test cases for User model."""

    def test_user_creation_with_default_role(self):
        """Test creating user with default USER role."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.role, User.Role.USER)
        self.assertFalse(user.is_admin)
        self.assertTrue(user.is_active)

    def test_user_creation_with_admin_role(self):
        """Test creating user with ADMIN role."""
        user = User.objects.create_user(
            username='adminuser',
            password='adminpass123',
            role=User.Role.ADMIN
        )
        
        self.assertEqual(user.username, 'adminuser')
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertTrue(user.is_admin)

    def test_superuser_creation(self):
        """Test creating superuser."""
        user = User.objects.create_superuser(
            username='superuser',
            password='superpass123'
        )
        
        self.assertEqual(user.username, 'superuser')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_admin)

    def test_is_admin_property_for_admin_user(self):
        """Test is_admin property returns True for admin users."""
        user = User.objects.create_user(
            username='admin',
            password='pass123',
            role=User.Role.ADMIN
        )
        
        self.assertTrue(user.is_admin)

    def test_is_admin_property_for_regular_user(self):
        """Test is_admin property returns False for regular users."""
        user = User.objects.create_user(
            username='user',
            password='pass123',
            role=User.Role.USER
        )
        
        self.assertFalse(user.is_admin)

    def test_is_admin_property_for_superuser(self):
        """Test is_admin property returns True for superusers."""
        user = User.objects.create_superuser(
            username='super',
            password='pass123'
        )
        
        self.assertTrue(user.is_admin)

    def test_user_string_representation(self):
        """Test user __str__ method."""
        user = User.objects.create_user(
            username='testuser',
            password='pass123',
            role=User.Role.ADMIN
        )
        
        expected = 'testuser (Admin)'
        self.assertEqual(str(user), expected)

    def test_user_string_representation_regular_user(self):
        """Test user __str__ method for regular user."""
        user = User.objects.create_user(
            username='regularuser',
            password='pass123',
            role=User.Role.USER
        )
        
        expected = 'regularuser (User)'
        self.assertEqual(str(user), expected)

    def test_username_field_configuration(self):
        """Test USERNAME_FIELD is set to username."""
        self.assertEqual(User.USERNAME_FIELD, 'username')

    def test_required_fields_configuration(self):
        """Test REQUIRED_FIELDS configuration."""
        self.assertEqual(User.REQUIRED_FIELDS, [])

    def test_user_password_is_hashed(self):
        """Test user password is properly hashed."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Password should be hashed, not plain text
        self.assertNotEqual(user.password, 'testpass123')
        self.assertTrue(user.check_password('testpass123'))

    def test_role_choices(self):
        """Test role choices are correctly defined."""
        choices = User.Role.choices
        
        self.assertEqual(len(choices), 2)
        self.assertIn(('USER', 'User'), choices)
        self.assertIn(('ADMIN', 'Admin'), choices)

    def test_db_table_name(self):
        """Test database table name."""
        self.assertEqual(User._meta.db_table, 'users')

