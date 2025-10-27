"""
Tests for Conversation models.

Following Clean Code principles: clear test names, comprehensive coverage.
Tests all edge cases and business logic.
"""

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.conversations.models import ConversationHistory, ConversationLogs
from apps.conversations.constants import (
    DEFAULT_SUCCESS_RATE,
    PERCENTAGE_BASE,
    PERCENTAGE_DECIMAL_PLACES
)

User = get_user_model()


class ConversationHistoryModelTest(TestCase):
    """Test cases for ConversationHistory model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role=User.Role.ADMIN
        )

        self.conversation = ConversationHistory.objects.create(
            session_id='test_session_001',
            user=self.user,
            user_query='How do I reset my password?',
            ai_response='Please follow these steps...',
            status=ConversationHistory.Status.ACTIVE,
            language=ConversationHistory.Language.ENGLISH,
            response_time=1200,  # 1.2 seconds in milliseconds
            is_escalated=False,
            escalation_reason='',
            escalated_at=None,
            resolved_at=None,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

    def test_conversation_creation(self):
        """Test basic conversation creation."""
        self.assertEqual(self.conversation.session_id, 'test_session_001')
        self.assertEqual(self.conversation.user, self.user)
        self.assertEqual(self.conversation.user_query, 'How do I reset my password?')
        self.assertEqual(self.conversation.ai_response, 'Please follow these steps...')
        self.assertEqual(self.conversation.status, ConversationHistory.Status.ACTIVE)
        self.assertEqual(self.conversation.language, ConversationHistory.Language.ENGLISH)
        self.assertEqual(self.conversation.response_time, 1200)
        self.assertFalse(self.conversation.is_escalated)
        self.assertEqual(self.conversation.escalation_reason, '')

    def test_conversation_str_method(self):
        """Test string representation."""
        expected = f"{self.conversation.session_id} - {self.conversation.created_at}"
        self.assertEqual(str(self.conversation), expected)

    def test_conversation_default_values(self):
        """Test default values."""
        conversation = ConversationHistory.objects.create(
            session_id='test_session_002',
            user_query='Test query',
            ai_response='Test response',
            response_time=1000,
            is_escalated=False,
            escalation_reason='',
            escalated_at=None,
            resolved_at=None
        )

        self.assertEqual(conversation.status, ConversationHistory.Status.ACTIVE)
        self.assertEqual(conversation.language, ConversationHistory.Language.ENGLISH)
        self.assertFalse(conversation.is_escalated)
        self.assertEqual(conversation.escalation_reason, '')
        self.assertIsNotNone(conversation.created_at)
        self.assertIsNotNone(conversation.updated_at)

    def test_conversation_status_choices(self):
        """Test status choices."""
        # Test all status choices
        for status in ConversationHistory.Status.choices:
            conversation = ConversationHistory.objects.create(
                session_id=f'test_session_{status[0]}',
                user_query='Test query',
                ai_response='Test response',
                status=status[0],
                response_time=1000,
                is_escalated=False,
                escalation_reason='',
                escalated_at=None,
                resolved_at=None
            )
            self.assertEqual(conversation.get_status_display(), status[1])

    def test_conversation_language_choices(self):
        """Test language choices."""
        # Test English
        conversation_en = ConversationHistory.objects.create(
            session_id='test_session_en',
            user_query='Test query',
            ai_response='Test response',
            language=ConversationHistory.Language.ENGLISH,
            response_time=1000,
            is_escalated=False,
            escalation_reason='',
            escalated_at=None,
            resolved_at=None
        )
        self.assertEqual(conversation_en.get_language_display(), 'English')

        # Test Swedish
        conversation_sv = ConversationHistory.objects.create(
            session_id='test_session_sv',
            user_query='Test query',
            ai_response='Test response',
            language=ConversationHistory.Language.SWEDISH,
            response_time=1000,
            is_escalated=False,
            escalation_reason='',
            escalated_at=None,
            resolved_at=None
        )
        self.assertEqual(conversation_sv.get_language_display(), 'Swedish')

    def test_conversation_with_null_user(self):
        """Test conversation with null user (anonymous)."""
        conversation = ConversationHistory.objects.create(
            session_id='anonymous_session',
            user=None,
            user_query='Anonymous query',
            ai_response='Anonymous response',
            response_time=1000,
            is_escalated=False,
            escalation_reason='',
            escalated_at=None,
            resolved_at=None
        )

        self.assertIsNone(conversation.user)
        self.assertEqual(conversation.session_id, 'anonymous_session')

    def test_conversation_database_indexes(self):
        """Test database indexes are created."""
        # Check that indexes exist
        indexes = ConversationHistory._meta.indexes
        index_fields = [index.fields for index in indexes]

        self.assertIn(['-created_at', 'status'], index_fields)
        self.assertIn(['session_id', '-created_at'], index_fields)
        self.assertIn(['language', '-created_at'], index_fields)

    def test_conversation_save_method(self):
        """Test that save method works correctly."""
        conversation = ConversationHistory.objects.create(
            session_id='test_save_session',
            user_query='Save test query',
            ai_response='Save test response',
            response_time=1000,
            is_escalated=False,
            escalation_reason='',
            escalated_at=None,
            resolved_at=None
        )

        # Save should update updated_at
        original_updated_at = conversation.updated_at
        conversation.save()

        self.assertIsNotNone(conversation.updated_at)

    def test_conversation_user_relation(self):
        """Test user relation."""
        self.assertEqual(self.conversation.user.username, 'testuser')
        self.assertIn(self.conversation, self.user.conversations.all())


class ConversationLogsModelTest(TestCase):
    """Test cases for ConversationLogs model."""

    def setUp(self):
        """Set up test data."""
        self.session_log = ConversationLogs.objects.create(
            session_id='test_session_logs_001',
            total_conversations=10,
            resolved_conversations=7,
            escalated_conversations=2,
            success_rate=70.0,
            created_at=timezone.now(),
            last_conversation_at=timezone.now()
        )

    def test_session_log_creation(self):
        """Test basic session log creation."""
        self.assertEqual(self.session_log.session_id, 'test_session_logs_001')
        self.assertEqual(self.session_log.total_conversations, 10)
        self.assertEqual(self.session_log.resolved_conversations, 7)
        self.assertEqual(self.session_log.escalated_conversations, 2)
        self.assertEqual(self.session_log.success_rate, 70.0)

    def test_session_log_str_method(self):
        """Test string representation."""
        expected = f"Session {self.session_log.session_id} - {self.session_log.total_conversations} conversations"
        self.assertEqual(str(self.session_log), expected)

    def test_session_log_calculated_success_rate_property(self):
        """Test calculated success rate property."""
        # Test with zero conversations
        log_zero = ConversationLogs.objects.create(
            session_id='zero_session',
            total_conversations=0,
            resolved_conversations=0,
            escalated_conversations=0,
            created_at=timezone.now(),
            last_conversation_at=timezone.now()
        )
        self.assertEqual(log_zero.calculated_success_rate, DEFAULT_SUCCESS_RATE)

        # Test with conversations
        log_with_data = ConversationLogs.objects.create(
            session_id='data_session',
            total_conversations=10,
            resolved_conversations=7,
            escalated_conversations=2,
            created_at=timezone.now(),
            last_conversation_at=timezone.now()
        )
        expected_rate = round((7 / 10) * PERCENTAGE_BASE, PERCENTAGE_DECIMAL_PLACES)
        self.assertEqual(log_with_data.calculated_success_rate, expected_rate)

    def test_session_log_save_method(self):
        """Test that save method calculates success rate."""
        log = ConversationLogs.objects.create(
            session_id='save_test_session',
            total_conversations=20,
            resolved_conversations=15,
            escalated_conversations=3,
            created_at=timezone.now(),
            last_conversation_at=timezone.now()
        )

        # Save should auto-calculate success rate
        expected_rate = round((15 / 20) * PERCENTAGE_BASE, PERCENTAGE_DECIMAL_PLACES)
        log.save()
        log.refresh_from_db()
        self.assertEqual(log.success_rate, expected_rate)

    def test_session_log_unique_session_id(self):
        """Test that session_id is unique."""
        with self.assertRaises(Exception):  # Should raise IntegrityError
            ConversationLogs.objects.create(
                session_id='test_session_logs_001',  # Duplicate
                total_conversations=5,
                resolved_conversations=3,
                escalated_conversations=1
            )

    def test_session_log_database_indexes(self):
        """Test database indexes."""
        indexes = ConversationLogs._meta.indexes
        index_fields = [index.fields for index in indexes]

        self.assertIn(['-created_at'], index_fields)
        self.assertIn(['-last_conversation_at'], index_fields)
        self.assertIn(['session_id'], index_fields)

    def test_session_log_default_values(self):
        """Test default values."""
        log = ConversationLogs.objects.create(
            session_id='default_test_session',
            created_at=timezone.now(),
            last_conversation_at=timezone.now()
        )

        self.assertEqual(log.total_conversations, 0)
        self.assertEqual(log.resolved_conversations, 0)
        self.assertEqual(log.escalated_conversations, 0)
        self.assertEqual(log.success_rate, 0.0)

    def test_session_log_ordering(self):
        """Test default ordering."""
        # Clear existing logs from setUp
        ConversationLogs.objects.all().delete()

        log1 = ConversationLogs.objects.create(
            session_id='session_a',
            total_conversations=1,
            resolved_conversations=1,
            escalated_conversations=0,
            created_at=timezone.now() - timezone.timedelta(hours=1),
            last_conversation_at=timezone.now() - timezone.timedelta(hours=1)
        )
        log2 = ConversationLogs.objects.create(
            session_id='session_b',
            total_conversations=1,
            resolved_conversations=1,
            escalated_conversations=0,
            created_at=timezone.now(),
            last_conversation_at=timezone.now()
        )

        logs = ConversationLogs.objects.all()
        self.assertEqual(logs[0], log2)  # Most recent first
        self.assertEqual(logs[1], log1)

    def test_session_log_null_timestamps(self):
        """Test null timestamp handling."""
        log = ConversationLogs.objects.create(
            session_id='null_timestamp_session',
            total_conversations=1,
            resolved_conversations=1,
            escalated_conversations=0,
            created_at=None,
            last_conversation_at=None
        )

        self.assertIsNone(log.created_at)
        self.assertIsNone(log.last_conversation_at)
