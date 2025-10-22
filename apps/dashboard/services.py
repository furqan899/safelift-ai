"""
Dashboard Services

Business logic layer for dashboard operations.
Follows Clean Code principles: Single Responsibility, DRY, meaningful names.
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Min, Max, Count, Q, Sum
from typing import Dict, List, Any, Optional

from .models import DashboardMetric, LanguageDistribution
from apps.conversations.models import ConversationHistory
from apps.users.models import User

logger = logging.getLogger(__name__)


class DashboardMetricsService:
    """
    Service class for calculating and retrieving dashboard metrics.
    
    Separates business logic from views following clean architecture.
    Each method has a single, well-defined responsibility.
    """
    
    @staticmethod
    def get_today_metrics() -> Dict[str, Any]:
        """
        Retrieve current day's dashboard metrics with optimized queries.
        
        Uses batch queries to minimize database hits and improve performance.
        
        Returns:
            Dictionary containing today's metrics with comparison to yesterday
        """
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Fetch both metrics in a single query (optimization)
        metrics = DashboardMetric.objects.filter(
            date__in=[today, yesterday]
        ).order_by('-date')
        
        # Convert to dictionary for easy lookup
        metrics_dict = {m.date: m for m in metrics}
        
        # Get or create metrics if they don't exist
        today_metric = metrics_dict.get(today)
        if not today_metric:
            today_metric = DashboardMetricsService.update_daily_metrics(today)
        
        yesterday_metric = metrics_dict.get(yesterday)
        if not yesterday_metric:
            yesterday_metric = DashboardMetricsService.update_daily_metrics(yesterday)
        
        return {
            "active_conversations": DashboardMetricsService._calculate_metric_with_change(
                today_metric.active_conversations,
                yesterday_metric.active_conversations,
                "yesterday"
            ),
            "total_users": DashboardMetricsService._calculate_metric_with_change(
                today_metric.total_users,
                yesterday_metric.total_users,
                "yesterday"
            ),
            "resolution_rate": DashboardMetricsService._calculate_resolution_rate(
                today, 
                today - timedelta(days=7)
            ),
            "escalated_cases": DashboardMetricsService._calculate_metric_with_change(
                today_metric.escalated_cases,
                yesterday_metric.escalated_cases,
                "yesterday",
                inverse=True
            ),
            "response_time": DashboardMetricsService._get_response_time_metrics(today)
        }
    
    @staticmethod
    def get_language_distribution(days: int = 30) -> List[Dict[str, Any]]:
        """
        Get language distribution for conversations over specified days.
        
        Args:
            days: Number of days to look back (default: 30)
            
        Returns:
            List of dictionaries containing language distribution data
        """
        start_date = timezone.now().date() - timedelta(days=days)
        
        distributions = LanguageDistribution.objects.filter(
            date__gte=start_date
        ).values("language", "language_name").annotate(
            total_count=Sum('conversation_count')
        ).order_by('-total_count')
        
        total_conversations = sum(d["total_count"] for d in distributions)
        
        if total_conversations == 0:
            return []
        
        return [
            {
                "language": dist["language"],
                "language_name": dist["language_name"],
                "count": dist["total_count"],
                "percentage": round((dist["total_count"] / total_conversations) * 100, 1)
            }
            for dist in distributions
        ]
    
    @staticmethod
    def get_quick_actions() -> List[Dict[str, str]]:
        """
        Retrieve quick action items for the dashboard.
        
        Returns:
            List of quick action dictionaries
        """
        return [
            {
                "title": "Manage Knowledge Base",
                "description": "Add or edit AI responses",
                "action": "knowledge_base",
                "icon": "database"
            },
            {
                "title": "View Recent Logs",
                "description": "Review conversation history",
                "action": "conversation_logs",
                "icon": "logs"
            },
            {
                "title": "Export Reports",
                "description": "Download analytics data",
                "action": "export_reports",
                "icon": "download"
            }
        ]
    
    @staticmethod
    def update_daily_metrics(date: Optional[datetime.date] = None) -> DashboardMetric:
        """
        Update or create daily metrics for a specific date.
        
        Populates all metric fields including conversation stats, user stats,
        escalations, and response times using optimized queries.
        
        Args:
            date: Date to update metrics for (defaults to today)
            
        Returns:
            Updated DashboardMetric instance
        """
        if date is None:
            date = timezone.now().date()
        
        logger.info(f"Updating daily metrics for {date}")
        
        try:
            metric, created = DashboardMetric.objects.get_or_create(date=date)
            
            # Fetch all conversations for the date (single query)
            conversations = ConversationHistory.objects.filter(
                created_at__date=date
            )
            
            # Calculate conversation metrics using aggregation
            conversation_stats = conversations.aggregate(
                total=Count("id"),
                active=Count("id", filter=Q(status=ConversationHistory.Status.ACTIVE)),
                resolved=Count("id", filter=Q(status=ConversationHistory.Status.RESOLVED)),
                escalated=Count("id", filter=Q(is_escalated=True)),
                avg_response=Avg("response_time"),
                min_response=Min("response_time"),
                max_response=Max("response_time")
            )
            
            # Update conversation metrics
            metric.total_conversations = conversation_stats["total"] or 0
            metric.active_conversations = conversation_stats["active"] or 0
            metric.resolved_conversations = conversation_stats["resolved"] or 0
            metric.escalated_cases = conversation_stats["escalated"] or 0
            
            # Calculate pending review (escalated but not resolved)
            metric.pending_review = conversations.filter(
                is_escalated=True,
                status__in=[
                    ConversationHistory.Status.PENDING,
                    ConversationHistory.Status.ESCALATED,
                ]
            ).count()
            
            # Update response time metrics (convert milliseconds to seconds)
            if conversation_stats["avg_response"]:
                metric.avg_response_time = round(conversation_stats["avg_response"] / 1000, 2)
                metric.fastest_response_time = round(conversation_stats["min_response"] / 1000, 2)
                metric.slowest_response_time = round(conversation_stats["max_response"] / 1000, 2)
            else:
                metric.avg_response_time = 0.0
                metric.fastest_response_time = 0.0
                metric.slowest_response_time = 0.0
            
            # Calculate unique users (users who had conversations on this date)
            metric.total_users = conversations.filter(
                user__isnull=False
            ).values("user").distinct().count()
            
            # Calculate unique visitors (unique session IDs)
            metric.unique_visitors = conversations.values("session_id").distinct().count()
            
            metric.save()
            
            # Also update language distribution for this date
            DashboardMetricsService.update_language_distribution(date)
            
            logger.info(f"Successfully updated metrics for {date}")
            return metric
            
        except Exception as e:
            logger.error(f"Failed to update daily metrics for {date}: {str(e)}")
            raise
    
    @staticmethod
    def update_language_distribution(date: Optional[datetime.date] = None) -> None:
        """
        Update language distribution for a specific date.
        
        Aggregates conversation counts by language and creates/updates
        LanguageDistribution records for the date.
        
        Args:
            date: Date to update language distribution for (defaults to today)
        """
        if date is None:
            date = timezone.now().date()
        
        logger.info(f"Updating language distribution for {date}")
        
        try:
            # Get language distribution from conversations
            language_stats = ConversationHistory.objects.filter(
                created_at__date=date
            ).values("language").annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Update or create language distribution records
            for lang_stat in language_stats:
                language_code = lang_stat["language"]
                language_name = dict(ConversationHistory.Language.choices).get(
                    language_code,
                    language_code.upper()
                )
                
                LanguageDistribution.objects.update_or_create(
                    date=date,
                    language=language_code,
                    defaults={
                        "language_name": language_name,
                        "conversation_count": lang_stat["count"]
                    },
                )

            logger.info(f"Successfully updated language distribution for {date}")

        except Exception as e:
            logger.error(f"Failed to update language distribution for {date}: {str(e)}")
            raise

    # Private helper methods
    
    @staticmethod
    def _get_or_create_metric(date: datetime.date) -> DashboardMetric:
        """Get or create a dashboard metric for a specific date."""
        metric, created = DashboardMetric.objects.get_or_create(date=date)
        if created:
            DashboardMetricsService.update_daily_metrics(date)
        return metric
    
    @staticmethod
    def _calculate_metric_with_change(
        current: float,
        previous: float,
        comparison_period: str,
        inverse: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate metric with percentage change.
        
        Args:
            current: Current metric value
            previous: Previous metric value
            comparison_period: Period description (e.g., 'yesterday', 'last week')
            inverse: If True, negative change is good (e.g., for escalations)
            
        Returns:
            Dictionary with current value and change information
        """
        if previous == 0:
            change_percentage = 100.0 if current > 0 else 0.0
        else:
            change_percentage = round(((current - previous) / previous) * 100, 1)
        
        is_positive = change_percentage > 0
        if inverse:
            is_positive = not is_positive
        
        return {
            "value": current,
            "change": abs(change_percentage),
            "is_increase": change_percentage > 0,
            "is_positive": is_positive,
            "comparison": comparison_period
        }
    
    @staticmethod
    def _calculate_resolution_rate(
        current_date: datetime.date,
        comparison_date: datetime.date
    ) -> Dict[str, Any]:
        """
        Calculate resolution rate with week-over-week comparison.
        
        Compares current week's average resolution rate with last week's average,
        providing a more stable and meaningful metric than day-to-day comparison.
        
        Args:
            current_date: Current date for calculation
            comparison_date: Date for comparison (typically 7 days ago)
            
        Returns:
            Dictionary with resolution rate metrics and comparison
        """
        # Calculate current week range (Monday to current date)
        current_week_start = current_date - timedelta(days=current_date.weekday())
        
        # Calculate last week range (previous Monday to Sunday)
        last_week_start = current_week_start - timedelta(days=7)
        last_week_end = current_week_start - timedelta(days=1)
        
        # Get current week's average resolution rate
        current_week_metrics = DashboardMetric.objects.filter(
            date__gte=current_week_start,
            date__lte=current_date
        )
        
        # Get last week's average resolution rate
        last_week_metrics = DashboardMetric.objects.filter(
            date__gte=last_week_start,
            date__lte=last_week_end
        )
        
        # Calculate averages using aggregate
        current_week_avg = current_week_metrics.aggregate(
            total_conv=Sum("total_conversations"),
            resolved_conv=Sum("resolved_conversations")
        )
        
        last_week_avg = last_week_metrics.aggregate(
            total_conv=Sum("total_conversations"),
            resolved_conv=Sum("resolved_conversations")
        )
        
        # Calculate resolution rates
        if current_week_avg["total_conv"] and current_week_avg["total_conv"] > 0:
            current_rate = round(
                (current_week_avg["resolved_conv"] / current_week_avg["total_conv"]) * 100,
                1
            )
        else:
            current_rate = 0.0
        
        if last_week_avg["total_conv"] and last_week_avg["total_conv"] > 0:
            comparison_rate = round(
                (last_week_avg["resolved_conv"] / last_week_avg["total_conv"]) * 100,
                1
            )
        else:
            comparison_rate = 0.0
        
        change = round(current_rate - comparison_rate, 1)
        
        return {
            "value": current_rate,
            "change": abs(change),
            "is_increase": change > 0,
            "is_positive": change > 0,
            "comparison": "last week",
            "previous_value": comparison_rate
        }
    
    @staticmethod
    def _get_response_time_metrics(date: datetime.date) -> Dict[str, Any]:
        """Get response time metrics with comparison to last week."""
        current_metric = DashboardMetricsService._get_or_create_metric(date)
        last_week_metric = DashboardMetricsService._get_or_create_metric(
            date - timedelta(days=7)
        )
        
        change = round(
            current_metric.avg_response_time - last_week_metric.avg_response_time,
            2
        )
        
        return {
            "average": current_metric.avg_response_time,
            "fastest": current_metric.fastest_response_time,
            "slowest": current_metric.slowest_response_time,
            "change": abs(change),
            "is_increase": change > 0,
            "is_positive": change < 0,  # Lower response time is better
            "comparison": "last week"
        }

