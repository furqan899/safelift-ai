from django.db import models
from django.utils import timezone
from apps.users.models import User


class Export(models.Model):
    """Represents an export job with status tracking and download management."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    class Format(models.TextChoices):
        CSV = "csv", "CSV (Spreadsheet)"
        JSON = "json", "JSON"
        PDF = "pdf", "PDF"

    class DataType(models.TextChoices):
        CONVERSATIONS = "conversations", "Conversation Logs"
        KNOWLEDGE_BASE = "knowledge_base", "Knowledge Base"
        ESCALATIONS = "escalations", "Escalated Cases"
        ANALYTICS = "analytics", "Usage Analytics"

    # User and metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="exports",
    )

    # Export configuration
    data_types = models.JSONField(
        default=list,
        help_text="List of data types to include in export",
    )
    format = models.CharField(
        max_length=10,
        choices=Format.choices,
        default=Format.CSV,
    )
    date_range_days = models.IntegerField(
        default=30,
        help_text="Number of days to look back for data",
    )
    include_personal_data = models.BooleanField(
        default=False,
        help_text="Include customer names and emails",
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    progress_percentage = models.IntegerField(
        default=0,
        help_text="Export progress 0-100%",
    )

    # File management
    file_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Path to exported file",
    )
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes",
    )

    # Error tracking
    error_message = models.TextField(
        blank=True,
        default="",
        help_text="Error message if export failed",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "exports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at", "status"]),
            models.Index(fields=["created_by", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Export {self.id} - {self.format} - {self.status}"

    def save(self, *args, **kwargs):
        if self.status == self.Status.COMPLETED and self.completed_at is None:
            self.completed_at = timezone.now()
        if self.status != self.Status.COMPLETED:
            self.completed_at = None
        super().save(*args, **kwargs)
