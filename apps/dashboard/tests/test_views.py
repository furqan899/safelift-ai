"""
Tests for Dashboard views.
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User


class DashboardOverviewViewTest(APITestCase):
    """Test cases for DashboardOverviewView."""

    def setUp(self):
        """Set up test data."""
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
        self.url = reverse('dashboard:overview')

    def test_dashboard_requires_admin(self):
        """Test dashboard overview requires admin access."""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dashboard_without_authentication(self):
        """Test dashboard requires authentication."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_returns_all_metrics(self):
        """Test dashboard returns all required metrics."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check all required fields are present
        self.assertIn('active_conversations', response.data)
        self.assertIn('total_users', response.data)
        self.assertIn('resolution_rate', response.data)
        self.assertIn('escalated_cases', response.data)
        self.assertIn('response_time', response.data)
        self.assertIn('language_distribution', response.data)
        self.assertIn('quick_actions', response.data)

    def test_dashboard_with_superuser(self):
        """Test dashboard works with superuser."""
        superuser = User.objects.create_superuser(
            username='super',
            password='pass123'
        )
        self.client.force_authenticate(user=superuser)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LanguageDistributionViewTest(APITestCase):
    """Test cases for LanguageDistributionView."""

    def setUp(self):
        """Set up test data."""
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
        self.url = reverse('dashboard:language-distribution')

    def test_language_distribution_requires_admin(self):
        """Test language distribution requires admin access."""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_language_distribution_with_default_days(self):
        """Test language distribution with default 30 days."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_language_distribution_with_custom_days(self):
        """Test language distribution with custom days parameter."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url, {'days': 7})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_language_distribution_validates_days_parameter(self):
        """Test days parameter validation (1-365)."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Test days < 1
        response = self.client.get(self.url, {'days': 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test days > 365
        response = self.client.get(self.url, {'days': 400})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test valid days
        response = self.client.get(self.url, {'days': 60})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_language_distribution_invalid_days_format(self):
        """Test invalid days parameter format."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url, {'days': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class QuickActionsViewTest(APITestCase):
    """Test cases for QuickActionsView."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='pass123',
            role=User.Role.ADMIN
        )
        self.url = reverse('dashboard:quick-actions')

    def test_quick_actions_requires_authentication(self):
        """Test quick actions requires authentication."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_quick_actions_returns_list(self):
        """Test quick actions returns list of actions."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        
        # Should have at least some quick actions
        if len(response.data) > 0:
            action = response.data[0]
            # Check action has required fields
            self.assertIn('title', action)
            self.assertIn('description', action)


class HealthStatusViewTest(APITestCase):
    """Test cases for HealthStatusView."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='pass123',
            role=User.Role.ADMIN
        )
        self.url = reverse('dashboard:health')

    def test_health_status_requires_authentication(self):
        """Test health status requires authentication."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_health_status_returns_healthy(self):
        """Test health status returns healthy status."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
        self.assertIn('message', response.data)

