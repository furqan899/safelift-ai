"""
Views for Knowledge Base management.

Following Clean Code principles:
- Single Responsibility Principle
- Clear naming
- Small, focused methods
- Proper error handling
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import models
from django.db.models import Count
from django.utils import timezone
import logging
from drf_spectacular.utils import extend_schema

from .models import KnowledgeBaseEntry
from .serializers import (
    KnowledgeBaseEntrySerializer,
    KnowledgeBaseEntryCreateSerializer,
    KnowledgeBaseEntryUpdateSerializer,
    KnowledgeBaseEntryListSerializer,
    KnowledgeBaseSearchSerializer
)
from .services import EmbeddingProcessor, EmbeddingService

logger = logging.getLogger(__name__)


@extend_schema(tags=["Knowledge Base"])
class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bilingual knowledge base entries.

    Provides CRUD operations and embedding generation for troubleshooting entries.
    """
    queryset = KnowledgeBaseEntry.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return KnowledgeBaseEntryCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return KnowledgeBaseEntryUpdateSerializer
        elif self.action == 'list':
            return KnowledgeBaseEntryListSerializer
        else:
            return KnowledgeBaseEntrySerializer

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = KnowledgeBaseEntry.objects.filter(created_by=self.request.user)

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__iexact=category)

        # Filter by status (active/inactive)
        entry_status = self.request.query_params.get('status')
        if entry_status:
            queryset = queryset.filter(status=entry_status.lower())

        # Filter by embedding status
        embedding_status = self.request.query_params.get('embedding_status')
        if embedding_status:
            queryset = queryset.filter(embedding_status=embedding_status.lower())

        # Search filter (simple text search in titles)
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(issue_title_en__icontains=search) |
                models.Q(issue_title_sv__icontains=search)
            )

        return queryset

    def perform_create(self, serializer):
        """Create entry and trigger embedding generation."""
        entry = serializer.save()
        self._trigger_embedding_generation(entry)

    def perform_update(self, serializer):
        """Update entry and regenerate embeddings if content changed."""
        entry = serializer.save()
        
        # Check if content fields were updated
        content_fields = [
            'issue_title_en', 'solution_en',
            'issue_title_sv', 'solution_sv'
        ]
        if any(field in serializer.validated_data for field in content_fields):
            self._trigger_embedding_generation(entry)

    def _trigger_embedding_generation(self, entry: KnowledgeBaseEntry) -> None:
        """Trigger embedding generation for an entry."""
        try:
            processor = EmbeddingProcessor(entry.id)
            processor.process_entry()
        except Exception as e:
            logger.error(
                f"Error triggering embedding generation for entry {entry.id}: {str(e)}"
            )

    @action(detail=True, methods=['post'])
    def regenerate_embeddings(self, request, pk=None):
        """Manually trigger embedding regeneration."""
        entry = self.get_object()

        try:
            processor = EmbeddingProcessor(entry.id)
            result = processor.process_entry()

            if result.success:
                return Response({
                    'message': 'Embeddings regenerated successfully',
                    'vector_ids': result.vector_ids
                })
            else:
                return Response(
                    {'error': result.error_message},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"Error regenerating embeddings for entry {pk}: {str(e)}")
            return Response(
                {'error': f'Failed to regenerate embeddings: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle entry status between active and inactive."""
        entry = self.get_object()
        
        # Toggle status
        if entry.status == KnowledgeBaseEntry.Status.ACTIVE:
            entry.status = KnowledgeBaseEntry.Status.INACTIVE
        else:
            entry.status = KnowledgeBaseEntry.Status.ACTIVE
        
        entry.save(update_fields=['status'])
        
        serializer = self.get_serializer(entry)
        return Response(serializer.data)


@extend_schema(tags=["Knowledge Base"])
class KnowledgeBaseSearchView(generics.GenericAPIView):
    """
    View for searching knowledge base entries using vector similarity.

    Supports filtering by language, category, and returns semantically similar results.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = KnowledgeBaseSearchSerializer

    def post(self, request):
        """Search for relevant entries based on query."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data['query']
        language = serializer.validated_data.get('language')
        category = serializer.validated_data.get('category')
        top_k = serializer.validated_data['top_k']
        include_content = serializer.validated_data['include_content']

        try:
            embedding_service = EmbeddingService()
            results = embedding_service.search(
                query=query,
                language=language,
                category=category,
                top_k=top_k,
                include_content=include_content
            )

            # Format results for response
            formatted_results = [
                {
                    'entry_id': result.entry_id,
                    'score': result.score,
                    'content': result.content,
                    'language': result.language,
                    'category': result.category,
                    'metadata': result.metadata
                }
                for result in results
            ]

            return Response({
                'query': query,
                'language': language,
                'category': category,
                'results': formatted_results,
                'count': len(formatted_results)
            })

        except Exception as e:
            logger.error(f"Error searching entries: {str(e)}")
            return Response(
                {'error': f'Search failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(tags=["Knowledge Base"])
class KnowledgeBaseStatsView(generics.GenericAPIView):
    """Get statistics about knowledge base entries."""
    permission_classes = [IsAuthenticated]
    serializer_class = None

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "total_entries": {"type": "integer"},
                    "active_entries": {"type": "integer"},
                    "inactive_entries": {"type": "integer"},
                    "embedding_status_breakdown": {
                        "type": "object",
                        "properties": {
                            "pending": {"type": "integer"},
                            "processing": {"type": "integer"},
                            "completed": {"type": "integer"},
                            "failed": {"type": "integer"}
                        }
                    },
                    "category_breakdown": {"type": "object"},
                    "recent_entries": {"type": "integer"},
                    "bilingual_entries": {"type": "integer"}
                }
            }
        }
    )
    def get(self, request):
        """Get statistics about user's knowledge base entries."""
        user = request.user
        entries = KnowledgeBaseEntry.objects.filter(created_by=user)

        stats = {
            'total_entries': entries.count(),
            'active_entries': entries.filter(
                status=KnowledgeBaseEntry.Status.ACTIVE
            ).count(),
            'inactive_entries': entries.filter(
                status=KnowledgeBaseEntry.Status.INACTIVE
            ).count(),
            'embedding_status_breakdown': {
                'pending': entries.filter(
                    embedding_status=KnowledgeBaseEntry.EmbeddingStatus.PENDING
                ).count(),
                'processing': entries.filter(
                    embedding_status=KnowledgeBaseEntry.EmbeddingStatus.PROCESSING
                ).count(),
                'completed': entries.filter(
                    embedding_status=KnowledgeBaseEntry.EmbeddingStatus.COMPLETED
                ).count(),
                'failed': entries.filter(
                    embedding_status=KnowledgeBaseEntry.EmbeddingStatus.FAILED
                ).count(),
            },
            'category_breakdown': dict(
                entries.exclude(category='')
                .values('category')
                .annotate(count=Count('id'))
                .values_list('category', 'count')
            ),
            'recent_entries': entries.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).count(),
            'bilingual_entries': entries.filter(
                issue_title_en__isnull=False,
                solution_en__isnull=False,
                issue_title_sv__isnull=False,
                solution_sv__isnull=False
            ).exclude(
                issue_title_en='',
                solution_en='',
                issue_title_sv='',
                solution_sv=''
            ).count()
        }

        return Response(stats)


@extend_schema(tags=["Knowledge Base"])
class KnowledgeBaseCategoriesView(generics.GenericAPIView):
    """Get available categories for knowledge base entries."""
    permission_classes = [IsAuthenticated]
    serializer_class = None

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        }
    )
    def get(self, request):
        """Get list of unique categories from user's entries."""
        user = request.user

        categories = (
            KnowledgeBaseEntry.objects.filter(created_by=user)
            .exclude(category='')
            .values_list('category', flat=True)
            .distinct()
            .order_by('category')
        )

        return Response({
            'categories': list(categories)
        })
