from django.db import models
from django.contrib.auth import get_user_model
import uuid
from django.utils import timezone

User = get_user_model()


class KnowledgeBaseEntry(models.Model):
    """
    Model for storing bilingual troubleshooting entries with embeddings.
    
    Supports English and Swedish content for troubleshooting solutions.
    Generates embeddings for semantic search using Pinecone.
    """

    # Status choices
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'

    # Embedding status choices
    class EmbeddingStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # English content (optional)
    issue_title_en = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Issue title in English"
    )
    solution_en = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed solution in English"
    )
    
    # Swedish content (optional)
    issue_title_sv = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Issue title in Swedish"
    )
    solution_sv = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed solution in Swedish"
    )

    # Category and status
    category = models.CharField(
        max_length=100,
        help_text="Troubleshooting category (e.g., Hydraulics, Brakes, Engine)"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text="Entry status (Active/Inactive)"
    )

    # Embedding and vector storage
    embedding_status = models.CharField(
        max_length=20,
        choices=EmbeddingStatus.choices,
        default=EmbeddingStatus.PENDING,
        help_text="Status of embedding generation"
    )
    pinecone_vector_ids = models.JSONField(
        default=list,
        help_text="List of vector IDs in Pinecone (one per language)"
    )

    # Metadata (optional, for future use)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata for the entry"
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Optional tags for categorization and filtering"
    )

    # User and timestamps
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='knowledge_base_entries'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When embeddings were last generated"
    )

    class Meta:
        db_table = 'knowledge_base_entry'
        ordering = ['-created_at']
        verbose_name = 'Knowledge Base Entry'
        verbose_name_plural = 'Knowledge Base Entries'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['embedding_status']),
            models.Index(fields=['category']),
            models.Index(fields=['created_by']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        title = self.issue_title_en or self.issue_title_sv or "Untitled"
        return f"{title} ({self.category})"

    def get_combined_content_en(self) -> str:
        """Get combined English content for embedding generation."""
        return f"{self.issue_title_en}\n\n{self.solution_en}"

    def get_combined_content_sv(self) -> str:
        """Get combined Swedish content for embedding generation."""
        return f"{self.issue_title_sv}\n\n{self.solution_sv}"

    def has_both_languages(self) -> bool:
        """Check if entry has content in both languages."""
        return bool(
            self.issue_title_en and self.solution_en and
            self.issue_title_sv and self.solution_sv
        )

    def is_active(self) -> bool:
        """Check if entry is active."""
        return self.status == self.Status.ACTIVE

    def is_embedding_complete(self) -> bool:
        """Check if embedding generation is complete."""
        return self.embedding_status == self.EmbeddingStatus.COMPLETED
