from django.db import models
from apps.users.models import User


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
    
    def escalate(self, reason: str = '') -> None:
        """Mark conversation as escalated."""
        from django.utils import timezone
        self.is_escalated = True
        self.status = self.Status.ESCALATED
        self.escalated_at = timezone.now()
        self.escalation_reason = reason
        self.save()
    
    def resolve(self) -> None:
        """Mark conversation as resolved."""
        from django.utils import timezone
        self.status = self.Status.RESOLVED
        self.resolved_at = timezone.now()
        self.save()

class ConversationLogs(models.Model):
    """
    A model for the conversation logs for each session.
    """
    total_conversations = models.IntegerField()
    resolved_conversations = models.IntegerField()
    escalated_conversations = models.IntegerField()
    success_rate = models.FloatField()

    class Meta:
        db_table = "conversation_logs"