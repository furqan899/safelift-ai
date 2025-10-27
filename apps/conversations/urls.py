"""
URL configuration for conversations app.

Provides endpoints for managing conversation history and logs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ConversationHistoryViewSet, ConversationLogsViewSet

# Create router for ViewSets
router = DefaultRouter()
router.register(
    r'history',
    ConversationHistoryViewSet,
    basename='conversation-history'
)
router.register(
    r'logs',
    ConversationLogsViewSet,
    basename='conversation-logs'
)

app_name = 'conversations'

# URL patterns
urlpatterns = [
    # ViewSet routes
    path('', include(router.urls)),
]

