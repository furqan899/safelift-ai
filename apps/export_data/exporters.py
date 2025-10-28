"""
Exporters for generating export files in different formats.

Implements a simple strategy pattern with CSV, JSON, and PDF exporters.
CSV exports multiple data types as a ZIP archive when necessary.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from datetime import timedelta
from io import StringIO
from typing import Dict, List, Tuple
from zipfile import ZipFile, ZIP_DEFLATED

from django.conf import settings
from django.utils import timezone

from apps.conversations.models import ConversationHistory
from apps.knowledge_base.models import KnowledgeBaseEntry
from apps.escalations.models import Escalation
from apps.dashboard.models import DashboardMetric


@dataclass
class ExportContext:
    export_id: int
    data_types: List[str]
    date_range_days: int
    include_personal_data: bool


class BaseExporter:
    def __init__(self, context: ExportContext) -> None:
        self.context = context
        self.media_root = settings.MEDIA_ROOT
        self.base_dir = os.path.join(self.media_root, "exports", str(self.context.export_id))
        os.makedirs(self.base_dir, exist_ok=True)

    def export(self) -> Tuple[str, int]:
        raise NotImplementedError

    # Data gathering helpers
    def _get_date_bounds(self) -> Tuple[timezone.datetime, timezone.datetime]:
        end = timezone.now()
        start = end - timedelta(days=self.context.date_range_days)
        return start, end

    def _fetch_conversations(self) -> List[Dict]:
        start, end = self._get_date_bounds()
        qs = ConversationHistory.objects.filter(created_at__range=(start, end))
        results: List[Dict] = []
        for c in qs.iterator():
            item = {
                "id": c.id,
                "session_id": c.session_id,
                "user_query": c.user_query,
                "ai_response": c.ai_response,
                "status": c.status,
                "language": c.language,
                "response_time_ms": c.response_time,
                "is_escalated": c.is_escalated,
                "escalated_at": c.escalated_at.isoformat() if c.escalated_at else None,
                "escalation_reason": c.escalation_reason,
                "created_at": c.created_at.isoformat(),
            }
            if self.context.include_personal_data and c.user:
                item["user_email"] = getattr(c.user, "email", None)
            results.append(item)
        return results

    def _fetch_knowledge_base(self) -> List[Dict]:
        start, end = self._get_date_bounds()
        qs = KnowledgeBaseEntry.objects.filter(created_at__range=(start, end))
        results: List[Dict] = []
        for k in qs.iterator():
            item = {
                "id": str(k.id),
                "category": k.category,
                "status": k.status,
                "issue_title_en": k.issue_title_en,
                "solution_en": k.solution_en,
                "issue_title_sv": k.issue_title_sv,
                "solution_sv": k.solution_sv,
                "created_at": k.created_at.isoformat(),
            }
            if self.context.include_personal_data and k.created_by:
                item["created_by_email"] = getattr(k.created_by, "email", None)
            results.append(item)
        return results

    def _fetch_escalations(self) -> List[Dict]:
        start, end = self._get_date_bounds()
        qs = Escalation.objects.filter(created_at__range=(start, end))
        results: List[Dict] = []
        for e in qs.iterator():
            item = {
                "id": e.id,
                "equipment_id": e.equipment_id,
                "problem_description": e.problem_description,
                "status": e.status,
                "priority": e.priority,
                "language": e.language,
                "created_at": e.created_at.isoformat(),
            }
            if self.context.include_personal_data:
                item["customer_name"] = e.customer_name
                item["customer_email"] = e.customer_email
            results.append(item)
        return results

    def _fetch_analytics(self) -> List[Dict]:
        start_date, _ = self._get_date_bounds()
        qs = DashboardMetric.objects.filter(date__gte=start_date.date())
        return [
            {
                "date": m.date.isoformat(),
                "active_conversations": m.active_conversations,
                "total_conversations": m.total_conversations,
                "resolved_conversations": m.resolved_conversations,
                "total_users": m.total_users,
                "unique_visitors": m.unique_visitors,
                "escalated_cases": m.escalated_cases,
                "pending_review": m.pending_review,
                "avg_response_time": m.avg_response_time,
                "fastest_response_time": m.fastest_response_time,
                "slowest_response_time": m.slowest_response_time,
            }
            for m in qs.iterator()
        ]

    def _collect_data(self) -> Dict[str, List[Dict]]:
        data: Dict[str, List[Dict]] = {}
        if "conversations" in self.context.data_types:
            data["conversations"] = self._fetch_conversations()
        if "knowledge_base" in self.context.data_types:
            data["knowledge_base"] = self._fetch_knowledge_base()
        if "escalations" in self.context.data_types:
            data["escalations"] = self._fetch_escalations()
        if "analytics" in self.context.data_types:
            data["analytics"] = self._fetch_analytics()
        return data


class CsvExporter(BaseExporter):
    def export(self) -> Tuple[str, int]:
        data = self._collect_data()

        # If multiple datasets, produce a zip with one CSV per dataset
        if len(data.keys()) > 1:
            zip_path = os.path.join(self.base_dir, f"export_{self.context.export_id}.zip")
            with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
                for name, rows in data.items():
                    csv_buffer = StringIO()
                    if rows:
                        writer = csv.DictWriter(csv_buffer, fieldnames=list(rows[0].keys()))
                        writer.writeheader()
                        writer.writerows(rows)
                    else:
                        writer = csv.DictWriter(csv_buffer, fieldnames=["empty"])
                        writer.writeheader()
                    zf.writestr(f"{name}.csv", csv_buffer.getvalue())
            return zip_path, os.path.getsize(zip_path)

        # Single dataset: write a standalone CSV
        name, rows = next(iter(data.items())) if data else ("export", [])
        file_path = os.path.join(self.base_dir, f"{name}.csv")
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            else:
                writer = csv.DictWriter(f, fieldnames=["empty"])
                writer.writeheader()
        return file_path, os.path.getsize(file_path)


class JsonExporter(BaseExporter):
    def export(self) -> Tuple[str, int]:
        data = self._collect_data()
        file_path = os.path.join(self.base_dir, f"export_{self.context.export_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path, os.path.getsize(file_path)


class PdfExporter(BaseExporter):
    def export(self) -> Tuple[str, int]:
        # Simple PDF summary using reportlab if available
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except Exception as _:
            # Fallback: write a text file with .pdf extension
            file_path = os.path.join(self.base_dir, f"export_{self.context.export_id}.pdf")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("PDF export requires reportlab. Falling back to plain text summary.\n")
                data = self._collect_data()
                for section, rows in data.items():
                    f.write(f"\n== {section.upper()} ({len(rows)} records) ==\n")
            return file_path, os.path.getsize(file_path)

        file_path = os.path.join(self.base_dir, f"export_{self.context.export_id}.pdf")
        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4
        y = height - 50
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Safelift Export Summary")
        y -= 25
        c.setFont("Helvetica", 10)
        data = self._collect_data()
        for section, rows in data.items():
            if y < 80:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 10)
            c.drawString(50, y, f"{section.title()}: {len(rows)} records")
            y -= 16
        c.showPage()
        c.save()
        return file_path, os.path.getsize(file_path)


def get_exporter(format_value: str, context: ExportContext) -> BaseExporter:
    fmt = (format_value or "").lower()
    if fmt == "csv":
        return CsvExporter(context)
    if fmt == "json":
        return JsonExporter(context)
    if fmt == "pdf":
        return PdfExporter(context)
    # Default to JSON when unknown
    return JsonExporter(context)


