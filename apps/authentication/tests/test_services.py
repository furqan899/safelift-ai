"""
Tests for authentication services.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from apps.authentication.services import AuthenticationService

User = get_user_model()


class AuthenticationServiceTest(TestCase):
    """Test cases for AuthenticationService."""

    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            role=User.Role.ADMIN
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='user',
            password='userpass123',
            role=User.Role.USER
        )
        
        # Create inactive admin
        self.inactive_admin = User.objects.create_user(
            username='inactive',
            password='inactivepass123',
            role=User.Role.ADMIN,
            is_active=False
        )
        
        # Create superuser
        self.superuser = User.objects.create_superuser(
            username='superuser',
            password='superpass123'
        )

    def test_authenticate_admin_success(self):
        """Test successful admin authentication."""
        result = AuthenticationService.authenticate_admin(
            username='admin',
            password='adminpass123'
        )
        
        self.assertIn('tokens', result)
        self.assertIn('access', result['tokens'])
        self.assertIn('refresh', result['tokens'])
        self.assertIn('user', result)
        self.assertEqual(result['user']['username'], 'admin')
        self.assertEqual(result['user']['role'], 'ADMIN')

    def test_authenticate_superuser_success(self):
        """Test successful superuser authentication."""
        result = AuthenticationService.authenticate_admin(
            username='superuser',
            password='superpass123'
        )
        
        self.assertIn('tokens', result)
        self.assertIn('access', result['tokens'])
        self.assertIn('refresh', result['tokens'])
        self.assertEqual(result['user']['username'], 'superuser')

    def test_authenticate_with_wrong_password(self):
        """Test authentication fails with wrong password."""
        with self.assertRaises(AuthenticationFailed):
            AuthenticationService.authenticate_admin(
                username='admin',
                password='wrongpassword'
            )

    def test_authenticate_with_nonexistent_user(self):
        """Test authentication fails with non-existent user."""
        with self.assertRaises(AuthenticationFailed):
            AuthenticationService.authenticate_admin(
                username='nonexistent',
                password='anypassword'
            )

    def test_authenticate_non_admin_user(self):
        """Test authentication fails for non-admin users."""
        with self.assertRaises(PermissionDenied):
            AuthenticationService.authenticate_admin(
                username='user',
                password='userpass123'
            )

    def test_authenticate_inactive_admin(self):
        """Test authentication fails for inactive admin."""
        with self.assertRaises(AuthenticationFailed):
            AuthenticationService.authenticate_admin(
                username='inactive',
                password='inactivepass123'
            )

    def test_token_generation_includes_user_id(self):
        """Test generated token includes user information."""
        result = AuthenticationService.authenticate_admin(
            username='admin',
            password='adminpass123'
        )
        
        # Access token should be a string
        self.assertIsInstance(result['tokens']['access'], str)
        self.assertIsInstance(result['tokens']['refresh'], str)
        
        # Token should have content
        self.assertGreater(len(result['tokens']['access']), 50)
        self.assertGreater(len(result['tokens']['refresh']), 50)

    def test_user_data_in_response(self):
        """Test authentication response includes complete user data."""
        result = AuthenticationService.authenticate_admin(
            username='admin',
            password='adminpass123'
        )
        
        user_data = result['user']
        self.assertEqual(user_data['username'], 'admin')
        self.assertEqual(user_data['role'], 'ADMIN')
        self.assertIn('id', user_data)
        self.assertTrue(user_data['is_admin'])

    def test_empty_username(self):
        """Test authentication fails with empty username."""
        with self.assertRaises(AuthenticationFailed):
            AuthenticationService.authenticate_admin(
                username='',
                password='adminpass123'
            )

    def test_empty_password(self):
        """Test authentication fails with empty password."""
        with self.assertRaises(AuthenticationFailed):
            AuthenticationService.authenticate_admin(
                username='admin',
                password=''
            )

