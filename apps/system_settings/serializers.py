from rest_framework import serializers
from .models import SystemSettings


class SystemSettingsSerializer(serializers.ModelSerializer):
    """Serializer for the SystemSettings singleton."""

    class Meta:
        model = SystemSettings
        fields = [
            'auto_detect_language',
            'default_language',
            'notification_email',
            'escalation_threshold',
            'widget_title',
            'welcome_message',
            'updated_at',
        ]
        read_only_fields = ['updated_at']

    def validate_escalation_threshold(self, value: int) -> int:
        if value < 1 or value > 10:
            raise serializers.ValidationError('Escalation threshold must be between 1 and 10')
        return value


