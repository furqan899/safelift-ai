from django.urls import path
from .views import SystemSettingsView


app_name = 'system_settings'


urlpatterns = [
    path('', SystemSettingsView.as_view(), name='system-settings'),
]


