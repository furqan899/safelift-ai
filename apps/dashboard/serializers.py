"""
Dashboard Serializers

Serializers for dashboard API responses.
Following Clean Code principles: clear, descriptive field names and documentation.
"""

from rest_framework import serializers


class MetricChangeSerializer(serializers.Serializer):
    """
    Serializer for a metric with change information.
    
    Used for metrics that show current value and comparison to previous period.
    """
    
    value = serializers.FloatField(
        help_text="Current metric value"
    )
    change = serializers.FloatField(
        help_text="Percentage change from comparison period"
    )
    is_increase = serializers.BooleanField(
        help_text="Whether the value has increased"
    )
    is_positive = serializers.BooleanField(
        help_text="Whether the change is positive (green) or negative (red)"
    )
    comparison = serializers.CharField(
        help_text="Comparison period description (e.g., 'yesterday', 'last week')"
    )


class ResolutionRateSerializer(MetricChangeSerializer):
    """Serializer for resolution rate metric with previous value."""
    
    previous_value = serializers.FloatField(
        help_text="Previous period's resolution rate"
    )


class ResponseTimeSerializer(serializers.Serializer):
    """Serializer for AI response time metrics."""
    
    average = serializers.FloatField(
        help_text="Average response time in seconds"
    )
    fastest = serializers.FloatField(
        help_text="Fastest response time in seconds"
    )
    slowest = serializers.FloatField(
        help_text="Slowest response time in seconds"
    )
    change = serializers.FloatField(
        help_text="Change in average response time"
    )
    is_increase = serializers.BooleanField(
        help_text="Whether response time has increased"
    )
    is_positive = serializers.BooleanField(
        help_text="Whether the change is positive (faster is better)"
    )
    comparison = serializers.CharField(
        help_text="Comparison period"
    )


class LanguageDistributionSerializer(serializers.Serializer):
    """Serializer for language distribution data."""
    
    language = serializers.CharField(
        help_text="Language code (e.g., 'en', 'sv')"
    )
    language_name = serializers.CharField(
        help_text="Full language name"
    )
    count = serializers.IntegerField(
        help_text="Number of conversations in this language"
    )
    percentage = serializers.FloatField(
        help_text="Percentage of total conversations"
    )


class QuickActionSerializer(serializers.Serializer):
    """Serializer for quick action items."""
    
    title = serializers.CharField(
        help_text="Action title"
    )
    description = serializers.CharField(
        help_text="Action description"
    )
    action = serializers.CharField(
        help_text="Action identifier"
    )
    icon = serializers.CharField(
        help_text="Icon identifier"
    )


class DashboardOverviewSerializer(serializers.Serializer):
    """
    Main serializer for dashboard overview data.
    
    Combines all dashboard metrics into a single response.
    """
    
    active_conversations = MetricChangeSerializer(
        help_text="Active conversations metric"
    )
    total_users = MetricChangeSerializer(
        help_text="Total users today metric"
    )
    resolution_rate = ResolutionRateSerializer(
        help_text="Resolution rate metric"
    )
    escalated_cases = MetricChangeSerializer(
        help_text="Escalated cases metric"
    )
    response_time = ResponseTimeSerializer(
        help_text="AI response time metrics"
    )
    language_distribution = LanguageDistributionSerializer(
        many=True,
        help_text="Language distribution over past 30 days"
    )
    quick_actions = QuickActionSerializer(
        many=True,
        help_text="Quick action items"
    )
    
    class Meta:
        ref_name = 'DashboardOverview'

