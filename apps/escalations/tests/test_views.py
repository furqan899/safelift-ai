"""
Tests for Escalation views.
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.escalations.models import Escalation
from apps.users.models import User


class EscalationViewSetTest(APITestCase):
    """Test cases for EscalationViewSet."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='pass123',
            role=User.Role.ADMIN,
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='user',
            password='pass123',
            role=User.Role.USER
        )
        
        # Create test escalations
        self.escalation1 = Escalation.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-001',
            problem_description='Test problem 1',
            language='en',
            status=Escalation.Status.PENDING,
            priority=Escalation.Priority.HIGH
        )
        self.escalation2 = Escalation.objects.create(
            customer_name='Jane Smith',
            customer_email='jane@example.com',
            equipment_id='SL-002',
            problem_description='Test problem 2',
            language='sv',
            status=Escalation.Status.IN_PROGRESS,
            priority=Escalation.Priority.MEDIUM
        )
        
        self.list_url = reverse('escalation-list')

    def get_detail_url(self, escalation_id):
        """Helper to get detail URL."""
        return reverse('escalation-detail', kwargs={'pk': escalation_id})

    def test_list_escalations_requires_admin(self):
        """Test listing escalations requires admin access."""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_escalations_as_admin(self):
        """Test admin can list escalations."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 2)

    def test_retrieve_escalation_as_admin(self):
        """Test admin can retrieve escalation details."""
        self.client.force_authenticate(user=self.admin_user)
        url = self.get_detail_url(self.escalation1.id)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['customer_name'], 'John Doe')
        self.assertEqual(response.data['equipment_id'], 'SL-001')

    def test_update_escalation_as_admin(self):
        """Test admin can update escalation."""
        self.client.force_authenticate(user=self.admin_user)
        url = self.get_detail_url(self.escalation1.id)
        
        data = {
            'status': 'in_progress',
            'priority': 'high',
            'internal_notes': 'Updated notes'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')
        self.assertEqual(response.data['internal_notes'], 'Updated notes')

    def test_partial_update_escalation(self):
        """Test partial update of escalation."""
        self.client.force_authenticate(user=self.admin_user)
        url = self.get_detail_url(self.escalation1.id)
        
        data = {'status': 'resolved'}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'resolved')

    def test_filter_by_status(self):
        """Test filtering escalations by status."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.list_url, {'status': 'pending'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        for escalation in results:
            self.assertEqual(escalation['status'], 'pending')

    def test_filter_by_priority(self):
        """Test filtering escalations by priority."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.list_url, {'priority': 'high'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        for escalation in results:
            self.assertEqual(escalation['priority'], 'high')

    def test_filter_by_language(self):
        """Test filtering escalations by language."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.list_url, {'language': 'sv'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        for escalation in results:
            self.assertEqual(escalation['language'], 'sv')

    def test_search_by_customer_name(self):
        """Test searching escalations by customer name."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.list_url, {'q': 'John'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_search_by_equipment_id(self):
        """Test searching escalations by equipment ID."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(self.list_url, {'q': 'SL-001'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_set_status_action(self):
        """Test set_status action updates escalation status."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('escalation-set-status', kwargs={'pk': self.escalation1.id})
        
        data = {
            'status': 'in_progress',
            'internal_notes': 'Working on it'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')

    def test_stats_endpoint_returns_summary_counts(self):
        """Test stats endpoint returns summary counts."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('escalation-stats')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total', response.data)
        self.assertIn('pending', response.data)
        self.assertIn('in_progress', response.data)
        self.assertIn('resolved', response.data)
        
        # Check values are correct
        self.assertEqual(response.data['total'], 2)
        self.assertEqual(response.data['pending'], 1)
        self.assertEqual(response.data['in_progress'], 1)

