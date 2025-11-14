# Generated migration to add email_notifications_enabled field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system_settings', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemsettings',
            name='email_notifications_enabled',
            field=models.BooleanField(
                default=True,
                help_text='Enable or disable email notifications'
            ),
        ),
    ]

