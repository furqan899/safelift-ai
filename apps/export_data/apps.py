from django.apps import AppConfig


class ExportDataConfig(AppConfig):
    """Configuration for export data app."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.export_data"
    verbose_name = "Export Data"