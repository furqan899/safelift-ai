"""
Tests for Conversation views.

Following Clean Code principles: comprehensive coverage, edge cases.
Tests all view methods, authentication, permissions, and error handling.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.conversations.models import ConversationHistory, ConversationLogs
from apps.conversations.constants import (
    PARAM_LANGUAGE,
    PARAM_STATUS,
    PARAM_SESSION_ID,
    PARAM_SEARCH,
    ERROR_STATS_RETRIEVAL_FAILED,
    ERROR_CONVERSATIONS_RETRIEVAL_FAILED,
    ERROR_ESCALATION_FAILED,
    ERROR_RESOLUTION_FAILED
)

User = get_user_model()


class ConversationHistoryViewSetTest(APITestCase):
    """Test cases for ConversationHistoryViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role=User.Role.USER
        )

        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            role=User.Role.ADMIN
        )

        self.other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )

        # Create conversations
        self.conversations = []
        for i in range(10):
            user = self.user if i < 8 else self.other_user
            conv = ConversationHistory.objects.create(
                session_id=f'history_session_{i}',
                user=user,
                user_query=f'History query {i}',
                ai_response=f'History response {i}',
                status=ConversationHistory.Status.ACTIVE if i % 2 == 0 else ConversationHistory.Status.RESOLVED,
                language=ConversationHistory.Language.ENGLISH if i % 2 == 0 else ConversationHistory.Language.SWEDISH,
                response_time=1000 + (i * 100),
                is_escalated=(i == 9),
                escalation_reason='Test escalation' if i == 9 else ''
            )
            self.conversations.append(conv)

        # Set up authentication
        self.user_token = self.get_token_for_user(self.user)
        self.admin_token = self.get_token_for_user(self.admin_user)

    def get_token_for_user(self, user):
        """Get JWT token for user."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def authenticate_user(self, token):
        """Set authentication header."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_list_conversations_unauthenticated(self):
        """Test list conversations without authentication."""
        response = self.client.get('/api/conversations/history/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_conversations_authenticated(self):
        """Test list conversations with authentication."""
        self.authenticate_user(self.user_token)
        response = self.client.get('/api/conversations/history/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 8)  # User should only see their conversations

    def test_list_conversations_admin(self):
        """Test list conversations as admin."""
        self.authenticate_user(self.admin_token)
        response = self.client.get('/api/conversations/history/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Admin should see all conversations

    def test_list_conversations_with_pagination(self):
        """Test pagination functionality."""
        self.authenticate_user(self.user_token)

        # Test default page size
        response = self.client.get('/api/conversations/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)

    def test_list_conversations_filter_by_language(self):
        """Test filtering by language."""
        self.authenticate_user(self.user_token)

        # Filter by English
        response = self.client.get(f'/api/conversations/history/?{PARAM_LANGUAGE}={ConversationHistory.Language.ENGLISH}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should have half English conversations
        english_count = sum(1 for conv in self.conversations[:8] if conv.language == ConversationHistory.Language.ENGLISH)
        self.assertEqual(len(response.data['results']), english_count)

    def test_list_conversations_filter_by_status(self):
        """Test filtering by status."""
        self.authenticate_user(self.user_token)

        # Filter by active status
        response = self.client.get(f'/api/conversations/history/?{PARAM_STATUS}={ConversationHistory.Status.ACTIVE}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        active_count = sum(1 for conv in self.conversations[:8] if conv.status == ConversationHistory.Status.ACTIVE)
        self.assertEqual(len(response.data['results']), active_count)

    def test_list_conversations_filter_by_session(self):
        """Test filtering by session ID."""
        self.authenticate_user(self.user_token)

        response = self.client.get(f'/api/conversations/history/?{PARAM_SESSION_ID}=history_session_0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['session_id'], 'history_session_0')

    def test_list_conversations_text_search(self):
        """Test text search functionality."""
        self.authenticate_user(self.user_token)

        response = self.client.get('/api/conversations/history/?search=History query 0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['user_query'], 'History query 0')

    def test_list_conversations_multiple_filters(self):
        """Test multiple filters combined."""
        self.authenticate_user(self.user_token)

        response = self.client.get(
            f'/api/conversations/history/?{PARAM_LANGUAGE}={ConversationHistory.Language.ENGLISH}&{PARAM_STATUS}={ConversationHistory.Status.ACTIVE}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should only return English AND active conversations
        filtered_count = sum(
            1 for conv in self.conversations[:8]
            if conv.language == ConversationHistory.Language.ENGLISH and conv.status == ConversationHistory.Status.ACTIVE
        )
        self.assertEqual(len(response.data['results']), filtered_count)

    def test_get_single_conversation(self):
        """Test retrieving single conversation."""
        self.authenticate_user(self.user_token)
        conversation = self.conversations[0]

        response = self.client.get(f'/api/conversations/history/{conversation.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['session_id'], conversation.session_id)

    def test_get_nonexistent_conversation(self):
        """Test retrieving nonexistent conversation."""
        self.authenticate_user(self.user_token)

        response = self.client.get('/api/conversations/history/999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_other_user_conversation(self):
        """Test accessing other user's conversation."""
        self.authenticate_user(self.user_token)

        # Try to access other user's conversation
        other_conversation = self.conversations[8]  # Belongs to other_user
        response = self.client.get(f'/api/conversations/history/{other_conversation.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_conversation(self):
        """Test creating new conversation."""
        self.authenticate_user(self.user_token)

        data = {
            'session_id': 'new_session',
            'user_query': 'New query',
            'ai_response': 'New response',
            'status': ConversationHistory.Status.ACTIVE,
            'language': ConversationHistory.Language.ENGLISH,
            'response_time': 1500
        }

        response = self.client.post('/api/conversations/history/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['session_id'], 'new_session')
        self.assertEqual(response.data['user_query'], 'New query')

    def test_create_conversation_invalid_data(self):
        """Test creating conversation with invalid data."""
        self.authenticate_user(self.user_token)

        # Missing required fields
        data = {
            'session_id': 'invalid_session'
            # Missing user_query and ai_response
        }

        response = self.client.post('/api/conversations/history/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_conversation(self):
        """Test updating conversation."""
        self.authenticate_user(self.user_token)
        conversation = self.conversations[0]

        data = {
            'user_query': 'Updated query',
            'status': ConversationHistory.Status.RESOLVED
        }

        response = self.client.patch(f'/api/conversations/history/{conversation.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_query'], 'Updated query')
        self.assertEqual(response.data['status'], ConversationHistory.Status.RESOLVED)

    def test_delete_conversation(self):
        """Test deleting conversation."""
        self.authenticate_user(self.user_token)
        conversation = self.conversations[0]

        response = self.client.delete(f'/api/conversations/history/{conversation.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify deletion
        response = self.client.get(f'/api/conversations/history/{conversation.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_stats_endpoint(self):
        """Test statistics endpoint."""
        self.authenticate_user(self.user_token)

        response = self.client.get('/api/conversations/history/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response structure
        expected_fields = ['total_conversations', 'resolved_conversations', 'escalated_conversations', 'success_rate']
        for field in expected_fields:
            self.assertIn(field, response.data)

        # Check calculations
        self.assertEqual(response.data['total_conversations'], 8)  # User's conversations
        self.assertEqual(response.data['escalated_conversations'], 0)  # User's conversations don't include escalated one

    def test_stats_endpoint_with_filters(self):
        """Test statistics with filters applied."""
        self.authenticate_user(self.user_token)

        # Get stats for specific language
        response = self.client.get(f'/api/conversations/history/stats/?{PARAM_LANGUAGE}={ConversationHistory.Language.ENGLISH}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should calculate stats only for English conversations
        english_conversations = [conv for conv in self.conversations[:8] if conv.language == ConversationHistory.Language.ENGLISH]
        expected_total = len(english_conversations)
        self.assertEqual(response.data['total_conversations'], expected_total)

    def test_escalate_conversation(self):
        """Test escalating conversation."""
        self.authenticate_user(self.user_token)
        conversation = self.conversations[0]

        data = {'reason': 'Test escalation reason'}
        response = self.client.post(f'/api/conversations/history/{conversation.id}/escalate/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['escalation_reason'], 'Test escalation reason')
        self.assertTrue(response.data['is_escalated'])

        # Verify in database
        conversation.refresh_from_db()
        self.assertTrue(conversation.is_escalated)
        self.assertEqual(conversation.escalation_reason, 'Test escalation reason')

    def test_escalate_conversation_no_reason(self):
        """Test escalating conversation without reason."""
        self.authenticate_user(self.user_token)
        conversation = self.conversations[0]

        response = self.client.post(f'/api/conversations/history/{conversation.id}/escalate/', {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['escalation_reason'], '')
        self.assertTrue(response.data['is_escalated'])

    def test_escalate_nonexistent_conversation(self):
        """Test escalating nonexistent conversation."""
        self.authenticate_user(self.user_token)

        response = self.client.post('/api/conversations/history/999/escalate/', {'reason': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_resolve_conversation(self):
        """Test resolving conversation."""
        self.authenticate_user(self.user_token)
        conversation = self.conversations[0]

        response = self.client.post(f'/api/conversations/history/{conversation.id}/resolve/', {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], ConversationHistory.Status.RESOLVED)
        self.assertIsNotNone(response.data['resolved_at'])

        # Verify in database
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, ConversationHistory.Status.RESOLVED)
        self.assertIsNotNone(conversation.resolved_at)

    def test_resolve_nonexistent_conversation(self):
        """Test resolving nonexistent conversation."""
        self.authenticate_user(self.user_token)

        response = self.client.post('/api/conversations/history/999/resolve/', {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_serializer_selection(self):
        """Test that correct serializer is used for different actions."""
        self.authenticate_user(self.user_token)

        # List should use ConversationHistoryListSerializer
        response = self.client.get('/api/conversations/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that list serializer fields are present (not full serializer fields)
        result = response.data['results'][0]
        list_only_fields = ['user_query', 'ai_response', 'status_display', 'language_display', 'response_time_seconds', 'is_escalated']
        full_only_fields = ['user', 'response_time', 'escalated_at', 'escalation_reason', 'updated_at', 'resolved_at']

        for field in list_only_fields:
            self.assertIn(field, result)

        for field in full_only_fields:
            self.assertNotIn(field, result)

        # Detail should use ConversationHistorySerializer
        conversation = self.conversations[0]
        response = self.client.get(f'/api/conversations/history/{conversation.id}/')

        result = response.data
        for field in list_only_fields + full_only_fields:
            self.assertIn(field, result)


class ConversationLogsViewSetTest(APITestCase):
    """Test cases for ConversationLogsViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            role=User.Role.ADMIN
        )

        # Create session logs
        for i in range(5):
            ConversationLogs.objects.create(
                session_id=f'logs_session_{i}',
                total_conversations=10 + i,
                resolved_conversations=7 + i,
                escalated_conversations=i,
                success_rate=round(((7 + i) / (10 + i)) * 100, 2),
                created_at=timezone.now(),
                updated_at=timezone.now(),
                last_conversation_at=timezone.now()
            )

        self.user_token = self.get_token_for_user(self.user)
        self.admin_token = self.get_token_for_user(self.admin_user)

    def get_token_for_user(self, user):
        """Get JWT token for user."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def authenticate_user(self, token):
        """Set authentication header."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_list_logs_unauthenticated(self):
        """Test list logs without authentication."""
        response = self.client.get('/api/conversations/logs/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_logs_authenticated(self):
        """Test list logs with authentication."""
        self.authenticate_user(self.user_token)
        response = self.client.get('/api/conversations/logs/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

    def test_logs_response_structure(self):
        """Test logs response structure."""
        self.authenticate_user(self.user_token)
        response = self.client.get('/api/conversations/logs/')

        result = response.data['results'][0]
        expected_fields = [
            'id', 'session_id', 'total_conversations', 'resolved_conversations',
            'escalated_conversations', 'success_rate', 'created_at',
            'created_at_formatted', 'updated_at', 'last_conversation_at',
            'last_conversation_at_formatted'
        ]

        for field in expected_fields:
            self.assertIn(field, result)

    def test_logs_pagination(self):
        """Test logs pagination."""
        self.authenticate_user(self.user_token)
        response = self.client.get('/api/conversations/logs/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
