from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class SystemSettings(models.Model):
    """
    Singleton model to store global system settings used by the admin UI.
    """

    class Language(models.TextChoices):
        ENGLISH = 'en', 'English'
        SWEDISH = 'sv', 'Swedish'

    # Language & Localization
    auto_detect_language = models.BooleanField(default=True)
    default_language = models.CharField(
        max_length=5,
        choices=Language.choices,
        default=Language.ENGLISH,
    )

    # Notifications
    notification_email = models.EmailField(blank=True, default='')
    escalation_threshold = models.PositiveSmallIntegerField(default=3)

    # Branding & Appearance
    widget_title = models.CharField(
        max_length=120,
        blank=True,
        default='Safelift AI Assistant'
    )
    welcome_message = models.TextField(blank=True, default='')

    # Audit
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='updated_system_settings'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_settings'

    def save(self, *args, **kwargs):
        """Ensure only one instance exists (enforce singleton)."""
        self.pk = 1  # force primary key
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls) -> 'SystemSettings':
        """Return the single settings instance, creating with defaults if missing."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self) -> str:
        return 'System Settings'


