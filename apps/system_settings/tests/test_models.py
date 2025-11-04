from django.test import TestCase
from apps.system_settings.models import SystemSettings


class SystemSettingsModelTest(TestCase):
    def test_singleton_behavior(self):
        s1 = SystemSettings.get_solo()
        s2 = SystemSettings.get_solo()
        self.assertEqual(s1.pk, 1)
        self.assertEqual(s2.pk, 1)
        self.assertEqual(SystemSettings.objects.count(), 1)

    def test_defaults(self):
        settings_obj = SystemSettings.get_solo()
        self.assertTrue(settings_obj.auto_detect_language)
        self.assertEqual(settings_obj.default_language, SystemSettings.Language.ENGLISH)
        self.assertEqual(settings_obj.escalation_threshold, 3)


