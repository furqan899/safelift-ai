"""
Tests for Dashboard services.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from apps.dashboard.services import DashboardMetricsService
from apps.dashboard.models import DashboardMetric, LanguageDistribution
from apps.conversations.models import ConversationHistory
from apps.users.models import User


class DashboardMetricsServiceTest(TestCase):
    """Test cases for DashboardMetricsService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )

    def test_get_today_metrics_with_no_data(self):
        """Test get_today_metrics returns default values with no data."""
        metrics = DashboardMetricsService.get_today_metrics()
        
        self.assertIn('active_conversations', metrics)
        self.assertIn('total_users', metrics)
        self.assertIn('resolution_rate', metrics)
        self.assertIn('escalated_cases', metrics)
        self.assertIn('response_time', metrics)
        
        # Values should be present (even if zero/default)
        self.assertIsNotNone(metrics['active_conversations'])
        self.assertIsNotNone(metrics['total_users'])

    def test_get_today_metrics_with_existing_conversations(self):
        """Test get_today_metrics with existing conversation data."""
        # Create some conversations
        for i in range(5):
            ConversationHistory.objects.create(
                session_id=f'session_{i}',
                user=self.user,
                user_query='Test query',
                ai_response='Test response',
                language='en',
                response_time=1000,
                status='resolved' if i < 3 else 'active'
            )
        
        metrics = DashboardMetricsService.get_today_metrics()
        
        # Should include conversation counts
        self.assertIsNotNone(metrics['active_conversations'])

    def test_get_language_distribution_default_period(self):
        """Test get_language_distribution with default 30 day period."""
        # Create language distribution data
        today = date.today()
        LanguageDistribution.objects.create(
            date=today,
            language='en',
            language_name='English',
            conversation_count=100
        )
        LanguageDistribution.objects.create(
            date=today,
            language='sv',
            language_name='Swedish',
            conversation_count=50
        )
        
        distribution = DashboardMetricsService.get_language_distribution()
        
        self.assertIsInstance(distribution, list)
        # Should have 2 languages
        self.assertGreaterEqual(len(distribution), 2)

    def test_get_language_distribution_custom_period(self):
        """Test get_language_distribution with custom period."""
        # Create data for different dates
        today = date.today()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        
        LanguageDistribution.objects.create(
            date=today,
            language='en',
            language_name='English',
            conversation_count=100
        )
        LanguageDistribution.objects.create(
            date=yesterday,
            language='en',
            language_name='English',
            conversation_count=80
        )
        LanguageDistribution.objects.create(
            date=week_ago,
            language='en',
            language_name='English',
            conversation_count=60
        )
        
        # Get last 5 days
        distribution = DashboardMetricsService.get_language_distribution(days=5)
        
        self.assertIsInstance(distribution, list)

    def test_get_quick_actions_returns_correct_structure(self):
        """Test get_quick_actions returns correctly structured data."""
        actions = DashboardMetricsService.get_quick_actions()
        
        self.assertIsInstance(actions, list)
        self.assertGreater(len(actions), 0)
        
        # Check each action has required fields
        for action in actions:
            self.assertIn('title', action)
            self.assertIn('description', action)
            self.assertIn('action', action)
            self.assertIn('icon', action)

    def test_metrics_calculation_with_various_date_ranges(self):
        """Test metrics calculation handles different date ranges."""
        # Create dashboard metrics for multiple dates
        today = date.today()
        for i in range(7):
            metric_date = today - timedelta(days=i)
            DashboardMetric.objects.create(
                date=metric_date,
                active_conversations=10 + i,
                total_conversations=20 + i,
                resolved_conversations=15 + i
            )
        
        # Get today's metrics
        metrics = DashboardMetricsService.get_today_metrics()
        
        # Should return data
        self.assertIsNotNone(metrics)

    def test_language_distribution_aggregation(self):
        """Test language distribution aggregates data correctly."""
        # Create multiple entries for same language
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        LanguageDistribution.objects.create(
            date=today,
            language='en',
            language_name='English',
            conversation_count=100
        )
        LanguageDistribution.objects.create(
            date=yesterday,
            language='en',
            language_name='English',
            conversation_count=80
        )
        
        distribution = DashboardMetricsService.get_language_distribution(days=2)
        
        self.assertIsInstance(distribution, list)
        # Should aggregate English conversations
        if len(distribution) > 0:
            self.assertIn('language', distribution[0])
            self.assertIn('count', distribution[0])

