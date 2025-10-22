"""
Dashboard Models

This module contains models for storing and tracking dashboard metrics.
Following Clean Code principles: Single Responsibility, meaningful names.
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta


class DashboardMetric(models.Model):
    """
    Base model for storing time-series dashboard metrics.
    
    Stores daily aggregated metrics for dashboard statistics.
    Each record represents metrics for a specific date.
    """
    
    date = models.DateField(
        unique=True,
        db_index=True,
        help_text="Date for which metrics are recorded"
    )
    
    # Conversation Metrics
    active_conversations = models.IntegerField(
        default=0,
        help_text="Number of active conversations on this date"
    )
    total_conversations = models.IntegerField(
        default=0,
        help_text="Total number of conversations created on this date"
    )
    resolved_conversations = models.IntegerField(
        default=0,
        help_text="Number of conversations resolved on this date"
    )
    
    # User Metrics
    total_users = models.IntegerField(
        default=0,
        help_text="Number of unique users on this date"
    )
    unique_visitors = models.IntegerField(
        default=0,
        help_text="Number of unique visitors on this date"
    )
    
    # Escalation Metrics
    escalated_cases = models.IntegerField(
        default=0,
        help_text="Number of cases escalated on this date"
    )
    pending_review = models.IntegerField(
        default=0,
        help_text="Number of cases pending review on this date"
    )
    
    # Response Time Metrics (in milliseconds)
    avg_response_time = models.FloatField(
        default=0.0,
        help_text="Average AI response time in seconds"
    )
    fastest_response_time = models.FloatField(
        default=0.0,
        help_text="Fastest response time in seconds"
    )
    slowest_response_time = models.FloatField(
        default=0.0,
        help_text="Slowest response time in seconds"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Dashboard Metric"
        verbose_name_plural = "Dashboard Metrics"
        db_table = "dashboard_metrics"
        indexes = [
            models.Index(fields=['-date']),
        ]
    
    def __str__(self):
        return f"Metrics for {self.date}"
    
    @property
    def resolution_rate(self):
        """Calculate resolution rate percentage."""
        if self.total_conversations == 0:
            return 0.0
        return round(
            (self.resolved_conversations / self.total_conversations) * 100,
            2
        )


class LanguageDistribution(models.Model):
    """
    Model for tracking language distribution in conversations.
    
    Stores the count of conversations per language per date.
    """
    
    date = models.DateField(
        db_index=True,
        help_text="Date for which language distribution is recorded"
    )
    language = models.CharField(
        max_length=50,
        help_text="Language code (e.g., 'en', 'sv')"
    )
    language_name = models.CharField(
        max_length=100,
        help_text="Full language name (e.g., 'English', 'Swedish')"
    )
    conversation_count = models.IntegerField(
        default=0,
        help_text="Number of conversations in this language"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-conversation_count']
        verbose_name = "Language Distribution"
        verbose_name_plural = "Language Distributions"
        db_table = "language_distribution"
        unique_together = [['date', 'language']]
        indexes = [
            models.Index(fields=['-date', 'language']),
        ]
    
    def __str__(self):
        return f"{self.language_name} - {self.date} ({self.conversation_count})"

