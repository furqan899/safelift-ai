"""
Tests for KnowledgeBase views.
"""
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.knowledge_base.models import KnowledgeBaseEntry
from apps.users.models import User


class KnowledgeBaseViewSetTest(APITestCase):
    """Test cases for KnowledgeBaseViewSet."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123',
            role=User.Role.USER
        )
        
        # Create test entries
        self.entry1 = KnowledgeBaseEntry.objects.create(
            issue_title_en='Hydraulic Issue',
            solution_en='Hydraulic Solution',
            category='Hydraulics',
            created_by=self.user,
            status=KnowledgeBaseEntry.Status.ACTIVE
        )
        self.entry2 = KnowledgeBaseEntry.objects.create(
            issue_title_en='Brake Issue',
            solution_en='Brake Solution',
            category='Brakes',
            created_by=self.user,
            status=KnowledgeBaseEntry.Status.INACTIVE
        )
        
        self.list_url = reverse('knowledge-base-entry-list')

    def get_detail_url(self, entry_id):
        """Helper to get detail URL."""
        return reverse('knowledge-base-entry-detail', kwargs={'pk': entry_id})

    @patch('apps.knowledge_base.views.EmbeddingProcessor')
    def test_list_entries(self, mock_processor):
        """Test listing knowledge base entries."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    @patch('apps.knowledge_base.views.EmbeddingProcessor')
    def test_create_entry(self, mock_processor):
        """Test creating knowledge base entry."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'issue_title_en': 'New Issue',
            'solution_en': 'New Solution',
            'category': 'Engine'
        }
        response = self.client.post(self.list_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['issue_title_en'], 'New Issue')
        
        # Embedding processor should be triggered
        mock_processor.assert_called_once()

    def test_retrieve_entry(self):
        """Test retrieving knowledge base entry."""
        self.client.force_authenticate(user=self.user)
        url = self.get_detail_url(self.entry1.id)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['issue_title_en'], 'Hydraulic Issue')

    @patch('apps.knowledge_base.views.EmbeddingProcessor')
    def test_update_entry(self, mock_processor):
        """Test updating knowledge base entry."""
        self.client.force_authenticate(user=self.user)
        url = self.get_detail_url(self.entry1.id)
        
        data = {
            'issue_title_en': 'Updated Issue',
            'solution_en': 'Updated Solution',
            'category': 'Hydraulics'
        }
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['issue_title_en'], 'Updated Issue')

    def test_delete_entry(self):
        """Test deleting knowledge base entry."""
        self.client.force_authenticate(user=self.user)
        url = self.get_detail_url(self.entry1.id)
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(KnowledgeBaseEntry.objects.filter(id=self.entry1.id).exists())

    def test_filter_by_category(self):
        """Test filtering entries by category."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.list_url, {'category': 'Hydraulics'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        for entry in results:
            self.assertEqual(entry['category'], 'Hydraulics')

    def test_filter_by_status(self):
        """Test filtering entries by status."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.list_url, {'status': 'active'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        for entry in results:
            self.assertEqual(entry['status'], 'active')

    def test_filter_by_embedding_status(self):
        """Test filtering entries by embedding status."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.list_url, {'embedding_status': 'pending'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_by_title(self):
        """Test searching entries by title."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.list_url, {'search': 'Hydraulic'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_toggle_status_action(self):
        """Test toggle_status action switches status."""
        self.client.force_authenticate(user=self.user)
        url = reverse('knowledge-base-entry-toggle-status', kwargs={'pk': self.entry1.id})
        
        original_status = self.entry1.status
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data['status'], original_status)

    @patch('apps.knowledge_base.views.EmbeddingProcessor')
    def test_regenerate_embeddings_action(self, mock_processor):
        """Test regenerate_embeddings action."""
        self.client.force_authenticate(user=self.user)
        url = reverse('knowledge-base-entry-regenerate-embeddings', kwargs={'pk': self.entry1.id})
        
        # Mock successful processing
        mock_instance = MagicMock()
        mock_instance.process_entry.return_value = MagicMock(success=True, vector_ids=['id1', 'id2'])
        mock_processor.return_value = mock_instance
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_stats_view(self):
        """Test knowledge base stats view."""
        self.client.force_authenticate(user=self.user)
        url = reverse('knowledge-base-stats')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_entries', response.data)
        self.assertIn('active_entries', response.data)
        self.assertIn('inactive_entries', response.data)

    def test_categories_view(self):
        """Test knowledge base categories view."""
        self.client.force_authenticate(user=self.user)
        url = reverse('knowledge-base-categories')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('categories', response.data)
        self.assertIsInstance(response.data['categories'], list)


class KnowledgeBaseSearchViewTest(APITestCase):
    """Test cases for KnowledgeBaseSearchView."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )
        self.url = reverse('knowledge-base-search')

    @patch('apps.knowledge_base.views.EmbeddingService')
    def test_search_with_query(self, mock_service):
        """Test searching with query."""
        self.client.force_authenticate(user=self.user)
        
        # Mock search results
        mock_instance = MagicMock()
        mock_instance.search.return_value = []
        mock_service.return_value = mock_instance
        
        data = {
            'query': 'hydraulic problems',
            'top_k': 5
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    @patch('apps.knowledge_base.views.EmbeddingService')
    def test_search_with_language_filter(self, mock_service):
        """Test searching with language filter."""
        self.client.force_authenticate(user=self.user)
        
        mock_instance = MagicMock()
        mock_instance.search.return_value = []
        mock_service.return_value = mock_instance
        
        data = {
            'query': 'test query',
            'language': 'en',
            'top_k': 5
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('apps.knowledge_base.views.EmbeddingService')
    def test_search_with_category_filter(self, mock_service):
        """Test searching with category filter."""
        self.client.force_authenticate(user=self.user)
        
        mock_instance = MagicMock()
        mock_instance.search.return_value = []
        mock_service.return_value = mock_instance
        
        data = {
            'query': 'test query',
            'category': 'Hydraulics',
            'top_k': 5
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

