"""
URL configuration for Knowledge Base app.

Provides endpoints for:
- CRUD operations on bilingual entries
- Semantic search using embeddings
- Statistics and category management
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSet
router = DefaultRouter()
router.register(
    r'entries',
    views.KnowledgeBaseViewSet,
    basename='knowledge-base-entry'
)

# URL patterns
urlpatterns = [
    # ViewSet routes (CRUD operations)
    path('', include(router.urls)),

    # Search endpoint (POST /knowledge-base/search/)
    path(
        'search/',
        views.KnowledgeBaseSearchView.as_view(),
        name='knowledge-base-search'
    ),

    # Statistics endpoint (GET /knowledge-base/stats/)
    path(
        'stats/',
        views.KnowledgeBaseStatsView.as_view(),
        name='knowledge-base-stats'
    ),

    # Categories endpoint (GET /knowledge-base/categories/)
    path(
        'categories/',
        views.KnowledgeBaseCategoriesView.as_view(),
        name='knowledge-base-categories'
    ),
]
