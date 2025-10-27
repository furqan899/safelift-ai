"""
Constants for the conversations app.

Following Clean Code principles: centralized configuration, meaningful names.
All magic numbers and string literals used across the conversations module.
"""


# ============================================================================
# Percentage and Calculation Constants
# ============================================================================

PERCENTAGE_BASE = 100.0
"""Base value for percentage calculations (100 for percentage)"""

DEFAULT_SUCCESS_RATE = 0.0
"""Default success rate when no conversations exist"""

PERCENTAGE_DECIMAL_PLACES = 2
"""Number of decimal places for percentage calculations"""


# ============================================================================
# Query Parameter Names
# ============================================================================

PARAM_LANGUAGE = 'language'
"""Query parameter name for filtering by language"""

PARAM_STATUS = 'status'
"""Query parameter name for filtering by status"""

PARAM_SESSION_ID = 'session_id'
"""Query parameter name for filtering by session ID"""

PARAM_SEARCH = 'search'
"""Query parameter name for text search"""


# ============================================================================
# Response Time Constants
# ============================================================================

MILLISECONDS_PER_SECOND = 1000
"""Conversion factor from milliseconds to seconds"""


# ============================================================================
# Error Messages
# ============================================================================

ERROR_ESCALATION_FAILED = "Failed to escalate conversation"
"""Error message when escalation fails"""

ERROR_RESOLUTION_FAILED = "Failed to resolve conversation"
"""Error message when resolution fails"""

ERROR_STATS_RETRIEVAL_FAILED = "Failed to retrieve statistics"
"""Error message when statistics retrieval fails"""

ERROR_CONVERSATIONS_RETRIEVAL_FAILED = "Failed to retrieve conversations"
"""Error message when conversations retrieval fails"""

ERROR_LOGS_RETRIEVAL_FAILED = "Failed to retrieve conversation logs"
"""Error message when logs retrieval fails"""

ERROR_LOG_UPDATE_FAILED = "Failed to update conversation log"
"""Error message when log update fails"""

ERROR_ENTRY_NOT_FOUND = "Conversation entry not found"
"""Error message when conversation not found"""

ERROR_SESSION_NOT_FOUND = "Session not found"
"""Error message when session not found"""


# ============================================================================
# Log Messages
# ============================================================================

LOG_CONVERSATION_ESCALATED = "Conversation {id} escalated: {reason}"
"""Log message template for escalated conversations"""

LOG_CONVERSATION_RESOLVED = "Conversation {id} resolved"
"""Log message template for resolved conversations"""

LOG_CONVERSATION_LOG_UPDATED = (
    "Updated conversation log for session {session_id} (created: {created})"
)
"""Log message template for log updates"""


# ============================================================================
# Validation Constants
# ============================================================================

MIN_SEARCH_QUERY_LENGTH = 1
"""Minimum length for search queries"""

MAX_SEARCH_QUERY_LENGTH = 1000
"""Maximum length for search queries"""


# ============================================================================
# Session Constants
# ============================================================================

SESSION_ID_PREFIX_LEGACY = "legacy_"
"""Prefix for legacy session IDs during migration"""
