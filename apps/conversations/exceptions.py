"""
Custom exceptions for the conversations app.

Following Clean Code principles: specific, meaningful exceptions.
Each exception represents a specific error condition in conversation operations.
"""

from typing import Optional


class ConversationError(Exception):
    """
    Base exception for all conversation-related errors.
    
    All conversation exceptions should inherit from this class.
    """
    
    def __init__(self, message: str, details: Optional[str] = None):
        """
        Initialize conversation error.
        
        Args:
            message: Human-readable error message
            details: Optional additional details about the error
        """
        self.message = message
        self.details = details
        super().__init__(self.message)


class ConversationNotFoundError(ConversationError):
    """
    Exception raised when a conversation is not found.
    
    Raised when attempting to retrieve, update, or delete a conversation
    that doesn't exist.
    """
    
    def __init__(self, conversation_id: int, details: Optional[str] = None):
        """
        Initialize not found error.
        
        Args:
            conversation_id: ID of the conversation that was not found
            details: Optional additional details
        """
        message = f"Conversation with ID {conversation_id} not found"
        super().__init__(message, details)
        self.conversation_id = conversation_id


class SessionNotFoundError(ConversationError):
    """
    Exception raised when a session is not found.
    
    Raised when attempting to retrieve session logs for a session
    that doesn't exist.
    """
    
    def __init__(self, session_id: str, details: Optional[str] = None):
        """
        Initialize session not found error.
        
        Args:
            session_id: ID of the session that was not found
            details: Optional additional details
        """
        message = f"Session with ID {session_id} not found"
        super().__init__(message, details)
        self.session_id = session_id


class ConversationActionError(ConversationError):
    """
    Base exception for conversation action errors.
    
    Used for errors that occur during conversation state changes
    (escalate, resolve, etc.).
    """
    
    def __init__(self, action: str, conversation_id: int, message: str):
        """
        Initialize action error.
        
        Args:
            action: Name of the action that failed
            conversation_id: ID of the conversation
            message: Error message
        """
        super().__init__(message)
        self.action = action
        self.conversation_id = conversation_id


class ConversationEscalationError(ConversationActionError):
    """
    Exception raised when escalating a conversation fails.
    
    Can occur due to invalid state, missing permissions, or database errors.
    """
    
    def __init__(self, conversation_id: int, reason: str, details: Optional[str] = None):
        """
        Initialize escalation error.
        
        Args:
            conversation_id: ID of the conversation
            reason: Escalation reason provided
            details: Optional additional error details
        """
        message = f"Failed to escalate conversation {conversation_id} with reason: {reason}"
        super().__init__("escalate", conversation_id, message)
        self.reason = reason
        self.details = details


class ConversationResolutionError(ConversationActionError):
    """
    Exception raised when resolving a conversation fails.
    
    Can occur due to invalid state, missing permissions, or database errors.
    """
    
    def __init__(self, conversation_id: int, details: Optional[str] = None):
        """
        Initialize resolution error.
        
        Args:
            conversation_id: ID of the conversation
            details: Optional additional error details
        """
        message = f"Failed to resolve conversation {conversation_id}"
        super().__init__("resolve", conversation_id, message)
        self.details = details


class ConversationStatsError(ConversationError):
    """
    Exception raised when calculating conversation statistics fails.
    
    Can occur due to database errors or invalid query parameters.
    """
    
    def __init__(self, details: Optional[str] = None):
        """
        Initialize stats error.
        
        Args:
            details: Optional additional error details
        """
        message = "Failed to calculate conversation statistics"
        super().__init__(message, details)


class ConversationLogUpdateError(ConversationError):
    """
    Exception raised when updating conversation logs fails.
    
    Can occur during session log aggregation or database operations.
    """
    
    def __init__(self, session_id: str, details: Optional[str] = None):
        """
        Initialize log update error.
        
        Args:
            session_id: ID of the session being updated
            details: Optional additional error details
        """
        message = f"Failed to update conversation log for session {session_id}"
        super().__init__(message, details)
        self.session_id = session_id


class ConversationValidationError(ConversationError):
    """
    Exception raised when conversation data validation fails.
    
    Used for invalid input data, missing required fields, etc.
    """
    
    def __init__(self, field: Optional[str] = None, details: Optional[str] = None):
        """
        Initialize validation error.
        
        Args:
            field: Name of the field that failed validation
            details: Optional additional error details
        """
        if field:
            message = f"Validation failed for field: {field}"
        else:
            message = "Conversation validation failed"
        super().__init__(message, details)
        self.field = field


class ConversationPermissionError(ConversationError):
    """
    Exception raised when user lacks permission for conversation operation.
    
    Used for access control violations.
    """
    
    def __init__(
        self,
        operation: str,
        user: Optional[str] = None,
        details: Optional[str] = None
    ):
        """
        Initialize permission error.
        
        Args:
            operation: Name of the operation attempted
            user: Username of the user who attempted the operation
            details: Optional additional error details
        """
        if user:
            message = f"User {user} lacks permission for operation: {operation}"
        else:
            message = f"Permission denied for operation: {operation}"
        super().__init__(message, details)
        self.operation = operation
        self.user = user

