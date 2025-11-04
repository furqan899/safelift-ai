"""
Tests for User permissions.
"""
from django.test import TestCase, RequestFactory
from apps.users.models import User
from apps.users.permissions import IsAdminUser, CanAccessUser


class IsAdminUserPermissionTest(TestCase):
    """Test cases for IsAdminUser permission."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.permission = IsAdminUser()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='pass123',
            role=User.Role.ADMIN
        )
        self.regular_user = User.objects.create_user(
            username='user',
            password='pass123',
            role=User.Role.USER
        )
        self.superuser = User.objects.create_superuser(
            username='super',
            password='pass123'
        )

    def test_admin_user_has_permission(self):
        """Test admin user has permission."""
        request = self.factory.get('/')
        request.user = self.admin_user
        
        has_permission = self.permission.has_permission(request, None)
        
        self.assertTrue(has_permission)

    def test_superuser_has_permission(self):
        """Test superuser has permission."""
        request = self.factory.get('/')
        request.user = self.superuser
        
        has_permission = self.permission.has_permission(request, None)
        
        self.assertTrue(has_permission)

    def test_regular_user_denied_permission(self):
        """Test regular user is denied permission."""
        request = self.factory.get('/')
        request.user = self.regular_user
        
        has_permission = self.permission.has_permission(request, None)
        
        self.assertFalse(has_permission)

    def test_unauthenticated_user_denied_permission(self):
        """Test unauthenticated user is denied permission."""
        from django.contrib.auth.models import AnonymousUser
        
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        has_permission = self.permission.has_permission(request, None)
        
        self.assertFalse(has_permission)


class CanAccessUserPermissionTest(TestCase):
    """Test cases for CanAccessUser permission."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.permission = CanAccessUser()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='pass123',
            role=User.Role.ADMIN
        )
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass123',
            role=User.Role.USER
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass123',
            role=User.Role.USER
        )

    def test_user_can_access_own_data(self):
        """Test user can access their own data."""
        request = self.factory.get('/')
        request.user = self.user1
        
        has_permission = self.permission.has_object_permission(
            request, None, self.user1
        )
        
        self.assertTrue(has_permission)

    def test_admin_can_access_any_user(self):
        """Test admin can access any user's data."""
        request = self.factory.get('/')
        request.user = self.admin_user
        
        has_permission = self.permission.has_object_permission(
            request, None, self.user1
        )
        
        self.assertTrue(has_permission)

    def test_user_cannot_access_other_user_data(self):
        """Test user cannot access other user's data."""
        request = self.factory.get('/')
        request.user = self.user1
        
        has_permission = self.permission.has_object_permission(
            request, None, self.user2
        )
        
        self.assertFalse(has_permission)

    def test_unauthenticated_user_denied(self):
        """Test unauthenticated user is denied by has_permission."""
        from django.contrib.auth.models import AnonymousUser
        
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        has_permission = self.permission.has_permission(request, None)
        self.assertFalse(has_permission)

