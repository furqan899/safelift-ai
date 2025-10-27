"""
Conversation Services

Business logic layer for conversation operations.
Following Clean Code principles: Single Responsibility, DRY, meaningful names.
"""

import logging
from typing import Dict, Any, Optional
from django.db.models import Q, QuerySet
from django.utils import timezone

from .models import ConversationHistory, ConversationLogs
from .constants import (
    PERCENTAGE_BASE,
    DEFAULT_SUCCESS_RATE,
    PERCENTAGE_DECIMAL_PLACES,
    PARAM_LANGUAGE,
    PARAM_STATUS,
    PARAM_SESSION_ID,
    PARAM_SEARCH,
    LOG_CONVERSATION_ESCALATED,
    LOG_CONVERSATION_RESOLVED,
    LOG_CONVERSATION_LOG_UPDATED,
    MAX_SEARCH_QUERY_LENGTH,
)
from .exceptions import (
    ConversationNotFoundError,
    SessionNotFoundError,
    ConversationEscalationError,
    ConversationResolutionError,
    ConversationStatsError,
    ConversationLogUpdateError,
)

logger = logging.getLogger(__name__)


class ConversationStatsService:
    """
    Service for calculating conversation statistics.
    
    Separates business logic from views following clean architecture.
    """
    
    @staticmethod
    def calculate_overall_stats(queryset: QuerySet) -> Dict[str, Any]:
        """
        Calculate overall conversation statistics.
        
        Args:
            queryset: Filtered conversation queryset
            
        Returns:
            Dictionary containing total, resolved, escalated counts and success rate
        """
        total_conversations = queryset.count()
        resolved_conversations = queryset.filter(
            status=ConversationHistory.Status.RESOLVED
        ).count()
        escalated_conversations = queryset.filter(
            is_escalated=True
        ).count()
        
        success_rate = ConversationStatsService._calculate_success_rate(
            total_conversations,
            resolved_conversations
        )
        
        return {
            'total_conversations': total_conversations,
            'resolved_conversations': resolved_conversations,
            'escalated_conversations': escalated_conversations,
            'success_rate': success_rate,
        }
    
    @staticmethod
    def _calculate_success_rate(total: int, resolved: int) -> float:
        """
        Calculate success rate as percentage of resolved conversations.
        
        Args:
            total: Total number of conversations
            resolved: Number of resolved conversations
            
        Returns:
            Success rate as float (0-100)
        """
        if total == 0:
            return DEFAULT_SUCCESS_RATE
        
        percentage = (resolved / total) * PERCENTAGE_BASE
        return round(percentage, PERCENTAGE_DECIMAL_PLACES)


class ConversationFilterService:
    """
    Service for filtering conversation querysets.
    
    Centralizes all filtering logic for conversations.
    """
    
    @staticmethod
    def apply_filters(
        queryset: QuerySet,
        filters: Dict[str, Any],
        user
    ) -> QuerySet:
        """
        Apply all filters to conversation queryset.
        
        Args:
            queryset: Base conversation queryset
            filters: Dictionary of filter parameters
            user: Current user for permission-based filtering
            
        Returns:
            Filtered queryset
        """
        # Language filter
        language = filters.get(PARAM_LANGUAGE)
        if language:
            queryset = ConversationFilterService._filter_by_language(
                queryset,
                language
            )
        
        # Status filter
        status = filters.get(PARAM_STATUS)
        if status:
            queryset = ConversationFilterService._filter_by_status(
                queryset,
                status
            )
        
        # Session filter
        session_id = filters.get(PARAM_SESSION_ID)
        if session_id:
            queryset = ConversationFilterService._filter_by_session(
                queryset,
                session_id
            )
        
        # Text search
        search = filters.get(PARAM_SEARCH)
        if search:
            queryset = ConversationFilterService._apply_text_search(
                queryset,
                search
            )
        
        # Permission-based filtering
        if not user.is_admin:
            queryset = queryset.filter(user=user)
        
        return queryset
    
    @staticmethod
    def _filter_by_language(queryset: QuerySet, language: str) -> QuerySet:
        """Filter conversations by language code."""
        return queryset.filter(language=language.lower())
    
    @staticmethod
    def _filter_by_status(queryset: QuerySet, status: str) -> QuerySet:
        """Filter conversations by status."""
        return queryset.filter(status=status.lower())
    
    @staticmethod
    def _filter_by_session(queryset: QuerySet, session_id: str) -> QuerySet:
        """Filter conversations by session ID."""
        return queryset.filter(session_id=session_id)
    
    @staticmethod
    def _apply_text_search(queryset: QuerySet, search_term: str) -> QuerySet:
        """
        Apply text search in user query and AI response fields.
        
        Args:
            queryset: QuerySet to filter
            search_term: Search term (validated for length in views)
            
        Returns:
            Filtered queryset
        """
        # Validate search term length
        if len(search_term) > MAX_SEARCH_QUERY_LENGTH:
            search_term = search_term[:MAX_SEARCH_QUERY_LENGTH]
        
        return queryset.filter(
            Q(user_query__icontains=search_term) |
            Q(ai_response__icontains=search_term)
        )


