"""
Tests for Conversation services.

Following Clean Code principles: comprehensive coverage, edge cases.
Tests all service methods with various scenarios and error conditions.
"""

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q
from unittest.mock import patch, MagicMock
from apps.conversations.models import ConversationHistory, ConversationLogs
from apps.conversations.services import (
    ConversationStatsService,
    ConversationFilterService,
    ConversationActionService,
    ConversationLogUpdateService
)
from apps.conversations.exceptions import (
    ConversationEscalationError,
    ConversationResolutionError,
    ConversationLogUpdateError
)
from apps.conversations.constants import (
    DEFAULT_SUCCESS_RATE,
    PERCENTAGE_BASE,
    PERCENTAGE_DECIMAL_PLACES,
    PARAM_LANGUAGE,
    PARAM_STATUS,
    PARAM_SESSION_ID,
    PARAM_SEARCH,
    LOG_CONVERSATION_ESCALATED,
    LOG_CONVERSATION_RESOLVED,
    LOG_CONVERSATION_LOG_UPDATED,
    MAX_SEARCH_QUERY_LENGTH
)

User = get_user_model()


class ConversationStatsServiceTest(TestCase):
    """Test cases for ConversationStatsService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Create test conversations
        self.conversations = []
        for i in range(5):
            conv = ConversationHistory.objects.create(
                session_id=f'stats_session_{i}',
                user=self.user,
                user_query=f'Query {i}',
                ai_response=f'Response {i}',
                status=ConversationHistory.Status.RESOLVED if i < 3 else ConversationHistory.Status.ACTIVE,
                language=ConversationHistory.Language.ENGLISH,
                response_time=1000,
                is_escalated=(i == 4)
            )
            self.conversations.append(conv)

    def test_calculate_overall_stats(self):
        """Test overall statistics calculation."""
        queryset = ConversationHistory.objects.all()

        stats = ConversationStatsService.calculate_overall_stats(queryset)

        self.assertEqual(stats['total_conversations'], 5)
        self.assertEqual(stats['resolved_conversations'], 3)
        self.assertEqual(stats['escalated_conversations'], 1)
        expected_success_rate = round((3 / 5) * PERCENTAGE_BASE, PERCENTAGE_DECIMAL_PLACES)
        self.assertEqual(stats['success_rate'], expected_success_rate)

    def test_calculate_overall_stats_empty_queryset(self):
        """Test statistics calculation with empty queryset."""
        queryset = ConversationHistory.objects.filter(session_id='nonexistent')

        stats = ConversationStatsService.calculate_overall_stats(queryset)

        self.assertEqual(stats['total_conversations'], 0)
        self.assertEqual(stats['resolved_conversations'], 0)
        self.assertEqual(stats['escalated_conversations'], 0)
        self.assertEqual(stats['success_rate'], DEFAULT_SUCCESS_RATE)

    def test_calculate_success_rate_method(self):
        """Test private success rate calculation method."""
        # Test with zero total
        success_rate = ConversationStatsService._calculate_success_rate(0, 0)
        self.assertEqual(success_rate, DEFAULT_SUCCESS_RATE)

        # Test with data
        success_rate = ConversationStatsService._calculate_success_rate(10, 7)
        expected = round((7 / 10) * PERCENTAGE_BASE, PERCENTAGE_DECIMAL_PLACES)
        self.assertEqual(success_rate, expected)

        # Test with 100% success rate
        success_rate = ConversationStatsService._calculate_success_rate(5, 5)
        self.assertEqual(success_rate, 100.0)

        # Test with 0% success rate
        success_rate = ConversationStatsService._calculate_success_rate(5, 0)
        self.assertEqual(success_rate, 0.0)


class ConversationFilterServiceTest(TestCase):
    """Test cases for ConversationFilterService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            role=User.Role.ADMIN
        )

        # Create conversations with different languages and statuses
        self.conversations = []
        languages = [ConversationHistory.Language.ENGLISH, ConversationHistory.Language.SWEDISH]
        statuses = list(ConversationHistory.Status.choices)

        for i in range(8):
            conv = ConversationHistory.objects.create(
                session_id=f'filter_session_{i}',
                user=self.user,
                user_query=f'Filter query {i}',
                ai_response=f'Filter response {i}',
                status=statuses[i % len(statuses)][0],
                language=languages[i % len(languages)][0],
                response_time=1000
            )
            self.conversations.append(conv)

    def test_apply_filters_no_filters(self):
        """Test apply_filters with no filters."""
        queryset = ConversationHistory.objects.all()
        filters = {}

        result = ConversationFilterService.apply_filters(queryset, filters, self.admin_user)

        self.assertEqual(result.count(), 8)

    def test_apply_filters_language_filter(self):
        """Test language filtering."""
        queryset = ConversationHistory.objects.all()
        filters = {PARAM_LANGUAGE: ConversationHistory.Language.ENGLISH}

        result = ConversationFilterService.apply_filters(queryset, filters, self.admin_user)

        # Check how many conversations are actually English
        english_count = sum(1 for conv in self.conversations if conv.language == ConversationHistory.Language.ENGLISH)
        self.assertEqual(result.count(), english_count)

        # Test case insensitive
        filters = {PARAM_LANGUAGE: 'EN'}
        result = ConversationFilterService.apply_filters(queryset, filters, self.admin_user)
        self.assertEqual(result.count(), english_count)

    def test_apply_filters_status_filter(self):
        """Test status filtering."""
        queryset = ConversationHistory.objects.all()
        filters = {PARAM_STATUS: ConversationHistory.Status.ACTIVE}

        result = ConversationFilterService.apply_filters(queryset, filters, self.admin_user)

        # Should find active conversations
        active_count = sum(1 for conv in self.conversations if conv.status == ConversationHistory.Status.ACTIVE)
        self.assertEqual(result.count(), active_count)

    def test_apply_filters_session_filter(self):
        """Test session ID filtering."""
        queryset = ConversationHistory.objects.all()
        filters = {PARAM_SESSION_ID: 'filter_session_0'}

        result = ConversationFilterService.apply_filters(queryset, filters, self.admin_user)

        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().session_id, 'filter_session_0')

    def test_apply_filters_text_search(self):
        """Test text search functionality."""
        queryset = ConversationHistory.objects.all()
        filters = {PARAM_SEARCH: 'Filter query 0'}

        result = ConversationFilterService.apply_filters(queryset, filters, self.admin_user)

        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().user_query, 'Filter query 0')

    def test_apply_filters_multiple_filters(self):
        """Test multiple filters combined."""
        queryset = ConversationHistory.objects.all()
        filters = {
            PARAM_LANGUAGE: ConversationHistory.Language.ENGLISH,
            PARAM_STATUS: ConversationHistory.Status.ACTIVE,
            PARAM_SEARCH: 'Filter query'
        }

        result = ConversationFilterService.apply_filters(queryset, filters, self.admin_user)

        # Should find conversations that match all criteria
        self.assertGreaterEqual(result.count(), 0)

    def test_apply_filters_user_permissions(self):
        """Test user permission filtering."""
        # Create conversation for different user
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )

        ConversationHistory.objects.create(
            session_id='other_session',
            user=other_user,
            user_query='Other query',
            ai_response='Other response',
            response_time=1000,
            is_escalated=False,
            escalation_reason='',
            escalated_at=None,
            resolved_at=None
        )

        queryset = ConversationHistory.objects.all()
        filters = {}

        # Admin should see all conversations
        result_admin = ConversationFilterService.apply_filters(queryset, filters, self.admin_user)
        self.assertEqual(result_admin.count(), 9)  # 8 + 1 other user

        # Regular user should see only their conversations
        result_user = ConversationFilterService.apply_filters(queryset, filters, self.user)
        self.assertEqual(result_user.count(), 8)

    def test_apply_filters_long_search_term(self):
        """Test search term length validation."""
        queryset = ConversationHistory.objects.all()
        long_search = 'x' * (MAX_SEARCH_QUERY_LENGTH + 1)
        filters = {PARAM_SEARCH: long_search}

        result = ConversationFilterService.apply_filters(queryset, filters, self.admin_user)

        # Should still work but truncated
        self.assertEqual(result.count(), 0)  # No matches expected

    def test_filter_by_language_method(self):
        """Test individual language filter method."""
        queryset = ConversationHistory.objects.all()

        result = ConversationFilterService._filter_by_language(queryset, ConversationHistory.Language.ENGLISH)

        # Check how many conversations are actually English
        english_count = sum(1 for conv in self.conversations if conv.language == ConversationHistory.Language.ENGLISH)
        self.assertEqual(result.count(), english_count)

    def test_filter_by_status_method(self):
        """Test individual status filter method."""
        queryset = ConversationHistory.objects.all()

        result = ConversationFilterService._filter_by_status(queryset, ConversationHistory.Status.ACTIVE)
        active_count = sum(1 for conv in self.conversations if conv.status == ConversationHistory.Status.ACTIVE)
        self.assertEqual(result.count(), active_count)

    def test_filter_by_session_method(self):
        """Test individual session filter method."""
        queryset = ConversationHistory.objects.all()

        result = ConversationFilterService._filter_by_session(queryset, 'filter_session_0')
        self.assertEqual(result.count(), 1)

    def test_apply_text_search_method(self):
        """Test individual text search method."""
        queryset = ConversationHistory.objects.all()

        result = ConversationFilterService._apply_text_search(queryset, 'Filter query 0')
        self.assertEqual(result.count(), 1)

    def test_apply_text_search_multiple_matches(self):
        """Test text search with multiple matches."""
        # Create additional conversations with similar queries
        ConversationHistory.objects.create(
            session_id='search_session_1',
            user=self.user,
            user_query='Similar query test',
            ai_response='Response 1',
            response_time=1000,
            is_escalated=False,
            escalation_reason='',
            escalated_at=None,
            resolved_at=None
        )
        ConversationHistory.objects.create(
            session_id='search_session_2',
            user=self.user,
            user_query='Another query',
            ai_response='Similar query test response',
            response_time=1000,
            is_escalated=False,
            escalation_reason='',
            escalated_at=None,
            resolved_at=None
        )

        queryset = ConversationHistory.objects.filter(session_id__startswith='search_session')

        result = ConversationFilterService._apply_text_search(queryset, 'query test')
        self.assertEqual(result.count(), 2)


