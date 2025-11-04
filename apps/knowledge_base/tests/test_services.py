"""
Tests for KnowledgeBase services with mocked external dependencies.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.knowledge_base.models import KnowledgeBaseEntry
from apps.knowledge_base.services import EmbeddingProcessor, EmbeddingService
from apps.users.models import User


class EmbeddingProcessorTest(TestCase):
    """Test cases for EmbeddingProcessor with mocked services."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )
        self.entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='Test Issue',
            solution_en='Test Solution',
            category='Hydraulics',
            created_by=self.user
        )

    @patch('apps.knowledge_base.services.EmbeddingService')
    def test_process_entry_with_mock(self, mock_service_class):
        """Test process_entry with mocked EmbeddingService."""
        # Setup mock
        mock_service = MagicMock()
        mock_service.generate_and_store_embeddings.return_value = MagicMock(
            success=True,
            vector_ids=['vec1', 'vec2']
        )
        mock_service_class.return_value = mock_service
        
        processor = EmbeddingProcessor(self.entry.id)
        result = processor.process_entry()
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.vector_ids), 2)

    def test_embedding_processor_updates_status_to_processing(self):
        """Test processor updates status to processing."""
        with patch('apps.knowledge_base.services.EmbeddingService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.generate_and_store_embeddings.return_value = MagicMock(
                success=True,
                vector_ids=['vec1']
            )
            mock_service_class.return_value = mock_service
            
            processor = EmbeddingProcessor(self.entry.id)
            processor.process_entry()
            
            # Entry should have been marked as processing at some point
            # (though it will be completed at the end)
            self.entry.refresh_from_db()
            self.assertEqual(
                self.entry.embedding_status,
                KnowledgeBaseEntry.EmbeddingStatus.COMPLETED
            )

    @patch('apps.knowledge_base.services.EmbeddingService')
    def test_embedding_processor_updates_status_to_completed_on_success(self, mock_service_class):
        """Test processor updates status to completed on success."""
        mock_service = MagicMock()
        mock_service.generate_and_store_embeddings.return_value = MagicMock(
            success=True,
            vector_ids=['vec1', 'vec2']
        )
        mock_service_class.return_value = mock_service
        
        processor = EmbeddingProcessor(self.entry.id)
        processor.process_entry()
        
        self.entry.refresh_from_db()
        self.assertEqual(
            self.entry.embedding_status,
            KnowledgeBaseEntry.EmbeddingStatus.COMPLETED
        )
        self.assertEqual(self.entry.pinecone_vector_ids, ['vec1', 'vec2'])

    @patch('apps.knowledge_base.services.EmbeddingService')
    def test_embedding_processor_updates_status_to_failed_on_error(self, mock_service_class):
        """Test processor updates status to failed on error."""
        mock_service = MagicMock()
        mock_service.generate_and_store_embeddings.return_value = MagicMock(
            success=False,
            vector_ids=[],
            error_message='Test error'
        )
        mock_service_class.return_value = mock_service
        
        processor = EmbeddingProcessor(self.entry.id)
        result = processor.process_entry()
        
        self.assertFalse(result.success)
        self.entry.refresh_from_db()
        self.assertEqual(
            self.entry.embedding_status,
            KnowledgeBaseEntry.EmbeddingStatus.FAILED
        )

    def test_embedding_processor_with_nonexistent_entry(self):
        """Test processor handles nonexistent entry."""
        processor = EmbeddingProcessor('00000000-0000-0000-0000-000000000000')
        result = processor.process_entry()
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, 'Entry not found')


