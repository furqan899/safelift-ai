from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.authentication.permissions import IsAdminUser
from .models import SystemSettings
from .serializers import SystemSettingsSerializer


@extend_schema(tags=["System Settings"])
class SystemSettingsView(APIView):
    """Admin-only API to get and update global system settings."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Get system settings", responses={200: SystemSettingsSerializer}
    )
    def get(self, request):
        settings_obj = SystemSettings.get_solo()
        serializer = SystemSettingsSerializer(settings_obj)
        return Response(serializer.data)

    @extend_schema(
        summary="Update system settings",
        request=SystemSettingsSerializer,
        responses={200: SystemSettingsSerializer},
    )
    def put(self, request):
        settings_obj = SystemSettings.get_solo()
        serializer = SystemSettingsSerializer(settings_obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        instance.updated_by = request.user
        instance.save(update_fields=["updated_by"])
        return Response(SystemSettingsSerializer(instance).data)

    @extend_schema(
        summary="Partially update system settings",
        request=SystemSettingsSerializer,
        responses={200: SystemSettingsSerializer},
    )
    def patch(self, request):
        settings_obj = SystemSettings.get_solo()
        serializer = SystemSettingsSerializer(
            settings_obj, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        instance.updated_by = request.user
        instance.save(update_fields=["updated_by"])
        return Response(SystemSettingsSerializer(instance).data)
