from django.contrib import admin
from .models import SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'default_language', 'notification_email', 'escalation_threshold', 'updated_at'
    )

    def has_add_permission(self, request):
        # Prevent adding more than one instance
        if SystemSettings.objects.exists():
            return False
        return super().has_add_permission(request)


