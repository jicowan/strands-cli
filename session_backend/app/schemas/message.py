"""SessionMessage API schemas for request/response validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


class SessionMessageCreate(BaseModel):
    """Schema for creating a new session message."""
    
    message_id: int = Field(
        ...,
        ge=0,
        description="Unique identifier for the message within the agent's conversation"
    )
    message: Dict[str, Any] = Field(
        ...,
        description="Message data in Strands Message format"
    )
    redact_message: Optional[Dict[str, Any]] = Field(
        None,
        description="Redacted version of the message for privacy/security"
    )
    
    @validator('message')
    def validate_message_format(cls, v):
        """Validate message follows basic Strands message format."""
        if not isinstance(v, dict):
            raise ValueError("Message must be a dictionary")
        
        # Basic validation for Strands message format
        # Messages should have at least a role and content
        if 'role' not in v:
            raise ValueError("Message must contain 'role' field")
        
        if 'content' not in v:
            raise ValueError("Message must contain 'content' field")
        
        # Validate role is a string
        if not isinstance(v['role'], str):
            raise ValueError("Message 'role' must be a string")
        
        # Validate common roles
        valid_roles = {'user', 'assistant', 'system', 'tool', 'function'}
        if v['role'] not in valid_roles:
            # Allow other roles but warn in logs (this is just validation, not logging)
            pass
        
        return v
    
    @validator('redact_message')
    def validate_redact_message_format(cls, v):
        """Validate redacted message format if provided."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("Redacted message must be a dictionary")
            
            # Should have same basic structure as message
            if 'role' not in v:
                raise ValueError("Redacted message must contain 'role' field")
            
            if 'content' not in v:
                raise ValueError("Redacted message must contain 'content' field")
        
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "message_id": 1,
                "message": {
                    "role": "user",
                    "content": "Hello, how can you help me?",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "metadata": {
                        "source": "web_ui",
                        "session_id": "session-123"
                    }
                },
                "redact_message": {
                    "role": "user",
                    "content": "[REDACTED]",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "metadata": {
                        "source": "web_ui",
                        "session_id": "session-123"
                    }
                }
            }
        }


class SessionMessageUpdate(BaseModel):
    """Schema for updating an existing session message."""
    
    message: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated message data in Strands Message format"
    )
    redact_message: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated redacted version of the message"
    )
    
    @validator('message')
    def validate_message_format(cls, v):
        """Validate message follows basic Strands message format."""
        if v is not None:
            return SessionMessageCreate.__validators__['validate_message_format'](cls, v)
        return v
    
    @validator('redact_message')
    def validate_redact_message_format(cls, v):
        """Validate redacted message format if provided."""
        if v is not None:
            return SessionMessageCreate.__validators__['validate_redact_message_format'](cls, v)
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "message": {
                    "role": "user",
                    "content": "Updated message content",
                    "timestamp": "2024-01-01T12:05:00Z",
                    "metadata": {
                        "source": "web_ui",
                        "session_id": "session-123",
                        "edited": True
                    }
                }
            }
        }


class SessionMessageResponse(BaseModel):
    """Schema for session message response data."""
    
    message_id: int = Field(
        ...,
        description="Unique identifier for the message within the agent's conversation"
    )
    message: Dict[str, Any] = Field(
        ...,
        description="Message data in Strands Message format"
    )
    redact_message: Optional[Dict[str, Any]] = Field(
        None,
        description="Redacted version of the message for privacy/security"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the message was created"
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the message was last updated"
    )
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "message_id": 1,
                "message": {
                    "role": "user",
                    "content": "Hello, how can you help me?",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "metadata": {
                        "source": "web_ui",
                        "session_id": "session-123"
                    }
                },
                "redact_message": None,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }


class SessionMessageListResponse(BaseModel):
    """Schema for paginated session message list response."""
    
    messages: List[SessionMessageResponse] = Field(
        ...,
        description="List of session messages in chronological order"
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of messages"
    )
    page: int = Field(
        ...,
        ge=1,
        description="Current page number"
    )
    page_size: int = Field(
        ...,
        ge=1,
        le=1000,
        description="Number of items per page"
    )
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "messages": [
                    {
                        "message_id": 1,
                        "message": {
                            "role": "user",
                            "content": "Hello!",
                            "timestamp": "2024-01-01T12:00:00Z"
                        },
                        "redact_message": None,
                        "created_at": "2024-01-01T12:00:00Z",
                        "updated_at": "2024-01-01T12:00:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10
            }
        }


class MessagePaginationQuery(BaseModel):
    """Schema for message pagination query parameters."""
    
    page: int = Field(
        1,
        ge=1,
        description="Page number (1-based)"
    )
    page_size: int = Field(
        10,
        ge=1,
        le=1000,
        description="Number of messages per page"
    )
    order: str = Field(
        "asc",
        pattern="^(asc|desc)$",
        description="Sort order: 'asc' for chronological, 'desc' for reverse chronological"
    )
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "page": 1,
                "page_size": 50,
                "order": "asc"
            }
        }