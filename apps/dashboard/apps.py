from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """Configuration for dashboard app."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.dashboard"
    verbose_name = "Dashboard"