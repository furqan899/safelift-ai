"""
Export Services

Business logic for data exports: creation, retry, progress tracking, and validation.
"""

import logging
from typing import Dict, Any, Optional
from datetime import timedelta

from django.utils import timezone
from django.db.models import QuerySet, Count, Q

from apps.users.models import User
from .models import Export
from .constants import (
    MIN_DATE_RANGE_DAYS,
    MAX_DATE_RANGE_DAYS,
    PROGRESS_MIN,
    PROGRESS_MAX,
)
from .exceptions import (
    ExportCreationError,
    ExportRetryError,
    ExportDownloadError,
    ExportValidationError,
)
from .exporters import ExportContext, get_exporter


logger = logging.getLogger(__name__)


class ExportService:
    """Service for managing export operations."""

    @staticmethod
    def create_export(
        user: User,
        data_types: list,
        format: str,
        date_range_days: int,
        include_personal_data: bool = False,
    ) -> Export:
        """
        Create a new export job with validation.
        """
        if date_range_days < MIN_DATE_RANGE_DAYS or date_range_days > MAX_DATE_RANGE_DAYS:
            raise ExportCreationError.invalid_date_range(MIN_DATE_RANGE_DAYS, MAX_DATE_RANGE_DAYS)
        
        try:
            export = Export.objects.create(
                created_by=user,
                data_types=data_types,
                format=format,
                date_range_days=date_range_days,
                include_personal_data=include_personal_data,
                status=Export.Status.PENDING,
            )
            logger.info(
                "Export %d created by %s with types: %s",
                export.id,
                user.email,
                ", ".join(data_types),
            )
            return export
        except Exception as exc:
            logger.error("Failed to create export: %s", str(exc), exc_info=True)
            raise

    @staticmethod
    def run_export(export: Export) -> Export:
        """
        Execute the export synchronously (can be called from a background worker).
        """
        logger.info("Starting export %d", export.id)
        export.status = Export.Status.PROCESSING
        export.progress_percentage = 10
        export.save()

        try:
            context = ExportContext(
                export_id=export.id,
                data_types=export.data_types or [],
                date_range_days=export.date_range_days,
                include_personal_data=export.include_personal_data,
            )
            exporter = get_exporter(export.format, context)
            file_path, file_size = exporter.export()

            export = ExportService.mark_completed(export, file_path=file_path, file_size=file_size)
            logger.info("Export %d successfully completed", export.id)
            return export
        except Exception as exc:
            logger.error("Export %d failed: %s", export.id, str(exc), exc_info=True)
            export = ExportService.mark_failed(export, str(exc))
            return export

    @staticmethod
    def retry_export(export: Export) -> Export:
        """Retry a failed export."""
        if export.status != Export.Status.FAILED:
            raise ExportRetryError.not_retryable(export.id)

        export.status = Export.Status.PENDING
        export.progress_percentage = 0
        export.error_message = ""
        export.save()

        logger.info("Export %d retry initiated by %s", export.id, export.created_by.email)
        return export

    @staticmethod
    def update_progress(
        export: Export,
        percentage: int,
        status: Optional[str] = None,
    ) -> Export:
        """Update export progress percentage and optionally status."""
        if percentage < PROGRESS_MIN or percentage > PROGRESS_MAX:
            raise ExportValidationError.invalid_progress(PROGRESS_MIN, PROGRESS_MAX)

        export.progress_percentage = percentage
        if status:
            export.status = status
        export.save()

        logger.debug("Export %d progress updated to %d%%", export.id, percentage)
        return export

    @staticmethod
    def mark_completed(
        export: Export,
        file_path: str,
        file_size: int,
    ) -> Export:
        """Mark export as completed with file info."""
        export.status = Export.Status.COMPLETED
        export.progress_percentage = 100
        export.file_path = file_path
        export.file_size = file_size
        export.completed_at = timezone.now()
        export.save()

        logger.info("Export %d completed. File: %s, Size: %d bytes", export.id, file_path, file_size)
        return export

    @staticmethod
    def mark_failed(export: Export, error_message: str) -> Export:
        """Mark export as failed with error message."""
        export.status = Export.Status.FAILED
        export.error_message = error_message
        export.save()

        logger.error("Export %d failed: %s", export.id, error_message)
        return export

    @staticmethod
    def get_download_info(export: Export) -> Dict[str, Any]:
        """Get download information for a completed export."""
        if export.status != Export.Status.COMPLETED:
            raise ExportDownloadError.not_ready(export.id)

        if not export.file_path:
            raise ExportDownloadError.file_missing(export.id)

        return {
            "download_url": f"/media/{export.file_path}",
            "file_size": export.file_size,
            "format": export.format,
            "created_at": export.created_at.isoformat(),
        }

    @staticmethod
    def cleanup_old_exports(days: int = 30) -> int:
        """Delete old completed exports."""
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_exports = Export.objects.filter(
            status=Export.Status.COMPLETED,
            completed_at__lt=cutoff_date,
        ).delete()

        count = deleted_exports[0] if deleted_exports else 0
        logger.info("Deleted %d old exports", count)
        return count

    @staticmethod
    def get_user_export_history(user: User, limit: int = 10) -> QuerySet:
        """Get recent exports for a user."""
        return (
            Export.objects.filter(created_by=user)
            .order_by("-created_at")[:limit]
        )

    @staticmethod
    def get_export_stats() -> Dict[str, Any]:
        """Get system-wide export statistics with optimized query."""
        stats = Export.objects.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(status=Export.Status.PENDING)),
            processing=Count("id", filter=Q(status=Export.Status.PROCESSING)),
            completed=Count("id", filter=Q(status=Export.Status.COMPLETED)),
            failed=Count("id", filter=Q(status=Export.Status.FAILED)),
        )

        logger.info("Export stats retrieved")
        return stats
