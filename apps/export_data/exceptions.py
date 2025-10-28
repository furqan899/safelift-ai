"""
Custom exceptions for the export_data app.

Specific, meaningful exceptions following clean code principles.
"""

from typing import Optional


class ExportError(Exception):
    """Base exception for all export-related errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class ExportNotFoundError(ExportError):
    """Raised when an export instance is not found."""

    def __init__(self, export_id: int, details: Optional[str] = None):
        super().__init__(f"Export with ID {export_id} not found", details)
        self.export_id = export_id


class ExportCreationError(ExportError):
    """Raised when creating an export fails."""

    @staticmethod
    def invalid_date_range(min_days: int, max_days: int) -> "ExportCreationError":
        return ExportCreationError(
            f"date_range_days must be between {min_days} and {max_days}"
        )


class ExportRetryError(ExportError):
    """Raised when retrying an export fails."""

    @staticmethod
    def not_retryable(export_id: int) -> "ExportRetryError":
        return ExportRetryError(
            f"Export {export_id} is not in failed state and cannot be retried"
        )


class ExportDownloadError(ExportError):
    """Raised when attempting to download an export that's not ready."""

    @staticmethod
    def not_ready(export_id: int) -> "ExportDownloadError":
        return ExportDownloadError(f"Export {export_id} is not ready for download")

    @staticmethod
    def file_missing(export_id: int) -> "ExportDownloadError":
        return ExportDownloadError(f"Export {export_id} file not found")


class ExportValidationError(ExportError):
    """Raised when export data validation fails."""

    @staticmethod
    def invalid_progress(min_value: int, max_value: int) -> "ExportValidationError":
        return ExportValidationError(
            f"Progress must be between {min_value} and {max_value}"
        )

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, details)
