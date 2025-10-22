"""
Dashboard URL Configuration

URL patterns for dashboard API endpoints.
"""

from django.urls import path
from .views import (
    DashboardOverviewView,
    LanguageDistributionView,
    QuickActionsView,
    HealthStatusView,
)

app_name = "dashboard"

urlpatterns = [
    # Main dashboard overview
    path("overview/", DashboardOverviewView.as_view(), name="overview"),
    
    # Detailed analytics endpoints
    path("language-distribution/", LanguageDistributionView.as_view(), name="language-distribution"),
    path("quick-actions/", QuickActionsView.as_view(), name="quick-actions"),
    
    # System health
    path("health/", HealthStatusView.as_view(), name="health"),
]

