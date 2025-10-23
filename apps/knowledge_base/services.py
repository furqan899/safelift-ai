"""
Service layer for knowledge base entry processing and embedding generation.

Follows Clean Code principles:
- Single Responsibility Principle
- Small, focused functions
- Clear naming
- Proper error handling
"""
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from django.conf import settings
from django.utils import timezone

# AI imports
try:
    from langchain_openai import OpenAIEmbeddings
    from pinecone import Pinecone
    SERVICES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Required libraries not available: {e}")
    SERVICES_AVAILABLE = False

from .models import KnowledgeBaseEntry
from .utils import (
    build_embedding_metadata,
    EMBEDDING_MODEL,
    DEFAULT_SEARCH_TOP_K
)

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Data class for search results."""
    entry_id: str
    score: float
    content: Optional[str]
    language: str
    category: str
    metadata: Dict[str, Any]


@dataclass
class EmbeddingResult:
    """Data class for embedding generation results."""
    success: bool
    vector_ids: List[str]
    error_message: Optional[str] = None


class EmbeddingProcessor:
    """
    Processes knowledge base entries and generates embeddings.
    
    Responsibilities:
    - Generate embeddings for bilingual content
    - Update entry status
    - Handle errors gracefully
    """

    def __init__(self, entry_id: str):
        """Initialize with entry ID."""
        self.entry_id = entry_id
        self.entry = None

    def _get_entry(self) -> Optional[KnowledgeBaseEntry]:
        """Retrieve entry from database."""
        try:
            self.entry = KnowledgeBaseEntry.objects.get(id=self.entry_id)
            return self.entry
        except KnowledgeBaseEntry.DoesNotExist:
            logger.error(f"Entry {self.entry_id} not found")
            return None

    def _update_status(self, status: str) -> None:
        """Update entry embedding status."""
        if self.entry:
            self.entry.embedding_status = status
            self.entry.save(update_fields=['embedding_status'])

    def _mark_processing_complete(self, vector_ids: List[str]) -> None:
        """Mark entry as successfully processed."""
        if self.entry:
            self.entry.pinecone_vector_ids = vector_ids
            self.entry.embedding_status = KnowledgeBaseEntry.EmbeddingStatus.COMPLETED
            self.entry.processed_at = timezone.now()
            self.entry.save(update_fields=[
                'pinecone_vector_ids',
                'embedding_status',
                'processed_at'
            ])

    def process_entry(self) -> EmbeddingResult:
        """
        Process entry and generate embeddings for both languages.
        
        Returns:
            EmbeddingResult with success status and vector IDs
        """
        try:
            if not self._get_entry():
                return EmbeddingResult(
                    success=False,
                    vector_ids=[],
                    error_message="Entry not found"
                )

            self._update_status(KnowledgeBaseEntry.EmbeddingStatus.PROCESSING)

            embedding_service = EmbeddingService()
            result = embedding_service.generate_and_store_embeddings(self.entry)

            if result.success:
                self._mark_processing_complete(result.vector_ids)
                logger.info(
                    f"Entry {self.entry_id} processed successfully. "
                    f"Generated {len(result.vector_ids)} embeddings"
                )
            else:
                self._update_status(KnowledgeBaseEntry.EmbeddingStatus.FAILED)
                logger.error(
                    f"Failed to process entry {self.entry_id}: "
                    f"{result.error_message}"
                )

            return result

        except Exception as e:
            error_msg = f"Error processing entry {self.entry_id}: {str(e)}"
            logger.error(error_msg)
            self._update_status(KnowledgeBaseEntry.EmbeddingStatus.FAILED)
            return EmbeddingResult(
                success=False,
                vector_ids=[],
                error_message=str(e)
            )


class EmbeddingService:
    """
    Service for generating and searching embeddings using OpenAI and Pinecone.
    
    Responsibilities:
    - Initialize embedding and vector store connections
    - Generate embeddings for text content
    - Store embeddings in Pinecone
    - Search for similar content
    """

    def __init__(self):
        """Initialize the embedding service."""
        self.embeddings = None
        self.vector_store = None
        self.pinecone_client = None
        self._initialize_services()

    def _initialize_services(self) -> None:
        """Initialize OpenAI embeddings and Pinecone."""
        if not SERVICES_AVAILABLE:
            logger.warning("Required services not available")
            return

        self._initialize_embeddings()
        self._initialize_pinecone()

    def _initialize_embeddings(self) -> None:
        """Initialize OpenAI embeddings."""
        try:
            if not settings.OPENAI_API_KEY:
                logger.error("OpenAI API key not configured")
                self.embeddings = None
                return

            # Initialize with explicit parameters to avoid version compatibility issues
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY,
                model=EMBEDDING_MODEL
            )
            logger.info("OpenAI embeddings initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI embeddings: {str(e)}")
            logger.error(f"OpenAI API key configured: {bool(settings.OPENAI_API_KEY)}")
            self.embeddings = None

    def _initialize_pinecone(self) -> None:
        """Initialize Pinecone index."""
        try:
            if not settings.PINECONE_API_KEY:
                logger.error("Pinecone API key not configured")
                return

            self.pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
            self.vector_store = self.pinecone_client.Index(settings.PINECONE_INDEX_NAME)
            logger.info("Pinecone initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {str(e)}")
            self.vector_store = None

    def _create_vector_data(
        self,
        entry: KnowledgeBaseEntry,
        language: str
    ) -> tuple:
        """Create vector data for a specific language."""
        content = (
            entry.get_combined_content_en() if language == 'en'
            else entry.get_combined_content_sv()
        )
        
        metadata = build_embedding_metadata(
            entry_id=str(entry.id),
            language=language,
            category=entry.category,
            created_by_id=str(entry.created_by.id),
            additional_metadata={
                'status': entry.status,
                'tags': entry.tags
            }
        )
        
        return content, metadata

    def generate_and_store_embeddings(
        self,
        entry: KnowledgeBaseEntry
    ) -> EmbeddingResult:
        """
        Generate and store embeddings for both languages.
        
        Args:
            entry: Knowledge base entry to process
            
        Returns:
            EmbeddingResult with success status and vector IDs
        """
        if not self.vector_store or not self.embeddings:
            error_details = []
            if not self.embeddings:
                error_details.append("OpenAI embeddings not initialized")
            if not self.vector_store:
                error_details.append("Pinecone not initialized")

            return EmbeddingResult(
                success=False,
                vector_ids=[],
                error_message=f"Services not available: {'; '.join(error_details)}"
            )

        try:
            vectors = []
            
            # Process English content
            if entry.issue_title_en and entry.solution_en:
                content, metadata = self._create_vector_data(entry, 'en')
                embedding = self.embeddings.embed_query(content)
                vector_id = f"{entry.id}_en"
                vectors.append((vector_id, embedding, metadata))
            
            # Process Swedish content
            if entry.issue_title_sv and entry.solution_sv:
                content, metadata = self._create_vector_data(entry, 'sv')
                embedding = self.embeddings.embed_query(content)
                vector_id = f"{entry.id}_sv"
                vectors.append((vector_id, embedding, metadata))

            if not vectors:
                return EmbeddingResult(
                    success=False,
                    vector_ids=[],
                    error_message="No content to process"
                )

            # Upsert to Pinecone
            self.vector_store.upsert(vectors=vectors)
            vector_ids = [v[0] for v in vectors]
            
            logger.info(f"Stored {len(vector_ids)} embeddings for entry {entry.id}")
            
            return EmbeddingResult(
                success=True,
                vector_ids=vector_ids
            )

        except Exception as e:
            error_msg = f"Error storing embeddings: {str(e)}"
            logger.error(error_msg)
            return EmbeddingResult(
                success=False,
                vector_ids=[],
                error_message=error_msg
            )

    def search(
        self,
        query: str,
        language: Optional[str] = None,
        category: Optional[str] = None,
        top_k: int = DEFAULT_SEARCH_TOP_K,
        include_content: bool = True
    ) -> List[SearchResult]:
        """
        Search for similar entries using vector similarity.
        
        Args:
            query: Search query text
            language: Filter by language (en/sv)
            category: Filter by category
            top_k: Number of results to return
            include_content: Whether to include full content in results
            
        Returns:
            List of SearchResult objects
        """
        if not self.vector_store or not self.embeddings:
            logger.warning("Search services not available")
            return []

        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Build filter
            filter_dict = {}
            if language:
                filter_dict['language'] = language
            if category:
                filter_dict['category'] = category

            # Query Pinecone
            results = self.vector_store.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter_dict if filter_dict else None,
                include_metadata=True
            )

            # Format results
            return [
                SearchResult(
                    entry_id=match['metadata'].get('entry_id', ''),
                    score=float(match['score']),
                    content=match['metadata'].get('text') if include_content else None,
                    language=match['metadata'].get('language', ''),
                    category=match['metadata'].get('category', ''),
                    metadata=match['metadata']
                )
                for match in results['matches']
            ]

        except Exception as e:
            logger.error(f"Error searching entries: {str(e)}")
            return []

    def delete_entry_embeddings(self, vector_ids: List[str]) -> bool:
        """
        Delete embeddings for an entry.
        
        Args:
            vector_ids: List of Pinecone vector IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.vector_store or not vector_ids:
            return False

        try:
            self.vector_store.delete(ids=vector_ids)
            logger.info(f"Deleted {len(vector_ids)} embeddings")
            return True
        except Exception as e:
            logger.error(f"Error deleting embeddings: {str(e)}")
            return False
