from rest_framework import serializers
from .models import ConversationHistory, ConversationLogs

class ConversationHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for the conversation history model.
    """
    class Meta:
        model = ConversationHistory
        fields = '__all__'

class ConversationLogsSerializer(serializers.ModelSerializer):
    """
    Serializer for the conversation logs model.
    """
    class Meta:
        model = ConversationLogs
        fields = '__all__'
