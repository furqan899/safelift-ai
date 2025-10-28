"""
Unit tests for the export_data app.

Tests for models, services, serializers, and views.
"""

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.users.models import User
from .models import Export
from .services import ExportService
from .exceptions import (
    ExportCreationError,
    ExportValidationError,
    ExportRetryError,
    ExportDownloadError,
)


class ExportServiceTestCase(TestCase):
    """Test cases for ExportService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            full_name="Test User",
        )

    def test_create_export_success(self):
        """Test successful export creation."""
        export = ExportService.create_export(
            user=self.user,
            data_types=["conversations", "escalations"],
            format="csv",
            date_range_days=30,
            include_personal_data=False,
        )

        self.assertEqual(export.status, Export.Status.PENDING)
        self.assertEqual(export.created_by, self.user)
        self.assertEqual(export.data_types, ["conversations", "escalations"])
        self.assertEqual(export.format, "csv")
        self.assertEqual(export.date_range_days, 30)

    def test_create_export_invalid_date_range_too_low(self):
        """Test export creation with date_range_days too low."""
        with self.assertRaises(ExportCreationError) as context:
            ExportService.create_export(
                user=self.user,
                data_types=["conversations"],
                format="csv",
                date_range_days=0,
            )
        self.assertIn("between", str(context.exception))

    def test_create_export_invalid_date_range_too_high(self):
        """Test export creation with date_range_days too high."""
        with self.assertRaises(ExportCreationError):
            ExportService.create_export(
                user=self.user,
                data_types=["conversations"],
                format="csv",
                date_range_days=500,
            )

    def test_retry_export_success(self):
        """Test successful export retry."""
        export = Export.objects.create(
            created_by=self.user,
            status=Export.Status.FAILED,
            error_message="Test error",
        )

        retried = ExportService.retry_export(export)

        self.assertEqual(retried.status, Export.Status.PENDING)
        self.assertEqual(retried.progress_percentage, 0)
        self.assertEqual(retried.error_message, "")

    def test_retry_export_not_failed(self):
        """Test retry on non-failed export."""
        export = Export.objects.create(
            created_by=self.user,
            status=Export.Status.COMPLETED,
        )

        with self.assertRaises(ExportRetryError) as context:
            ExportService.retry_export(export)
        self.assertIn("failed", str(context.exception).lower())

    def test_update_progress_success(self):
        """Test progress update."""
        export = Export.objects.create(
            created_by=self.user,
            status=Export.Status.PROCESSING,
        )

        updated = ExportService.update_progress(export, 50)

        self.assertEqual(updated.progress_percentage, 50)

    def test_update_progress_invalid_percentage(self):
        """Test progress update with invalid percentage."""
        export = Export.objects.create(created_by=self.user)

        with self.assertRaises(ExportValidationError):
            ExportService.update_progress(export, 150)

    def test_mark_completed(self):
        """Test marking export as completed."""
        export = Export.objects.create(
            created_by=self.user,
            status=Export.Status.PROCESSING,
        )

        completed = ExportService.mark_completed(
            export,
            file_path="exports/test.csv",
            file_size=1024,
        )

        self.assertEqual(completed.status, Export.Status.COMPLETED)
        self.assertEqual(completed.progress_percentage, 100)
        self.assertEqual(completed.file_path, "exports/test.csv")
        self.assertEqual(completed.file_size, 1024)
        self.assertIsNotNone(completed.completed_at)

    def test_mark_failed(self):
        """Test marking export as failed."""
        export = Export.objects.create(
            created_by=self.user,
            status=Export.Status.PROCESSING,
        )

        failed = ExportService.mark_failed(export, "Database error")

        self.assertEqual(failed.status, Export.Status.FAILED)
        self.assertEqual(failed.error_message, "Database error")

    def test_get_download_info_success(self):
        """Test getting download info for completed export."""
        export = Export.objects.create(
            created_by=self.user,
            status=Export.Status.COMPLETED,
            file_path="exports/test.csv",
            file_size=1024,
            format="csv",
        )

        info = ExportService.get_download_info(export)

        self.assertIn("download_url", info)
        self.assertEqual(info["file_size"], 1024)
        self.assertEqual(info["format"], "csv")

    def test_get_download_info_not_completed(self):
        """Test getting download info for incomplete export."""
        export = Export.objects.create(
            created_by=self.user,
            status=Export.Status.PROCESSING,
        )

        with self.assertRaises(ExportDownloadError):
            ExportService.get_download_info(export)

    def test_get_export_stats(self):
        """Test export statistics retrieval."""
        # Create multiple exports with different statuses
        Export.objects.create(created_by=self.user, status=Export.Status.PENDING)
        Export.objects.create(created_by=self.user, status=Export.Status.PROCESSING)
        Export.objects.create(created_by=self.user, status=Export.Status.COMPLETED)
        Export.objects.create(created_by=self.user, status=Export.Status.FAILED)

        stats = ExportService.get_export_stats()

        self.assertEqual(stats["total"], 4)
        self.assertEqual(stats["pending"], 1)
        self.assertEqual(stats["processing"], 1)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["failed"], 1)


class ExportViewSetTestCase(APITestCase):
    """Test cases for ExportViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            full_name="Test User",
        )
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="adminpass123",
            full_name="Admin User",
            is_admin=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_list_exports_authenticated(self):
        """Test listing exports as authenticated user."""
        Export.objects.create(created_by=self.user, status=Export.Status.COMPLETED)

        response = self.client.get("/api/export-data/exports/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_exports_unauthenticated(self):
        """Test listing exports without authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/export-data/exports/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_export_success(self):
        """Test successful export creation via API."""
        data = {
            "data_types": ["conversations"],
            "format": "csv",
            "date_range_days": 30,
            "include_personal_data": False,
        }

        response = self.client.post("/api/export-data/exports/", data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "pending")

    def test_create_export_invalid_data_types(self):
        """Test export creation with invalid data types."""
        data = {
            "data_types": [],
            "format": "csv",
            "date_range_days": 30,
        }

        response = self.client.post("/api/export-data/exports/", data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_export_invalid_date_range(self):
        """Test export creation with invalid date range."""
        data = {
            "data_types": ["conversations"],
            "format": "csv",
            "date_range_days": 500,
        }

        response = self.client.post("/api/export-data/exports/", data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_export_success(self):
        """Test retrieving export details."""
        export = Export.objects.create(
            created_by=self.user,
            status=Export.Status.COMPLETED,
        )

        response = self.client.get(f"/api/export-data/exports/{export.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], export.id)

    def test_retry_export_success(self):
        """Test retrying a failed export."""
        export = Export.objects.create(
            created_by=self.user,
            status=Export.Status.FAILED,
        )

        response = self.client.post(f"/api/export-data/exports/{export.id}/retry/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        export.refresh_from_db()
        self.assertEqual(export.status, Export.Status.PENDING)

    def test_retry_export_not_failed(self):
        """Test retrying a non-failed export."""
        export = Export.objects.create(
            created_by=self.user,
            status=Export.Status.COMPLETED,
        )

        response = self.client.post(f"/api/export-data/exports/{export.id}/retry/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_download_export_success(self):
        """Test downloading a completed export."""
        export = Export.objects.create(
            created_by=self.user,
            status=Export.Status.COMPLETED,
            file_path="exports/test.csv",
            file_size=1024,
        )

        response = self.client.get(f"/api/export-data/exports/{export.id}/download/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("download_url", response.data)

    def test_download_export_not_completed(self):
        """Test downloading an incomplete export."""
        export = Export.objects.create(
            created_by=self.user,
            status=Export.Status.PROCESSING,
        )

        response = self.client.get(f"/api/export-data/exports/{export.id}/download/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_exports_filter_by_status(self):
        """Test listing exports with status filter."""
        Export.objects.create(created_by=self.user, status=Export.Status.PENDING)
        Export.objects.create(created_by=self.user, status=Export.Status.COMPLETED)

        response = self.client.get("/api/export-data/exports/?status=completed")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["status"], "completed")

    def test_admin_sees_all_exports(self):
        """Test that admin sees all exports."""
        other_user = User.objects.create_user(
            email="other@example.com",
            password="otherpass123",
        )
        Export.objects.create(created_by=self.user, status=Export.Status.COMPLETED)
        Export.objects.create(created_by=other_user, status=Export.Status.COMPLETED)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/export-data/exports/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_user_sees_only_own_exports(self):
        """Test that regular user sees only their own exports."""
        other_user = User.objects.create_user(
            email="other@example.com",
            password="otherpass123",
        )
        Export.objects.create(created_by=self.user, status=Export.Status.COMPLETED)
        Export.objects.create(created_by=other_user, status=Export.Status.COMPLETED)

        response = self.client.get("/api/export-data/exports/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["created_by_name"], "Test User")
