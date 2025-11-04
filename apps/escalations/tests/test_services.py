"""
Tests for Escalation services.
"""
from django.test import TestCase
from apps.escalations.models import Escalation
from apps.escalations.services import EscalationService
from apps.conversations.models import ConversationHistory
from apps.users.models import User


class EscalationServiceTest(TestCase):
    """Test cases for EscalationService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        self.conversation = ConversationHistory.objects.create(
            session_id='test_session',
            user=self.user,
            user_query='Test query',
            ai_response='Test response',
            language='en',
            response_time=1000,
            escalation_reason='Test escalation reason'
        )

    def test_create_from_conversation(self):
        """Test creating escalation from conversation."""
        escalation = EscalationService.create_from_conversation(
            conversation=self.conversation,
            problem_description='Custom problem description',
            priority=Escalation.Priority.HIGH
        )
        
        self.assertEqual(escalation.conversation, self.conversation)
        self.assertEqual(escalation.language, 'en')
        self.assertEqual(escalation.status, Escalation.Status.PENDING)
        self.assertEqual(escalation.priority, Escalation.Priority.HIGH)
        self.assertEqual(escalation.problem_description, 'Custom problem description')

    def test_create_from_conversation_copies_correct_data(self):
        """Test escalation copies data from conversation."""
        escalation = EscalationService.create_from_conversation(
            conversation=self.conversation
        )
        
        self.assertEqual(escalation.conversation, self.conversation)
        self.assertEqual(escalation.language, self.conversation.language)
        # Problem description should default to escalation_reason
        self.assertEqual(escalation.problem_description, 'Test escalation reason')

    def test_create_from_conversation_uses_default_priority(self):
        """Test escalation uses default priority if not specified."""
        escalation = EscalationService.create_from_conversation(
            conversation=self.conversation
        )
        
        self.assertEqual(escalation.priority, Escalation.Priority.MEDIUM)

    def test_set_status_updates_escalation_status(self):
        """Test set_status updates escalation status."""
        escalation = Escalation.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-001',
            problem_description='Test problem',
            language='en',
            status=Escalation.Status.PENDING
        )
        
        updated_escalation = EscalationService.set_status(
            escalation=escalation,
            status=Escalation.Status.IN_PROGRESS
        )
        
        self.assertEqual(updated_escalation.status, Escalation.Status.IN_PROGRESS)

    def test_set_status_updates_internal_notes(self):
        """Test set_status updates internal notes."""
        escalation = Escalation.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-001',
            problem_description='Test problem',
            language='en'
        )
        
        updated_escalation = EscalationService.set_status(
            escalation=escalation,
            status=Escalation.Status.IN_PROGRESS,
            internal_notes='Working on this issue'
        )
        
        self.assertEqual(updated_escalation.internal_notes, 'Working on this issue')

    def test_set_status_syncs_conversation_status_to_resolved(self):
        """Test conversation status syncs when escalation resolved."""
        escalation = Escalation.objects.create(
            conversation=self.conversation,
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-001',
            problem_description='Test problem',
            language='en',
            status=Escalation.Status.PENDING
        )
        
        EscalationService.set_status(
            escalation=escalation,
            status=Escalation.Status.RESOLVED
        )
        
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.status, ConversationHistory.Status.RESOLVED)
        self.assertIsNotNone(self.conversation.resolved_at)

    def test_set_status_syncs_conversation_status_to_escalated(self):
        """Test conversation status syncs to escalated for non-resolved states."""
        escalation = Escalation.objects.create(
            conversation=self.conversation,
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-001',
            problem_description='Test problem',
            language='en',
            status=Escalation.Status.PENDING
        )
        
        EscalationService.set_status(
            escalation=escalation,
            status=Escalation.Status.IN_PROGRESS
        )
        
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.status, ConversationHistory.Status.ESCALATED)

    def test_get_summary_counts_returns_correct_counts(self):
        """Test get_summary_counts returns correct escalation counts."""
        # Create escalations with different statuses
        Escalation.objects.create(
            customer_name='User 1',
            customer_email='user1@example.com',
            equipment_id='SL-001',
            problem_description='Problem 1',
            language='en',
            status=Escalation.Status.PENDING
        )
        Escalation.objects.create(
            customer_name='User 2',
            customer_email='user2@example.com',
            equipment_id='SL-002',
            problem_description='Problem 2',
            language='en',
            status=Escalation.Status.PENDING
        )
        Escalation.objects.create(
            customer_name='User 3',
            customer_email='user3@example.com',
            equipment_id='SL-003',
            problem_description='Problem 3',
            language='en',
            status=Escalation.Status.IN_PROGRESS
        )
        Escalation.objects.create(
            customer_name='User 4',
            customer_email='user4@example.com',
            equipment_id='SL-004',
            problem_description='Problem 4',
            language='en',
            status=Escalation.Status.RESOLVED
        )
        
        counts = EscalationService.get_summary_counts()
        
        self.assertEqual(counts['total'], 4)
        self.assertEqual(counts['pending'], 2)
        self.assertEqual(counts['in_progress'], 1)
        self.assertEqual(counts['resolved'], 1)

    def test_escalation_without_linked_conversation(self):
        """Test escalation can work without linked conversation."""
        escalation = Escalation.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            equipment_id='SL-001',
            problem_description='Test problem',
            language='en'
        )
        
        # Should not raise error when no conversation linked
        EscalationService.set_status(
            escalation=escalation,
            status=Escalation.Status.RESOLVED
        )
        
        self.assertEqual(escalation.status, Escalation.Status.RESOLVED)

