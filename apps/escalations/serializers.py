from rest_framework import serializers

from .models import Escalation


class EscalationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escalation
        fields = [
            "id",
            "created_at",
            "customer_name",
            "customer_email",
            "equipment_id",
            "problem_description",
            "language",
            "status",
            "priority",
        ]


class EscalationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escalation
        fields = [
            "id",
            "created_at",
            "updated_at",
            "resolved_at",
            "customer_name",
            "customer_email",
            "equipment_id",
            "problem_description",
            "conversation_transcript",
            "language",
            "status",
            "priority",
            "internal_notes",
            "conversation",
        ]
        read_only_fields = ["created_at", "updated_at", "resolved_at", "conversation"]


class EscalationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escalation
        fields = ["status", "priority", "internal_notes"]