class ConversationActionService:
    """
    Service for conversation actions (escalate, resolve).
    
    Handles business logic for conversation state changes.
    """
    
    @staticmethod
    def escalate_conversation(
        conversation: ConversationHistory,
        reason: str = ''
    ) -> ConversationHistory:
        """
        Escalate a conversation with optional reason.
        
        Args:
            conversation: Conversation to escalate
            reason: Optional escalation reason
            
        Returns:
            Updated conversation instance
            
        Raises:
            ConversationEscalationError: If escalation fails
        """
        try:
            conversation.is_escalated = True
            conversation.status = ConversationHistory.Status.ESCALATED
            conversation.escalated_at = timezone.now()
            conversation.escalation_reason = reason
            conversation.save()
            
            logger.info(LOG_CONVERSATION_ESCALATED.format(
                id=conversation.id,
                reason=reason
            ))
            return conversation
        except Exception as e:
            error_msg = f"Database error during escalation: {str(e)}"
            logger.error(error_msg)
            raise ConversationEscalationError(
                conversation.id,
                reason,
                error_msg
            )
    
    @staticmethod
    def resolve_conversation(
        conversation: ConversationHistory
    ) -> ConversationHistory:
        """
        Resolve a conversation.
        
        Args:
            conversation: Conversation to resolve
            
        Returns:
            Updated conversation instance
            
        Raises:
            ConversationResolutionError: If resolution fails
        """
        try:
            conversation.status = ConversationHistory.Status.RESOLVED
            conversation.resolved_at = timezone.now()
            conversation.save()
            
            logger.info(LOG_CONVERSATION_RESOLVED.format(id=conversation.id))
            return conversation
        except Exception as e:
            error_msg = f"Database error during resolution: {str(e)}"
            logger.error(error_msg)
            raise ConversationResolutionError(
                conversation.id,
                error_msg
            )


class ConversationLogUpdateService:
    """
    Service for updating conversation logs (session-level metrics).
    
    Handles synchronization between conversation history and logs.
    """
    
    @staticmethod
    def update_or_create_session_log(session_id: str) -> ConversationLogs:
        """
        Update or create conversation log for a session.
        
        Aggregates conversation statistics for the given session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Updated ConversationLogs instance
            
        Raises:
            ConversationLogUpdateError: If log update fails
        """
        try:
            session_log, created = ConversationLogs.objects.get_or_create(
                session_id=session_id,
                defaults={
                    'created_at': timezone.now(),
                    'total_conversations': 0,
                    'resolved_conversations': 0,
                    'escalated_conversations': 0,
                }
            )
            
            # Get all conversations for this session
            session_conversations = ConversationHistory.objects.filter(
                session_id=session_id
            )
            
            # Update metrics
            session_log.total_conversations = session_conversations.count()
            session_log.resolved_conversations = session_conversations.filter(
                status=ConversationHistory.Status.RESOLVED
            ).count()
            session_log.escalated_conversations = session_conversations.filter(
                is_escalated=True
            ).count()
            
            # Update last conversation timestamp
            last_conversation = session_conversations.order_by(
                '-created_at'
            ).first()
            if last_conversation:
                session_log.last_conversation_at = last_conversation.created_at
            
            session_log.save()
            
            logger.info(LOG_CONVERSATION_LOG_UPDATED.format(
                session_id=session_id,
                created=created
            ))
            
            return session_log
            
        except Exception as e:
            error_msg = f"Database error during log update: {str(e)}"
            logger.error(error_msg)
            raise ConversationLogUpdateError(
                session_id,
                error_msg
            )
