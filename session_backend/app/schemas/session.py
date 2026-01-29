"""Session API schemas for request/response validation - Strands compatible."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum
import re


class SessionType(str, Enum):
    """Session type enumeration matching Strands SessionType."""
    AGENT = "AGENT"


class SessionCreate(BaseModel):
    """Schema for creating a new session - matches Strands Session format."""
    
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique identifier for the session"
    )
    session_type: SessionType = Field(
        default=SessionType.AGENT,
        description="Type of session (AGENT for single agent sessions)"
    )
    created_at: Optional[str] = Field(
        None,
        description="ISO timestamp when session was created"
    )
    updated_at: Optional[str] = Field(
        None,
        description="ISO timestamp when session was last updated"
    )
    
    @validator('session_id')
    def validate_session_id(cls, v):
        """Validate session ID format."""
        if not v or not v.strip():
            raise ValueError("Session ID cannot be empty or whitespace")
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Session ID can only contain alphanumeric characters, hyphens, and underscores")
        
        return v.strip()
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "session_type": "AGENT"
            }
        }


class SessionUpdate(BaseModel):
    """Schema for updating an existing session."""
    
    session_type: Optional[SessionType] = Field(
        None,
        description="Updated session type"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "session_type": "AGENT"
            }
        }


class SessionResponse(BaseModel):
    """Schema for session response data - matches Strands Session format."""
    
    session_id: str = Field(
        ...,
        description="Unique identifier for the session"
    )
    session_type: SessionType = Field(
        ...,
        description="Type of session"
    )
    created_at: str = Field(
        ...,
        description="ISO timestamp when the session was created"
    )
    updated_at: str = Field(
        ...,
        description="ISO timestamp when the session was last updated"
    )
    
    @validator('created_at', 'updated_at', pre=True)
    def convert_datetime_to_string(cls, v):
        """Convert datetime objects to ISO format strings."""
        if isinstance(v, datetime):
            return v.isoformat()
        return v
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "session_type": "AGENT",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }


class SessionListResponse(BaseModel):
    """Schema for paginated session list response."""
    
    sessions: List[SessionResponse] = Field(
        ...,
        description="List of sessions"
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of sessions"
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
                "sessions": [
                    {
                        "session_id": "session-123",
                        "session_type": "AGENT",
                        "created_at": "2024-01-01T12:00:00Z",
                        "updated_at": "2024-01-01T12:00:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10
            }
        }