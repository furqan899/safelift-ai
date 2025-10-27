"""
Serializers for Conversation models.

Following Clean Code principles: clear naming, proper validation, DRY.
"""

from rest_framework import serializers
from .models import ConversationHistory, ConversationLogs
from .constants import (
    MILLISECONDS_PER_SECOND,
    PERCENTAGE_DECIMAL_PLACES,
    MAX_SEARCH_QUERY_LENGTH
)


class ConversationHistorySerializer(serializers.ModelSerializer):
    """
    Complete serializer for conversation history entries.
    
    Provides all fields for detailed conversation tracking.
    """
    
    # Status and language display fields
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    language_display = serializers.CharField(
        source='get_language_display',
        read_only=True
    )
    
    # Response time in seconds (converted from milliseconds)
    response_time_seconds = serializers.SerializerMethodField()
    
    # Formatted timestamps
    created_at_formatted = serializers.DateTimeField(
        source='created_at',
        read_only=True,
        format='%Y-%m-%d %H:%M:%S'
    )
    
    # Override with validation
    user_query = serializers.CharField(
        max_length=MAX_SEARCH_QUERY_LENGTH,
        required=True,
        help_text="User's question or query"
    )
    ai_response = serializers.CharField(
        max_length=MAX_SEARCH_QUERY_LENGTH,
        required=True,
        help_text="AI assistant's response"
    )
    
    
    class Meta:
        model = ConversationHistory
        fields = [
            'id',
            'session_id',
            'user',
            'user_query',
            'ai_response',
            'status',
            'status_display',
            'language',
            'language_display',
            'response_time',
            'response_time_seconds',
            'is_escalated',
            'escalated_at',
            'escalation_reason',
            'created_at',
            'created_at_formatted',
            'updated_at',
            'resolved_at'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'escalated_at',
            'resolved_at'
        ]
    
    def get_response_time_seconds(self, obj) -> float:
        """Convert response time from milliseconds to seconds."""
        if obj.response_time:
            return round(
                obj.response_time / MILLISECONDS_PER_SECOND,
                PERCENTAGE_DECIMAL_PLACES
            )
        return 0.0


class ConversationHistoryListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing conversations.
    
    Optimized for table views with minimal data.
    """
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    language_display = serializers.CharField(source='get_language_display', read_only=True)
    response_time_seconds = serializers.SerializerMethodField()
    created_at_formatted = serializers.DateTimeField(
        source='created_at',
        read_only=True,
        format='%Y-%m-%d %H:%M:%S'
    )
    
    class Meta:
        model = ConversationHistory
        fields = [
            'id',
            'session_id',
            'user_query',
            'ai_response',
            'status',
            'status_display',
            'language',
            'language_display',
            'response_time_seconds',
            'created_at_formatted',
            'is_escalated'
        ]
    
    def get_response_time_seconds(self, obj) -> float:
        """Convert response time from milliseconds to seconds."""
        if obj.response_time:
            return round(
                obj.response_time / MILLISECONDS_PER_SECOND,
                PERCENTAGE_DECIMAL_PLACES
            )
        return 0.0


class ConversationLogsSerializer(serializers.ModelSerializer):
    """
    Serializer for conversation logs (session-level metrics).
    """
    
    created_at_formatted = serializers.DateTimeField(
        source='created_at',
        read_only=True,
        format='%Y-%m-%d %H:%M:%S'
    )
    last_conversation_at_formatted = serializers.DateTimeField(
        source='last_conversation_at',
        read_only=True,
        format='%Y-%m-%d %H:%M:%S'
    )
    
    class Meta:
        model = ConversationLogs
        fields = [
            'id',
            'session_id',
            'total_conversations',
            'resolved_conversations',
            'escalated_conversations',
            'success_rate',
            'created_at',
            'created_at_formatted',
            'updated_at',
            'last_conversation_at',
            'last_conversation_at_formatted'
        ]
        read_only_fields = [
            'id',
            'success_rate',
            'created_at',
            'updated_at'
        ]


class ConversationStatsSerializer(serializers.Serializer):
    """
    Serializer for overall conversation statistics.
    
    Used for the summary cards in the conversation logs dashboard.
    """
    
    total_conversations = serializers.IntegerField()
    resolved_conversations = serializers.IntegerField()
    escalated_conversations = serializers.IntegerField()
    success_rate = serializers.FloatField()
