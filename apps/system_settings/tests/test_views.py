from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User
from apps.system_settings.models import SystemSettings


class SystemSettingsViewTest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='adminpass123', role=User.Role.ADMIN
        )
        self.user = User.objects.create_user(
            username='user', password='userpass123', role=User.Role.USER
        )
        self.url = reverse('system_settings:system-settings')

    def test_get_requires_admin(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_returns_defaults_for_admin(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('default_language', resp.data)

    def test_put_updates_all_fields(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            'auto_detect_language': False,
            'default_language': 'sv',
            'notification_email': 'admin@safelift.com',
            'escalation_threshold': 5,
            'widget_title': 'Safelift Assistant',
            'welcome_message': 'Hej!'
        }
        resp = self.client.put(self.url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['default_language'], 'sv')
        self.assertEqual(resp.data['escalation_threshold'], 5)

    def test_patch_partial_update(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.patch(self.url, {'widget_title': 'New Title'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['widget_title'], 'New Title')

    def test_validation_threshold_range(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.patch(self.url, {'escalation_threshold': 0}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