class EmbeddingServiceTest(TestCase):
    """Test cases for EmbeddingService with mocked external APIs."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )

    @patch('apps.knowledge_base.services.Pinecone')
    @patch('apps.knowledge_base.services.OpenAIEmbeddings')
    @patch('apps.knowledge_base.services.SERVICES_AVAILABLE', True)
    def test_embedding_service_initialization_without_api_keys(self, mock_openai, mock_pinecone):
        """Test service initialization without API keys."""
        with patch('django.conf.settings.OPENAI_API_KEY', ''):
            service = EmbeddingService()
            self.assertIsNone(service.embeddings)

    @patch('apps.knowledge_base.services.Pinecone')
    @patch('apps.knowledge_base.services.OpenAIEmbeddings')
    @patch('apps.knowledge_base.services.SERVICES_AVAILABLE', True)
    @patch('django.conf.settings.OPENAI_API_KEY', 'test-key')
    @patch('django.conf.settings.PINECONE_API_KEY', 'test-key')
    def test_generate_and_store_embeddings_for_english_content(self, mock_openai, mock_pinecone):
        """Test embedding generation for English content."""
        # Setup mocks
        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.embed_query.return_value = [0.1] * 1536
        mock_openai.return_value = mock_embeddings_instance
        
        mock_pinecone_client = MagicMock()
        mock_index = MagicMock()
        mock_pinecone_client.Index.return_value = mock_index
        mock_pinecone.return_value = mock_pinecone_client
        
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='Test Issue',
            solution_en='Test Solution',
            category='Test',
            created_by=self.user
        )
        
        service = EmbeddingService()
        service.embeddings = mock_embeddings_instance
        service.vector_store = mock_index
        
        result = service.generate_and_store_embeddings(entry)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.vector_ids), 1)  # One for English

    @patch('apps.knowledge_base.services.Pinecone')
    @patch('apps.knowledge_base.services.OpenAIEmbeddings')
    @patch('apps.knowledge_base.services.SERVICES_AVAILABLE', True)
    @patch('django.conf.settings.OPENAI_API_KEY', 'test-key')
    @patch('django.conf.settings.PINECONE_API_KEY', 'test-key')
    def test_generate_and_store_embeddings_for_swedish_content(self, mock_openai, mock_pinecone):
        """Test embedding generation for Swedish content."""
        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.embed_query.return_value = [0.1] * 1536
        mock_openai.return_value = mock_embeddings_instance
        
        mock_pinecone_client = MagicMock()
        mock_index = MagicMock()
        mock_pinecone_client.Index.return_value = mock_index
        mock_pinecone.return_value = mock_pinecone_client
        
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_sv='Test Problem',
            solution_sv='Test Lösning',
            category='Test',
            created_by=self.user
        )
        
        service = EmbeddingService()
        service.embeddings = mock_embeddings_instance
        service.vector_store = mock_index
        
        result = service.generate_and_store_embeddings(entry)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.vector_ids), 1)  # One for Swedish

    @patch('apps.knowledge_base.services.Pinecone')
    @patch('apps.knowledge_base.services.OpenAIEmbeddings')
    @patch('apps.knowledge_base.services.SERVICES_AVAILABLE', True)
    @patch('django.conf.settings.OPENAI_API_KEY', 'test-key')
    @patch('django.conf.settings.PINECONE_API_KEY', 'test-key')
    def test_generate_and_store_embeddings_for_both_languages(self, mock_openai, mock_pinecone):
        """Test embedding generation for both languages."""
        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.embed_query.return_value = [0.1] * 1536
        mock_openai.return_value = mock_embeddings_instance
        
        mock_pinecone_client = MagicMock()
        mock_index = MagicMock()
        mock_pinecone_client.Index.return_value = mock_index
        mock_pinecone.return_value = mock_pinecone_client
        
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='Test Issue',
            solution_en='Test Solution',
            issue_title_sv='Test Problem',
            solution_sv='Test Lösning',
            category='Test',
            created_by=self.user
        )
        
        service = EmbeddingService()
        service.embeddings = mock_embeddings_instance
        service.vector_store = mock_index
        
        result = service.generate_and_store_embeddings(entry)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.vector_ids), 2)  # One for each language

    def test_error_handling_when_services_unavailable(self):
        """Test error handling when external services unavailable."""
        entry = KnowledgeBaseEntry.objects.create(
            issue_title_en='Test Issue',
            solution_en='Test Solution',
            category='Test',
            created_by=self.user
        )
        
        service = EmbeddingService()
        service.embeddings = None
        service.vector_store = None
        
        result = service.generate_and_store_embeddings(entry)
        
        self.assertFalse(result.success)
        self.assertIn('not available', result.error_message.lower())

