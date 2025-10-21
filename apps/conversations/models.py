from django.db import models
from apps.users.models import User

class ConversationHistory(models.Model):
    """
    A model for a conversation between a user and the AI assistant.
    """
    session_id = models.CharField(max_length=255)
    user_query = models.TextField()
    ai_response = models.TextField()
    status = models.CharField(max_length=255)
    response_time = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.session_id} - {self.created_at}"

class ConversationLogs(models.Model):
    """
    A model for the conversation logs for each session.
    """
    total_conversations = models.IntegerField()
    resolved_conversations = models.IntegerField()
    escalated_conversations = models.IntegerField()
    success_rate = models.FloatField()