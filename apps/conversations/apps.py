"""
App configuration for the conversations module.

This module contains the Django app configuration for managing conversations
and their associated logs.
"""

from django.apps import AppConfig


class ConversationsConfig(AppConfig):
    """
    Configuration for the conversations app.
    
    Manages conversation history and logs functionality.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.conversations"
    verbose_name = "Conversations"