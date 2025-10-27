from django.db import models
from apps.users.models import User
from .constants import PERCENTAGE_BASE, PERCENTAGE_DECIMAL_PLACES, DEFAULT_SUCCESS_RATE

class ConversationHistory(models.Model):
    """
    Model for storing conversation history between users and the AI assistant.
    
    Each record represents a single conversation exchange with complete
    tracking of status, performance metrics, and escalation information.
    """
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        RESOLVED = 'resolved', 'Resolved'
        ESCALATED = 'escalated', 'Escalated'
        PENDING = 'pending', 'Pending'
    
    class Language(models.TextChoices):
        """Supported conversation languages - focusing on Swedish and English."""
        SWEDISH = 'sv', 'Swedish'
        ENGLISH = 'en', 'English'
    
    # Session Information
    session_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Unique session identifier"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        help_text="User who initiated the conversation"
    )
    
    # Conversation Content
    user_query = models.TextField(help_text="User's question or query")
    ai_response = models.TextField(help_text="AI assistant's response")
    
    # Status and Language
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        help_text="Current status of the conversation"
    )
    language = models.CharField(
        max_length=10,
        choices=Language.choices,
        default=Language.ENGLISH,
        db_index=True,
        help_text="Language of the conversation (Swedish or English)"
    )
    
    # Performance Metrics
    response_time = models.IntegerField(
        help_text="AI response time in milliseconds"
    )
    
    # Escalation Information
    is_escalated = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this conversation has been escalated"
    )
    escalated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the conversation was escalated"
    )
    escalation_reason = models.TextField(
        blank=True,
        default='',
        help_text="Reason for escalation"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the conversation was resolved"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Conversation History"
        verbose_name_plural = "Conversation Histories"
        db_table = "conversation_history"
        indexes = [
            models.Index(fields=['-created_at', 'status']),
            models.Index(fields=['session_id', '-created_at']),
            models.Index(fields=['language', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.session_id} - {self.created_at}"
    
    # Note: escalate() and resolve() methods moved to ConversationActionService
    # This follows Clean Code principles: business logic belongs in services, not models

class ConversationLogs(models.Model):
    """
    Model for tracking aggregated conversation statistics per session.
    
    This represents session-level metrics summarizing all conversations
    within a specific session.
    """
    
    # Session Information
    session_id = models.CharField(
        max_length=255,
        db_index=True,
        unique=True,
        help_text="Unique session identifier"
    )
    
    # Aggregated Metrics
    total_conversations = models.IntegerField(
        default=0,
        help_text="Total number of conversations in this session"
    )
    resolved_conversations = models.IntegerField(
        default=0,
        help_text="Number of resolved conversations in this session"
    )
    escalated_conversations = models.IntegerField(
        default=0,
        help_text="Number of escalated conversations in this session"
    )
    
    # Calculated Metrics
    success_rate = models.FloatField(
        default=0.0,
        help_text="Success rate percentage for this session"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        db_index=True,
        help_text="When the session started",
        null=True,
        blank=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update timestamp",
        null=True,
        blank=True
    )
    last_conversation_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of the last conversation in this session"
    )
    
    class Meta:
        ordering = ['-last_conversation_at', '-created_at']
        verbose_name = "Conversation Log"
        verbose_name_plural = "Conversation Logs"
        db_table = "conversation_logs"
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['-last_conversation_at']),
            models.Index(fields=['session_id']),
        ]
    
    def __str__(self):
        return f"Session {self.session_id} - {self.total_conversations} conversations"
    
    @property
    def calculated_success_rate(self) -> float:
        """
        Calculate success rate as a property.
        
        Returns:
            Success rate as float (0-100)
        """
        if self.total_conversations == 0:
            return DEFAULT_SUCCESS_RATE
        
        percentage = (self.resolved_conversations / self.total_conversations) * PERCENTAGE_BASE
        return round(percentage, PERCENTAGE_DECIMAL_PLACES)
    
    def save(self, *args, **kwargs):
        """
        Override save to auto-calculate and store success rate.
        
        Calculates success rate automatically before saving.
        """
        self.success_rate = self.calculated_success_rate
        super().save(*args, **kwargs)