"""
Management command to update dashboard metrics.

This command calculates and stores daily metrics for the dashboard,
including conversation statistics, user counts, and language distribution.

Usage:
    python manage.py update_dashboard_metrics
    python manage.py update_dashboard_metrics --date 2024-01-15
    python manage.py update_dashboard_metrics --days 7
"""

from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.dashboard.services import DashboardMetricsService


class Command(BaseCommand):
    """
    Management command to update dashboard metrics.
    
    Follows Clean Code principles: clear purpose, descriptive names,
    proper error handling, and comprehensive logging.
    """
    
    help = 'Update dashboard metrics for specified date(s)'
    
    def add_arguments(self, parser):
        """Add command-line arguments."""
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to update metrics for (YYYY-MM-DD format)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Number of days to update (starting from today or specified date)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if metrics already exist',
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(
            self.style.SUCCESS('Starting dashboard metrics update...')
        )
        
        try:
            # Determine the date range
            end_date = self._parse_end_date(options.get('date'))
            days_count = options.get('days', 1)
            
            if days_count < 1:
                raise CommandError('Days parameter must be positive')
            
            # Calculate date range
            dates_to_update = [
                end_date - timedelta(days=i)
                for i in range(days_count)
            ]
            
            self.stdout.write(
                f'Updating metrics for {len(dates_to_update)} day(s)...'
            )
            
            # Update metrics for each date
            success_count = 0
            error_count = 0
            
            for date in dates_to_update:
                try:
                    self._update_metrics_for_date(date)
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Updated metrics for {date}')
                    )
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to update metrics for {date}: {str(e)}')
                    )
            
            # Print summary
            self.stdout.write('\n' + '='*50)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Metrics update completed: {success_count} succeeded, {error_count} failed'
                )
            )
            
        except CommandError as e:
            self.stdout.write(self.style.ERROR(f'Command error: {str(e)}'))
            raise
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Unexpected error: {str(e)}'))
            raise CommandError(str(e))
    
    def _parse_end_date(self, date_string: str) -> datetime.date:
        """
        Parse date string or use today's date.
        
        Args:
            date_string: Date string in YYYY-MM-DD format or None
            
        Returns:
            Parsed date object
            
        Raises:
            CommandError: If date format is invalid
        """
        if date_string:
            try:
                return datetime.strptime(date_string, '%Y-%m-%d').date()
            except ValueError:
                raise CommandError(
                    f'Invalid date format: {date_string}. Use YYYY-MM-DD format.'
                )
        return timezone.now().date()
    
    def _update_metrics_for_date(self, date: datetime.date) -> None:
        """
        Update metrics for a specific date.
        
        Args:
            date: Date to update metrics for
        """
        # Update daily metrics (this also updates language distribution)
        DashboardMetricsService.update_daily_metrics(date)
        
        # Log progress
        self.stdout.write(f'  - Processed conversations and calculated metrics')
        self.stdout.write(f'  - Updated language distribution')

