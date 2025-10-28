"""
Escalation Services

Business logic for escalations: creation from conversations, status updates,
and summary metrics for the header cards.
"""

from typing import Dict, Any, Optional
import logging
from django.utils import timezone

from apps.conversations.models import ConversationHistory
from .models import Escalation


logger = logging.getLogger(__name__)


class EscalationService:
    @staticmethod
    def create_from_conversation(
        conversation: ConversationHistory,
        *,
        problem_description: Optional[str] = None,
        conversation_transcript: str = "",
        priority: Optional[str] = None,
    ) -> Escalation:
        """Create an escalation seeded from a conversation."""
        escalation = Escalation.objects.create(
            conversation=conversation,
            customer_name=getattr(conversation.user, "full_name", "") or "",
            customer_email=getattr(conversation.user, "email", "") or "",
            equipment_id="",  # Populate when equipment domain is available
            problem_description=(
                problem_description
                or conversation.escalation_reason
                or conversation.user_query
            ),
            conversation_transcript=conversation_transcript,
            language=conversation.language,
            status=Escalation.Status.PENDING,
            priority=priority or Escalation.Priority.MEDIUM,
        )
        logger.info("Escalation created from conversation %s", conversation.id)
        return escalation

    @staticmethod
    def set_status(
        escalation: Escalation,
        *,
        status: str,
        internal_notes: Optional[str] = None,
    ) -> Escalation:
        """Update escalation status and keep linked conversation in sync."""
        escalation.status = status
        if internal_notes is not None:
            escalation.internal_notes = internal_notes
        escalation.save()

        # Sync linked conversation status
        if escalation.conversation:
            if status == Escalation.Status.RESOLVED:
                escalation.conversation.status = ConversationHistory.Status.RESOLVED
                escalation.conversation.resolved_at = timezone.now()
            else:
                escalation.conversation.status = ConversationHistory.Status.ESCALATED
            escalation.conversation.save()

        logger.info("Escalation %s status updated to %s", escalation.id, status)
        return escalation

    @staticmethod
    def get_summary_counts() -> Dict[str, Any]:
        """Counts for header summary cards on the monitoring screen."""
        total = Escalation.objects.count()
        pending = Escalation.objects.filter(status=Escalation.Status.PENDING).count()
        in_progress = Escalation.objects.filter(status=Escalation.Status.IN_PROGRESS).count()
        resolved = Escalation.objects.filter(status=Escalation.Status.RESOLVED).count()
        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "resolved": resolved,
        }


