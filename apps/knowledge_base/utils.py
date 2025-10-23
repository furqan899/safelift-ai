"""
Utility functions for the knowledge base app.

Following Clean Code principles: DRY, single responsibility, clear naming.
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


# Constants
BYTES_IN_KB = 1024
BYTES_IN_MB = BYTES_IN_KB * 1024
BYTES_IN_GB = BYTES_IN_MB * 1024
BYTES_IN_TB = BYTES_IN_GB * 1024

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_SEARCH_TOP_K = 5
MAX_SEARCH_TOP_K = 20

EMBEDDING_MODEL = "text-embedding-ada-002"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if size_bytes < BYTES_IN_KB:
        return f"{size_bytes} B"
    elif size_bytes < BYTES_IN_MB:
        return f"{size_bytes / BYTES_IN_KB:.1f} KB"
    elif size_bytes < BYTES_IN_GB:
        return f"{size_bytes / BYTES_IN_MB:.1f} MB"
    elif size_bytes < BYTES_IN_TB:
        return f"{size_bytes / BYTES_IN_GB:.1f} GB"
    else:
        return f"{size_bytes / BYTES_IN_TB:.1f} TB"


def build_embedding_metadata(
    entry_id: str,
    language: str,
    category: str,
    created_by_id: str,
    additional_metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Build standardized metadata for Pinecone embeddings.
    
    Args:
        entry_id: Knowledge base entry ID
        language: Language code (en/sv)
        category: Entry category
        created_by_id: User ID who created the entry
        additional_metadata: Optional additional metadata
        
    Returns:
        Dictionary containing metadata
    """
    metadata = {
        'entry_id': entry_id,
        'language': language,
        'category': category,
        'created_by': created_by_id,
    }
    
    if additional_metadata:
        metadata.update(additional_metadata)
    
    return metadata


def sanitize_search_query(query: str, max_length: int = 1000) -> str:
    """
    Sanitize and validate search query.
    
    Args:
        query: Raw search query
        max_length: Maximum allowed query length
        
    Returns:
        Sanitized query string
    """
    if not query:
        return ""
    
    # Strip whitespace and limit length
    sanitized = query.strip()[:max_length]
    
    return sanitized


def get_language_display_name(language_code: str) -> str:
    """
    Get display name for language code.
    
    Args:
        language_code: Language code (en/sv)
        
    Returns:
        Display name (English/Swedish)
    """
    language_map = {
        'en': 'English',
        'sv': 'Swedish'
    }
    return language_map.get(language_code.lower(), 'Unknown')

