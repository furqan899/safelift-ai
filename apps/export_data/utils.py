"""
Utility functions for the export_data app.

Shared helpers for formatting, validation, and common operations.
"""

from typing import List
from .models import Export


def format_data_types_display(data_types: List[str]) -> str:
    """
    Format data types list as human-readable string.
    
    Args:
        data_types: List of data type codes
        
    Returns:
        Comma-separated display labels
    """
    if not data_types or not isinstance(data_types, list):
        return ""
    
    type_labels = []
    for dt in data_types:
        label = dict(Export.DataType.choices).get(dt, dt)
        type_labels.append(label)
    
    return ", ".join(type_labels)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "2.4 MB")
    """
    if size_bytes is None or size_bytes == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB"]
    size = float(size_bytes)
    
    for unit in units:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    
    return f"{size:.1f} TB"
