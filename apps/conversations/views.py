"""
Views for Conversation History and Logs.

Following Clean Code principles: single responsibility, clear error handling.
Business logic is delegated to services layer.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from drf_spectacular.utils import extend_schema

from .models import ConversationHistory, ConversationLogs
from .serializers import (
    ConversationHistorySerializer,
    ConversationHistoryListSerializer,
    ConversationLogsSerializer,
    ConversationStatsSerializer
)
from .services import (
    ConversationStatsService,
    ConversationFilterService,
    ConversationActionService,
)
from .constants import (
    PARAM_LANGUAGE,
    PARAM_STATUS,
    PARAM_SESSION_ID,
    PARAM_SEARCH,
)
from .exceptions import (
    ConversationEscalationError,
    ConversationResolutionError,
)

logger = logging.getLogger(__name__)

@extend_schema(tags=["Conversations"])
class ConversationHistoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversation history.
    
    Provides CRUD operations and filtering for individual conversation entries.
    """
    
    queryset = ConversationHistory.objects.select_related('user').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ConversationHistoryListSerializer
        return ConversationHistorySerializer
    
    def get_queryset(self):
        """
        Get filtered queryset using conversation filter service.
        
        Supports filtering by:
        - language: en, sv
        - status: active, resolved, escalated, pending
        - session_id: specific session
        - search: text search in user_query and ai_response
        """
        queryset = ConversationHistory.objects.select_related('user').all()
        
        # Extract filter parameters
        filters = {
            PARAM_LANGUAGE: self.request.query_params.get('language'),
            PARAM_STATUS: self.request.query_params.get('status'),
            PARAM_SESSION_ID: self.request.query_params.get('session_id'),
            PARAM_SEARCH: self.request.query_params.get('search'),
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Apply filters using service
        return ConversationFilterService.apply_filters(
            queryset,
            filters,
            self.request.user
        )
    
    @extend_schema(
        summary="List Conversation History",
        description="Get all conversation history with optional filtering",
        tags=["Conversations"]
    )
    def list(self, request, *args, **kwargs):
        """List conversations with filtering support."""
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error listing conversations: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve conversations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get Conversation Stats",
        description="Get overall conversation statistics for the dashboard",
        responses={200: ConversationStatsSerializer},
        tags=["Conversations"]
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get overall conversation statistics.
        
        Returns summary metrics for the conversation logs dashboard:
        - Total conversations
        - Resolved conversations
        - Escalated conversations  
        - Success rate
        """
        try:
            # Get filtered queryset
            queryset = self.get_queryset()
            
            # Calculate statistics using service
            stats = ConversationStatsService.calculate_overall_stats(queryset)
            
            serializer = ConversationStatsSerializer(stats)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(
                f"Error calculating conversation stats: {str(e)}",
                exc_info=True
            )
            return Response(
                {'error': 'Failed to retrieve statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Escalate Conversation",
        description="Mark a conversation as escalated with optional reason",
        tags=["Conversations"]
    )
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def escalate(self, request, pk=None):
        """Mark conversation as escalated."""
        conversation = self.get_object()
        reason = request.data.get('reason', '')
        
        try:
            # Use service to escalate
            updated_conversation = ConversationActionService.escalate_conversation(
                conversation,
                reason
            )
            serializer = self.get_serializer(updated_conversation)
            return Response(serializer.data)
        except ConversationEscalationError as e:
            logger.error(
                f"Error escalating conversation {pk}: {str(e)}",
                exc_info=True
            )
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(
                f"Unexpected error escalating conversation {pk}: {str(e)}",
                exc_info=True
            )
            return Response(
                {'error': 'Failed to escalate conversation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Resolve Conversation",
        description="Mark a conversation as resolved",
        tags=["Conversations"]
    )
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def resolve(self, request, pk=None):
        """Mark conversation as resolved."""
        conversation = self.get_object()
        
        try:
            # Use service to resolve
            updated_conversation = ConversationActionService.resolve_conversation(
                conversation
            )
            serializer = self.get_serializer(updated_conversation)
            return Response(serializer.data)
        except ConversationResolutionError as e:
            logger.error(
                f"Error resolving conversation {pk}: {str(e)}",
                exc_info=True
            )
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(
                f"Unexpected error resolving conversation {pk}: {str(e)}",
                exc_info=True
            )
            return Response(
                {'error': 'Failed to resolve conversation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@extend_schema(tags=["Conversations"])
class ConversationLogsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing conversation logs (session-level metrics).
    
    Read-only view of aggregated session statistics.
    """
    
    queryset = ConversationLogs.objects.all()
    serializer_class = ConversationLogsSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="List Conversation Logs",
        description="Get all conversation logs (session-level metrics)",
        tags=["Conversations"]
    )
    def list(self, request, *args, **kwargs):
        """List conversation logs."""
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error listing conversation logs: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve conversation logs'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
