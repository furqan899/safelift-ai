"""
Tests for Escalation model.
"""
from django.test import TestCase
from django.utils import timezone
from apps.escalations.models import Escalation
from apps.conversations.models import ConversationHistory
from apps.users.models import User


class EscalationModelTest(TestCase):
    """Test cases for Escalation model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )
        self.conversation = ConversationHistory.objects.create(
            session_id='test_session',
            user=self.user,
            user_query='Test query',
            ai_response='Test response',
            language='en',
            response_time=1000
        )

    def test_escalation_creation(self):
        """Test creating an escalation."""
        escalation = Escalation.objects.create(
            conversation=self.conversation,
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-123',
            problem_description='Test problem',
            language='en'
        )
        
        self.assertEqual(escalation.customer_name, 'John Doe')
        self.assertEqual(escalation.customer_email, 'john@example.com')
        self.assertEqual(escalation.equipment_id, 'SL-123')
        self.assertEqual(escalation.status, Escalation.Status.PENDING)
        self.assertEqual(escalation.priority, Escalation.Priority.MEDIUM)

    def test_escalation_status_choices(self):
        """Test status choices are correct."""
        choices = Escalation.Status.choices
        
        self.assertEqual(len(choices), 3)
        self.assertIn(('pending', 'Pending'), choices)
        self.assertIn(('in_progress', 'In Progress'), choices)
        self.assertIn(('resolved', 'Resolved'), choices)

    def test_escalation_priority_choices(self):
        """Test priority choices are correct."""
        choices = Escalation.Priority.choices
        
        self.assertEqual(len(choices), 3)
        self.assertIn(('low', 'Low'), choices)
        self.assertIn(('medium', 'Medium'), choices)
        self.assertIn(('high', 'High'), choices)

    def test_resolved_at_auto_set_on_status_change(self):
        """Test resolved_at is automatically set when status changes to resolved."""
        escalation = Escalation.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-123',
            problem_description='Test problem',
            language='en',
            status=Escalation.Status.PENDING
        )
        
        self.assertIsNone(escalation.resolved_at)
        
        # Change status to resolved
        escalation.status = Escalation.Status.RESOLVED
        escalation.save()
        
        self.assertIsNotNone(escalation.resolved_at)

    def test_resolved_at_cleared_when_moved_from_resolved(self):
        """Test resolved_at is cleared when status changes from resolved."""
        escalation = Escalation.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-123',
            problem_description='Test problem',
            language='en',
            status=Escalation.Status.RESOLVED
        )
        
        # Initially has resolved_at
        self.assertIsNotNone(escalation.resolved_at)
        
        # Change status back to pending
        escalation.status = Escalation.Status.PENDING
        escalation.save()
        
        self.assertIsNone(escalation.resolved_at)

    def test_escalation_conversation_relationship(self):
        """Test relationship with ConversationHistory."""
        escalation = Escalation.objects.create(
            conversation=self.conversation,
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-123',
            problem_description='Test problem',
            language='en'
        )
        
        self.assertEqual(escalation.conversation, self.conversation)
        self.assertIn(escalation, self.conversation.escalations.all())

    def test_escalation_language_field_mirrors_conversation(self):
        """Test language field uses same choices as ConversationHistory."""
        # Create escalation with Swedish language
        escalation = Escalation.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-123',
            problem_description='Test problem',
            language='sv'
        )
        
        self.assertEqual(escalation.language, 'sv')
        # Should be same choices as ConversationHistory.Language
        self.assertEqual(
            escalation._meta.get_field('language').choices,
            ConversationHistory.Language.choices
        )

    def test_string_representation(self):
        """Test __str__ method."""
        escalation = Escalation.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-123',
            problem_description='Test problem',
            language='en',
            status=Escalation.Status.PENDING
        )
        
        expected = f"Escalation #{escalation.pk} - pending"
        self.assertEqual(str(escalation), expected)

    def test_escalation_without_conversation(self):
        """Test escalation can be created without linked conversation."""
        escalation = Escalation.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-123',
            problem_description='Test problem',
            language='en'
        )
        
        self.assertIsNone(escalation.conversation)

    def test_default_values(self):
        """Test default values are set correctly."""
        escalation = Escalation.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-123',
            problem_description='Test problem',
            language='en'
        )
        
        self.assertEqual(escalation.status, Escalation.Status.PENDING)
        self.assertEqual(escalation.priority, Escalation.Priority.MEDIUM)
        self.assertEqual(escalation.conversation_transcript, '')
        self.assertEqual(escalation.internal_notes, '')
        self.assertFalse(escalation.resolved_at)

    def test_escalation_ordering(self):
        """Test default ordering is by created_at descending."""
        # Create multiple escalations
        escalation1 = Escalation.objects.create(
            customer_name='User 1',
            customer_email='user1@example.com',
            equipment_id='SL-001',
            problem_description='Problem 1',
            language='en'
        )
        escalation2 = Escalation.objects.create(
            customer_name='User 2',
            customer_email='user2@example.com',
            equipment_id='SL-002',
            problem_description='Problem 2',
            language='en'
        )
        
        escalations = list(Escalation.objects.all())
        
        # Most recent should be first
        self.assertEqual(escalations[0].pk, escalation2.pk)
        self.assertEqual(escalations[1].pk, escalation1.pk)

