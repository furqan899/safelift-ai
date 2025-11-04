"""
Tests for Dashboard models.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import date
from apps.dashboard.models import DashboardMetric, LanguageDistribution


class DashboardMetricModelTest(TestCase):
    """Test cases for DashboardMetric model."""

    def test_dashboard_metric_creation(self):
        """Test creating a dashboard metric."""
        metric = DashboardMetric.objects.create(
            date=date.today(),
            active_conversations=100,
            total_conversations=150,
            resolved_conversations=120,
            total_users=50,
            unique_visitors=45,
            escalated_cases=10,
            pending_review=5,
            avg_response_time=1.5,
            fastest_response_time=0.5,
            slowest_response_time=3.2
        )
        
        self.assertEqual(metric.date, date.today())
        self.assertEqual(metric.active_conversations, 100)
        self.assertEqual(metric.total_conversations, 150)
        self.assertEqual(metric.resolved_conversations, 120)

    def test_resolution_rate_calculation(self):
        """Test resolution rate property calculation."""
        metric = DashboardMetric.objects.create(
            date=date.today(),
            total_conversations=100,
            resolved_conversations=80
        )
        
        self.assertEqual(metric.resolution_rate, 80.0)

    def test_resolution_rate_with_zero_conversations(self):
        """Test resolution rate returns 0 when no conversations."""
        metric = DashboardMetric.objects.create(
            date=date.today(),
            total_conversations=0,
            resolved_conversations=0
        )
        
        self.assertEqual(metric.resolution_rate, 0.0)

    def test_resolution_rate_rounding(self):
        """Test resolution rate is rounded to 2 decimal places."""
        metric = DashboardMetric.objects.create(
            date=date.today(),
            total_conversations=3,
            resolved_conversations=2
        )
        
        # 2/3 = 0.6666... * 100 = 66.67
        self.assertEqual(metric.resolution_rate, 66.67)

    def test_string_representation(self):
        """Test __str__ method."""
        metric = DashboardMetric.objects.create(
            date=date(2024, 1, 15)
        )
        
        self.assertEqual(str(metric), "Metrics for 2024-01-15")

    def test_date_unique_constraint(self):
        """Test date field has unique constraint."""
        DashboardMetric.objects.create(date=date.today())
        
        # Trying to create another metric for same date should fail
        with self.assertRaises(Exception):
            DashboardMetric.objects.create(date=date.today())

    def test_default_values(self):
        """Test default values for numeric fields."""
        metric = DashboardMetric.objects.create(date=date.today())
        
        self.assertEqual(metric.active_conversations, 0)
        self.assertEqual(metric.total_conversations, 0)
        self.assertEqual(metric.resolved_conversations, 0)
        self.assertEqual(metric.avg_response_time, 0.0)


class LanguageDistributionModelTest(TestCase):
    """Test cases for LanguageDistribution model."""

    def test_language_distribution_creation(self):
        """Test creating a language distribution entry."""
        dist = LanguageDistribution.objects.create(
            date=date.today(),
            language='en',
            language_name='English',
            conversation_count=100
        )
        
        self.assertEqual(dist.language, 'en')
        self.assertEqual(dist.language_name, 'English')
        self.assertEqual(dist.conversation_count, 100)

    def test_string_representation(self):
        """Test __str__ method."""
        dist = LanguageDistribution.objects.create(
            date=date(2024, 1, 15),
            language='sv',
            language_name='Swedish',
            conversation_count=50
        )
        
        expected = "Swedish - 2024-01-15 (50)"
        self.assertEqual(str(dist), expected)

    def test_unique_constraint_date_language(self):
        """Test unique constraint on date + language combination."""
        LanguageDistribution.objects.create(
            date=date.today(),
            language='en',
            language_name='English',
            conversation_count=100
        )
        
        # Creating another entry for same date and language should fail
        with self.assertRaises(Exception):
            LanguageDistribution.objects.create(
                date=date.today(),
                language='en',
                language_name='English',
                conversation_count=50
            )

    def test_multiple_languages_same_date(self):
        """Test multiple languages can exist for same date."""
        LanguageDistribution.objects.create(
            date=date.today(),
            language='en',
            language_name='English',
            conversation_count=100
        )
        LanguageDistribution.objects.create(
            date=date.today(),
            language='sv',
            language_name='Swedish',
            conversation_count=50
        )
        
        # Should have 2 entries for today
        count = LanguageDistribution.objects.filter(date=date.today()).count()
        self.assertEqual(count, 2)

    def test_ordering(self):
        """Test default ordering by date and conversation_count."""
        LanguageDistribution.objects.create(
            date=date.today(),
            language='en',
            language_name='English',
            conversation_count=50
        )
        LanguageDistribution.objects.create(
            date=date.today(),
            language='sv',
            language_name='Swedish',
            conversation_count=100
        )
        
        distributions = list(LanguageDistribution.objects.all())
        
        # Should be ordered by conversation_count descending
        self.assertEqual(distributions[0].language, 'sv')
        self.assertEqual(distributions[1].language, 'en')

