from rest_framework import viewsets
from rest_framework.response import Response
from .models import ConversationHistory, ConversationLogs
from .serializers import ConversationHistorySerializer, ConversationLogsSerializer
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

class ConversationHistoryViewSet(viewsets.ModelViewSet):
    """
    API view for the conversation history model.
    """
    queryset = ConversationHistory.objects.all()
    serializer_class = ConversationHistorySerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Conversation History",
        description="Get all conversation history",
        responses={200: ConversationHistorySerializer(many=True)}
    )
    def list(self, request):
        """Get all conversation history."""
        conversation_history = self.get_queryset()
        serializer = ConversationHistorySerializer(conversation_history, many=True)
        return Response(serializer.data)

class ConversationLogsViewSet(viewsets.ModelViewSet):
    """
    API view for the conversation logs model.
    """
    queryset = ConversationLogs.objects.all()
    serializer_class = ConversationLogsSerializer
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary="Get Conversation Logs",
        description="Get all conversation logs",
        responses={200: ConversationLogsSerializer(many=True)}
    )