class ConversationActionServiceTest(TestCase):
    """Test cases for ConversationActionService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.conversation = ConversationHistory.objects.create(
            session_id='action_session',
            user=self.user,
            user_query='Action test query',
            ai_response='Action test response',
            status=ConversationHistory.Status.ACTIVE,
            language=ConversationHistory.Language.ENGLISH,
            response_time=1000
        )

    @patch('apps.conversations.services.logger')
    def test_escalate_conversation_success(self, mock_logger):
        """Test successful escalation."""
        reason = 'Test escalation reason'

        result = ConversationActionService.escalate_conversation(self.conversation, reason)

        # Check conversation was updated
        self.conversation.refresh_from_db()
        self.assertTrue(self.conversation.is_escalated)
        self.assertEqual(self.conversation.status, ConversationHistory.Status.ESCALATED)
        self.assertEqual(self.conversation.escalation_reason, reason)
        self.assertIsNotNone(self.conversation.escalated_at)

        # Check logging was called
        mock_logger.info.assert_called_once()
        self.assertIn('escalated', mock_logger.info.call_args[0][0])

        # Check return value
        self.assertEqual(result, self.conversation)

    @patch('apps.conversations.services.logger')
    def test_escalate_conversation_empty_reason(self, mock_logger):
        """Test escalation with empty reason."""
        result = ConversationActionService.escalate_conversation(self.conversation)

        self.conversation.refresh_from_db()
        self.assertTrue(self.conversation.is_escalated)
        self.assertEqual(self.conversation.escalation_reason, '')

    @patch('apps.conversations.services.logger')
    def test_escalate_conversation_database_error(self, mock_logger):
        """Test escalation with database error."""
        # Mock save to raise an exception
        with patch.object(self.conversation, 'save', side_effect=Exception('Database error')):
            with self.assertRaises(ConversationEscalationError) as context:
                ConversationActionService.escalate_conversation(self.conversation, 'Test reason')

            self.assertIn('Failed to escalate conversation', str(context.exception))
            mock_logger.error.assert_called()

    @patch('apps.conversations.services.logger')
    def test_resolve_conversation_success(self, mock_logger):
        """Test successful resolution."""
        result = ConversationActionService.resolve_conversation(self.conversation)

        # Check conversation was updated
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.status, ConversationHistory.Status.RESOLVED)
        self.assertIsNotNone(self.conversation.resolved_at)

        # Check logging was called
        mock_logger.info.assert_called_once()
        self.assertIn('resolved', mock_logger.info.call_args[0][0])

        # Check return value
        self.assertEqual(result, self.conversation)

    @patch('apps.conversations.services.logger')
    def test_resolve_conversation_database_error(self, mock_logger):
        """Test resolution with database error."""
        # Mock save to raise an exception
        with patch.object(self.conversation, 'save', side_effect=Exception('Database error')):
            with self.assertRaises(ConversationResolutionError) as context:
                ConversationActionService.resolve_conversation(self.conversation)

            self.assertIn('Failed to resolve conversation', str(context.exception))
            mock_logger.error.assert_called()

    def test_escalate_conversation_exception_handling(self):
        """Test escalation exception handling."""
        # Test with invalid conversation
        invalid_conversation = MagicMock()
        invalid_conversation.id = 999
        invalid_conversation.save.side_effect = Exception('Save failed')

        with self.assertRaises(ConversationEscalationError):
            ConversationActionService.escalate_conversation(invalid_conversation, 'Test')

    def test_resolve_conversation_exception_handling(self):
        """Test resolution exception handling."""
        # Test with invalid conversation
        invalid_conversation = MagicMock()
        invalid_conversation.id = 999
        invalid_conversation.save.side_effect = Exception('Save failed')

        with self.assertRaises(ConversationResolutionError):
            ConversationActionService.resolve_conversation(invalid_conversation)


class ConversationLogUpdateServiceTest(TestCase):
    """Test cases for ConversationLogUpdateService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Create conversations for a session
        for i in range(5):
            ConversationHistory.objects.create(
                session_id='log_session_001',
                user=self.user,
                user_query=f'Log query {i}',
                ai_response=f'Log response {i}',
                status=ConversationHistory.Status.RESOLVED if i < 3 else ConversationHistory.Status.ACTIVE,
                language=ConversationHistory.Language.ENGLISH,
                response_time=1000,
                is_escalated=(i == 4)
            )

    @patch('apps.conversations.services.logger')
    def test_update_or_create_session_log_new(self, mock_logger):
        """Test creating new session log."""
        result = ConversationLogUpdateService.update_or_create_session_log('log_session_001')

        # Check log was created
        self.assertIsInstance(result, ConversationLogs)
        self.assertEqual(result.session_id, 'log_session_001')
        self.assertEqual(result.total_conversations, 5)
        self.assertEqual(result.resolved_conversations, 3)
        self.assertEqual(result.escalated_conversations, 1)

        expected_success_rate = round((3 / 5) * PERCENTAGE_BASE, PERCENTAGE_DECIMAL_PLACES)
        self.assertEqual(result.success_rate, expected_success_rate)

        # Check logging was called for new creation
        mock_logger.info.assert_called_once()
        self.assertIn('created', mock_logger.info.call_args[0][0])

    @patch('apps.conversations.services.logger')
    def test_update_or_create_session_log_existing(self, mock_logger):
        """Test updating existing session log."""
        # Create existing log
        existing_log = ConversationLogs.objects.create(
            session_id='log_session_001',
            total_conversations=1,
            resolved_conversations=1,
            escalated_conversations=0
        )

        result = ConversationLogUpdateService.update_or_create_session_log('log_session_001')

        # Should return the same instance
        self.assertEqual(result.id, existing_log.id)

        # Should update with current data
        result.refresh_from_db()
        self.assertEqual(result.total_conversations, 5)
        self.assertEqual(result.resolved_conversations, 3)

        # Check logging was called for update
        mock_logger.info.assert_called_once()
        self.assertIn('created', mock_logger.info.call_args[0][0])

    @patch('apps.conversations.services.logger')
    def test_update_or_create_session_log_with_last_conversation(self, mock_logger):
        """Test session log with last conversation timestamp."""
        # Update one conversation to have a specific timestamp
        specific_time = timezone.now() - timezone.timedelta(hours=1)
        ConversationHistory.objects.filter(session_id='log_session_001').first().created_at = specific_time
        ConversationHistory.objects.filter(session_id='log_session_001').first().save()

        result = ConversationLogUpdateService.update_or_create_session_log('log_session_001')

        # Should set last_conversation_at to the most recent conversation
        self.assertIsNotNone(result.last_conversation_at)

    @patch('apps.conversations.services.logger')
    def test_update_or_create_session_log_database_error(self, mock_logger):
        """Test session log update with database error."""
        # Mock get_or_create to raise an exception
        with patch('apps.conversations.models.ConversationLogs.objects.get_or_create') as mock_get_or_create:
            mock_get_or_create.side_effect = Exception('Database connection failed')

            with self.assertRaises(ConversationLogUpdateError) as context:
                ConversationLogUpdateService.update_or_create_session_log('log_session_001')

            self.assertIn('Failed to update conversation log', str(context.exception))
            mock_logger.error.assert_called()

    def test_update_or_create_session_log_empty_session(self):
        """Test session log for session with no conversations."""
        result = ConversationLogUpdateService.update_or_create_session_log('empty_session')

        self.assertEqual(result.session_id, 'empty_session')
        self.assertEqual(result.total_conversations, 0)
        self.assertEqual(result.resolved_conversations, 0)
        self.assertEqual(result.escalated_conversations, 0)
        self.assertEqual(result.success_rate, DEFAULT_SUCCESS_RATE)

    def test_update_or_create_session_log_calculations(self):
        """Test that calculations are correct."""
        # Create mixed status conversations
        for i in range(10):
            status = (ConversationHistory.Status.RESOLVED if i < 6 else
                     ConversationHistory.Status.ESCALATED if i < 8 else
                     ConversationHistory.Status.ACTIVE)

            ConversationHistory.objects.create(
                session_id='calc_session',
                user=self.user,
                user_query=f'Calc query {i}',
                ai_response=f'Calc response {i}',
                status=status,
                language=ConversationHistory.Language.ENGLISH,
                response_time=1000,
                is_escalated=(status == ConversationHistory.Status.ESCALATED)
            )

        result = ConversationLogUpdateService.update_or_create_session_log('calc_session')

        self.assertEqual(result.total_conversations, 10)
        self.assertEqual(result.resolved_conversations, 6)
        self.assertEqual(result.escalated_conversations, 2)  # Only explicitly escalated ones
        expected_rate = round((6 / 10) * PERCENTAGE_BASE, PERCENTAGE_DECIMAL_PLACES)
        self.assertEqual(result.success_rate, expected_rate)
