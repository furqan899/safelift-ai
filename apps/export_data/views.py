"""
Views for Export management.

Following clean code principles: single responsibility, proper error handling.
"""

import logging
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.conf import settings
from django.http import FileResponse
import os

from .models import Export
from .serializers import (
    ExportListSerializer,
    ExportDetailSerializer,
    ExportCreateSerializer,
)
from .services import ExportService
from .constants import PARAM_STATUS, PARAM_FORMAT
from .exceptions import (
    ExportCreationError,
    ExportRetryError,
    ExportDownloadError,
)


logger = logging.getLogger(__name__)


@extend_schema(tags=["Export Data"])
class ExportViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet for managing data exports."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return ExportListSerializer
        elif self.action == "create":
            return ExportCreateSerializer
        return ExportDetailSerializer

    def get_queryset(self):
        """
        Filter exports based on user role and query parameters.

        Admins see all exports. Regular users see only their own.
        Supports filtering by status and format.
        """
        if self.request.user.is_admin:
            qs = Export.objects.select_related("created_by").all()
        else:
            qs = Export.objects.filter(created_by=self.request.user).select_related(
                "created_by"
            )

        # Filter by status
        status_param = self.request.query_params.get(PARAM_STATUS)
        if status_param:
            qs = qs.filter(status=status_param)

        # Filter by format
        format_param = self.request.query_params.get(PARAM_FORMAT)
        if format_param:
            qs = qs.filter(format=format_param)

        return qs

    @extend_schema(
        summary="Download Export",
        description="Securely download a completed export file",
        tags=["Export Data"],
    )
    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        export = self.get_object()

        # Ownership/admin check
        if not (request.user.is_admin or export.created_by_id == request.user.id):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        # Status check
        if export.status != export.Status.COMPLETED or not export.file_path:
            return Response({"error": "Export not ready"}, status=status.HTTP_400_BAD_REQUEST)

        file_abspath = os.path.join(str(settings.MEDIA_ROOT), export.file_path)
        if not os.path.isfile(file_abspath):
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        response = FileResponse(open(file_abspath, "rb"), as_attachment=True)
        # Suggest a filename
        filename = f"export-{export.id}.{export.format}"
        response["Content-Disposition"] = f"attachment; filename=\"{filename}\""
        return response

    @extend_schema(
        summary="List Exports",
        description="Get all export history with optional filtering by status and format",
        tags=["Export Data"],
    )
    def list(self, request, *args, **kwargs):
        """List all exports with optional filtering."""
        try:
            return super().list(request, *args, **kwargs)
        except ValueError as e:
            logger.warning("Invalid filter parameter: %s", str(e))
            return Response(
                {"error": "Invalid filter parameter"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error("Error listing exports: %s", str(e), exc_info=True)
            return Response(
                {"error": "Failed to retrieve exports"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Create Export",
        description="Create a new export job with selected data types and format",
        tags=["Export Data"],
    )
    def create(self, request, *args, **kwargs):
        """Create a new export job."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = serializer.validated_data
            export = ExportService.create_export(
                user=request.user,
                data_types=data.get('data_types', []),
                format=data.get('format'),
                date_range_days=data.get('date_range_days'),
                include_personal_data=data.get('include_personal_data', False),
            )
            logger.info("Export %d created successfully", export.id)
            return Response(
                ExportDetailSerializer(export).data, status=status.HTTP_201_CREATED
            )
        except ExportCreationError as e:
            logger.warning("Invalid export parameters: %s", str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Failed to create export: %s", str(e), exc_info=True)
            return Response(
                {"error": "Failed to create export"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Get Export Details",
        description="Get details of a specific export job",
        tags=["Export Data"],
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific export."""
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            logger.warning("Export not found: %s", str(e))
            return Response(
                {"error": "Export not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="retry",
    )
    @extend_schema(
        summary="Retry Failed Export",
        description="Retry an export that failed",
        tags=["Export Data"],
    )
    def retry(self, request, pk=None):
        """Retry a failed export."""
        export = self.get_object()

        try:
            export = ExportService.retry_export(export)
            logger.info("Export %d retry initiated", export.id)
            return Response(
                ExportDetailSerializer(export).data, status=status.HTTP_200_OK
            )
        except ExportRetryError as e:
            logger.warning("Cannot retry export %s: %s", pk, str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Error retrying export %d: %s", pk, str(e), exc_info=True)
            return Response(
                {"error": "Failed to retry export"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="download",
    )
    @extend_schema(
        summary="Download Export File",
        description="Get download URL for completed export",
        tags=["Export Data"],
    )
    def download(self, request, pk=None):
        """Get download link for export."""
        export = self.get_object()

        try:
            download_info = ExportService.get_download_info(export)
            logger.info("Download info retrieved for export %d", export.id)
            return Response(download_info, status=status.HTTP_200_OK)
        except ExportDownloadError as e:
            logger.warning("Cannot download export %s: %s", pk, str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(
                "Error retrieving download info for export %d: %s",
                pk,
                str(e),
                exc_info=True,
            )
            return Response(
                {"error": "Failed to retrieve download information"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
