"""Tests for authentication views."""

import copy

from django.conf import settings
from django.core.cache import cache
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.settings import reload_api_settings

from apps.users.models import User


THROTTLE_TEST_SETTINGS = copy.deepcopy(settings.REST_FRAMEWORK)
if "DEFAULT_THROTTLE_RATES" not in THROTTLE_TEST_SETTINGS:
    THROTTLE_TEST_SETTINGS["DEFAULT_THROTTLE_RATES"] = {}
THROTTLE_TEST_SETTINGS["DEFAULT_THROTTLE_RATES"]["login"] = "3/minute"


class LoginViewTest(APITestCase):
    """Test cases for LoginView."""

    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username="admin", password="adminpass123", role=User.Role.ADMIN
        )

        # Create regular user
        self.regular_user = User.objects.create_user(
            username="user", password="userpass123", role=User.Role.USER
        )

        # Create inactive admin
        self.inactive_admin = User.objects.create_user(
            username="inactive",
            password="inactivepass123",
            role=User.Role.ADMIN,
            is_active=False,
        )

        self.login_url = reverse("authentication:login")

    def test_login_with_valid_admin_credentials(self):
        """Test login with valid admin credentials returns tokens."""
        data = {"username": "admin", "password": "adminpass123"}
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "admin")
        self.assertEqual(response.data["user"]["role"], "ADMIN")

    def test_login_with_invalid_password(self):
        """Test login with invalid password fails."""
        data = {"username": "admin", "password": "wrongpassword"}
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)

    def test_login_with_invalid_username(self):
        """Test login with non-existent username fails."""
        data = {"username": "nonexistent", "password": "anypassword"}
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_non_admin_user(self):
        """Test login with non-admin user is forbidden."""
        data = {"username": "user", "password": "userpass123"}
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn("access", response.data)

    def test_login_with_inactive_admin(self):
        """Test login with inactive admin fails."""
        data = {"username": "inactive", "password": "inactivepass123"}
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_username(self):
        """Test login without username fails."""
        data = {"password": "adminpass123"}
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_password(self):
        """Test login without password fails."""
        data = {"username": "admin"}
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_jwt_token_structure(self):
        """Test JWT token has correct structure."""
        data = {"username": "admin", "password": "adminpass123"}
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Token should be a string
        self.assertIsInstance(response.data["tokens"]["access"], str)
        self.assertIsInstance(response.data["tokens"]["refresh"], str)

        # Token should have 3 parts (header.payload.signature)
        access_parts = response.data["tokens"]["access"].split(".")
        self.assertEqual(len(access_parts), 3)

    @override_settings(REST_FRAMEWORK=THROTTLE_TEST_SETTINGS)
    def test_login_rate_limiting_enforced(self):
        """Test that login rate limiting returns 429 after threshold exceeded."""
        cache.clear()
        reload_api_settings()
        self.addCleanup(cache.clear)
        self.addCleanup(reload_api_settings)
        data = {"username": "admin", "password": "wrongpass123"}

        for _ in range(3):
            response = self.client.post(self.login_url, data)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("detail", response.data)


class LogoutViewTest(APITestCase):
    """Test cases for LogoutView."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username="admin", password="adminpass123", role=User.Role.ADMIN
        )
        self.logout_url = reverse("authentication:logout")

    def test_logout_requires_authentication(self):
        """Test logout requires authentication."""
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_authenticated_user(self):
        """Test logout with authenticated user succeeds."""
        # Login first
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)


class TokenRefreshViewTest(APITestCase):
    """Test cases for token refresh."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username="admin", password="adminpass123", role=User.Role.ADMIN
        )
        self.login_url = reverse("authentication:login")
        self.refresh_url = reverse("authentication:token-refresh")

    def test_token_refresh_with_valid_token(self):
        """Test token refresh with valid refresh token."""
        # Get tokens by logging in
        login_data = {"username": "admin", "password": "adminpass123"}
        login_response = self.client.post(self.login_url, login_data)
        refresh_token = login_response.data["tokens"]["refresh"]

        # Refresh token
        refresh_data = {"refresh": refresh_token}
        response = self.client.post(self.refresh_url, refresh_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_token_refresh_with_invalid_token(self):
        """Test token refresh with invalid token fails."""
        refresh_data = {"refresh": "invalid.token.here"}
        response = self.client.post(self.refresh_url, refresh_data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReadinessProbeViewTest(APITestCase):
    """Test cases for ReadinessProbeView."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username="admin", password="adminpass123", role=User.Role.ADMIN
        )
        self.readiness_url = reverse("authentication:readiness")

    def test_readiness_probe_requires_authentication(self):
        """Test readiness probe requires authentication."""
        response = self.client.get(self.readiness_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_readiness_probe_with_authenticated_user(self):
        """Test readiness probe returns correct status."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.readiness_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ready")
        self.assertEqual(response.data["user"], "admin")
        self.assertTrue(response.data["is_admin"])


class LivenessProbeViewTest(APITestCase):
    """Test cases for LivenessProbeView."""

    def setUp(self):
        """Set up test data."""
        self.liveness_url = reverse("authentication:liveness")

    def test_liveness_probe_without_authentication(self):
        """Test liveness probe is accessible without authentication."""
        response = self.client.get(self.liveness_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "live")

    def test_liveness_probe_with_authentication(self):
        """Test liveness probe works with authentication too."""
        admin_user = User.objects.create_user(
            username="admin", password="adminpass123", role=User.Role.ADMIN
        )
        self.client.force_authenticate(user=admin_user)

        response = self.client.get(self.liveness_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "live")
