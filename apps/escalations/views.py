from django.db import models
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.authentication.permissions import IsAdminUser
from drf_spectacular.utils import extend_schema
from .models import Escalation
from .serializers import (
    EscalationListSerializer,
    EscalationDetailSerializer,
    EscalationUpdateSerializer,
)
from .services import EscalationService

@extend_schema(
    tags=["Escalations"],
    summary="Manage escalations",
    description="CRUD operations for escalations",
)
class EscalationViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        viewsets.GenericViewSet):
    queryset = Escalation.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action == "list":
            return EscalationListSerializer
        if self.action in ["update", "partial_update", "set_status"]:
            return EscalationUpdateSerializer
        return EscalationDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get("status")
        priority_param = self.request.query_params.get("priority")
        language_param = self.request.query_params.get("language")
        search_param = self.request.query_params.get("q")

        if status_param:
            qs = qs.filter(status=status_param)
        if priority_param:
            qs = qs.filter(priority=priority_param)
        if language_param:
            qs = qs.filter(language=language_param)
        if search_param:
            qs = qs.filter(
                models.Q(customer_name__icontains=search_param)
                | models.Q(customer_email__icontains=search_param)
                | models.Q(equipment_id__icontains=search_param)
                | models.Q(problem_description__icontains=search_param)
            )
        return qs

    @action(detail=True, methods=["post"], url_path="set-status")
    def set_status(self, request, pk=None):
        escalation = self.get_object()
        serializer = EscalationUpdateSerializer(instance=escalation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        EscalationService.set_status(
            escalation,
            status=serializer.validated_data.get("status", escalation.status),
            internal_notes=serializer.validated_data.get("internal_notes", escalation.internal_notes),
        )
        return Response(EscalationDetailSerializer(escalation).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        """Return summary counts for header cards."""
        return Response(EscalationService.get_summary_counts())


