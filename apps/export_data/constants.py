"""
Constants for the export_data app.

Central place for query params, limits, status values.
"""

# Query parameters
PARAM_STATUS = "status"
PARAM_FORMAT = "format"
PARAM_SORT = "sort"

# Date range validation
MAX_DATE_RANGE_DAYS = 365
MIN_DATE_RANGE_DAYS = 1
DEFAULT_DATE_RANGE_DAYS = 30

# Limits and constraints
MAX_EXPORTS_PER_USER = 100
EXPORT_FILE_RETENTION_DAYS = 30
MAX_EXPORT_FILE_SIZE = 500 * 1024 * 1024  # 500MB
PROGRESS_MIN = 0
PROGRESS_MAX = 100

# Status values
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

# Format values
FORMAT_CSV = "csv"
FORMAT_JSON = "json"
FORMAT_PDF = "pdf"

# Data types
DATA_TYPE_CONVERSATIONS = "conversations"
DATA_TYPE_KNOWLEDGE_BASE = "knowledge_base"
DATA_TYPE_ESCALATIONS = "escalations"
DATA_TYPE_ANALYTICS = "analytics"
