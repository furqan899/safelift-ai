"""
Tests for Escalation serializers.
"""
from django.test import TestCase
from apps.escalations.models import Escalation
from apps.escalations.serializers import (
    EscalationListSerializer,
    EscalationDetailSerializer,
    EscalationUpdateSerializer
)


class EscalationListSerializerTest(TestCase):
    """Test cases for EscalationListSerializer."""

    def test_escalation_list_serializer_structure(self):
        """Test list serializer includes essential fields."""
        escalation = Escalation.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-001',
            problem_description='Test problem',
            language='en'
        )
        
        serializer = EscalationListSerializer(instance=escalation)
        data = serializer.data
        
        # Check essential fields are present
        self.assertIn('id', data)
        self.assertIn('customer_name', data)
        self.assertIn('equipment_id', data)
        self.assertIn('status', data)
        self.assertIn('priority', data)
        self.assertIn('language', data)
        self.assertIn('created_at', data)


class EscalationDetailSerializerTest(TestCase):
    """Test cases for EscalationDetailSerializer."""

    def test_escalation_detail_serializer_includes_all_fields(self):
        """Test detail serializer includes all fields."""
        escalation = Escalation.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-001',
            problem_description='Test problem',
            conversation_transcript='Transcript here',
            internal_notes='Internal notes',
            language='en',
            status=Escalation.Status.PENDING,
            priority=Escalation.Priority.HIGH
        )
        
        serializer = EscalationDetailSerializer(instance=escalation)
        data = serializer.data
        
        # Check all fields are present
        self.assertIn('id', data)
        self.assertIn('customer_name', data)
        self.assertIn('customer_email', data)
        self.assertIn('equipment_id', data)
        self.assertIn('problem_description', data)
        self.assertIn('conversation_transcript', data)
        self.assertIn('internal_notes', data)
        self.assertIn('language', data)
        self.assertIn('status', data)
        self.assertIn('priority', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('resolved_at', data)


class EscalationUpdateSerializerTest(TestCase):
    """Test cases for EscalationUpdateSerializer."""

    def test_escalation_update_serializer_validates_status_choices(self):
        """Test update serializer validates status choices."""
        escalation = Escalation.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-001',
            problem_description='Test problem',
            language='en'
        )
        
        # Valid status
        data = {'status': 'in_progress'}
        serializer = EscalationUpdateSerializer(instance=escalation, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        # Invalid status
        data = {'status': 'invalid_status'}
        serializer = EscalationUpdateSerializer(instance=escalation, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)

    def test_required_fields_validation(self):
        """Test required fields validation."""
        # All fields should be optional for update
        data = {}
        serializer = EscalationUpdateSerializer(data=data, partial=True)
        # Should be valid even with empty data for partial update
        self.assertTrue(serializer.is_valid())

    def test_update_serializer_only_includes_updateable_fields(self):
        """Test update serializer only includes fields that can be updated."""
        escalation = Escalation.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-001',
            problem_description='Test problem',
            language='en'
        )
        
        serializer = EscalationUpdateSerializer(instance=escalation)
        fields = serializer.fields.keys()
        
        # Should include updateable fields
        self.assertIn('status', fields)
        self.assertIn('priority', fields)
        self.assertIn('internal_notes', fields)

