from django.db import models
from django.utils import timezone

from apps.conversations.models import ConversationHistory


class Escalation(models.Model):
    """
    Represents an escalated support request derived from a conversation.

    Stores customer details, equipment context, problem description, language,
    status tracking, and internal notes used by admins to process the case.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    # Optional link back to the originating conversation
    conversation = models.ForeignKey(
        ConversationHistory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="escalations",
        help_text="Originating conversation, if available",
    )

    # Customer context
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()

    # Equipment context
    equipment_id = models.CharField(max_length=100, db_index=True)

    # Case details
    problem_description = models.TextField()
    conversation_transcript = models.TextField(blank=True, default="")

    # Mirror conversation language choices for consistency
    language = models.CharField(
        max_length=10,
        choices=ConversationHistory.Language.choices,
        default=ConversationHistory.Language.ENGLISH,
        db_index=True,
    )

    # Workflow
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
    )
    internal_notes = models.TextField(blank=True, default="")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "escalations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at", "status"]),
            models.Index(fields=["equipment_id", "-created_at"]),
            models.Index(fields=["language", "-created_at"]),
            models.Index(fields=["priority", "status"]),
        ]

    def __str__(self) -> str:
        return f"Escalation #{self.pk or 'new'} - {self.status}"

    def save(self, *args, **kwargs):
        # Maintain resolved_at timestamp when status transitions to resolved
        if self.status == self.Status.RESOLVED and self.resolved_at is None:
            self.resolved_at = timezone.now()
        if self.status != self.Status.RESOLVED:
            # Clear resolved_at if moved out of resolved
            self.resolved_at = None
        super().save(*args, **kwargs)


