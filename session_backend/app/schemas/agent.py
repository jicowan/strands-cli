"""SessionAgent API schemas for request/response validation."""

import base64
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
import re


class SessionAgentCreate(BaseModel):
    """Schema for creating a new session agent."""
    
    agent_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique identifier for the agent within the session"
    )
    state: Dict[str, Any] = Field(
        ...,
        description="Agent state data in JSON format"
    )
    conversation_manager_state: Dict[str, Any] = Field(
        ...,
        description="Conversation manager state data in JSON format"
    )
    internal_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Internal agent state data in JSON format"
    )
    
    @validator('agent_id')
    def validate_agent_id(cls, v):
        """Validate agent ID format."""
        if not v or not v.strip():
            raise ValueError("Agent ID cannot be empty or whitespace")
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Agent ID can only contain alphanumeric characters, hyphens, and underscores")
        
        return v.strip()
    
    @validator('state', 'conversation_manager_state', 'internal_state')
    def validate_state_data(cls, v):
        """Validate state data and handle binary data encoding."""
        if not isinstance(v, dict):
            raise ValueError("State data must be a dictionary")
        
        # Process the state data to handle binary data encoding
        return cls._process_binary_data(v)
    
    @classmethod
    def _process_binary_data(cls, data: Any) -> Any:
        """Process data to encode binary data as base64."""
        if isinstance(data, bytes):
            # Encode binary data as base64
            return {
                "_type": "binary",
                "_data": base64.b64encode(data).decode('utf-8')
            }
        elif isinstance(data, dict):
            # Recursively process dictionary values
            return {k: cls._process_binary_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            # Recursively process list items
            return [cls._process_binary_data(item) for item in data]
        else:
            # Return other data types as-is
            return data
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            bytes: lambda v: base64.b64encode(v).decode('utf-8')
        }
        schema_extra = {
            "example": {
                "agent_id": "agent-1",
                "state": {
                    "tools": ["tool1", "tool2"],
                    "config": {"temperature": 0.7}
                },
                "conversation_manager_state": {
                    "history": [],
                    "context": "conversation context"
                },
                "internal_state": {
                    "memory": {},
                    "counters": {"messages": 0}
                }
            }
        }


class SessionAgentUpdate(BaseModel):
    """Schema for updating an existing session agent."""
    
    state: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated agent state data in JSON format"
    )
    conversation_manager_state: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated conversation manager state data in JSON format"
    )
    internal_state: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated internal agent state data in JSON format"
    )
    
    @validator('state', 'conversation_manager_state', 'internal_state')
    def validate_state_data(cls, v):
        """Validate state data and handle binary data encoding."""
        if v is not None and not isinstance(v, dict):
            raise ValueError("State data must be a dictionary")
        
        if v is not None:
            # Process the state data to handle binary data encoding
            return SessionAgentCreate._process_binary_data(v)
        
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            bytes: lambda v: base64.b64encode(v).decode('utf-8')
        }
        schema_extra = {
            "example": {
                "state": {
                    "tools": ["tool1", "tool2", "tool3"],
                    "config": {"temperature": 0.8}
                },
                "internal_state": {
                    "memory": {"key": "value"},
                    "counters": {"messages": 5}
                }
            }
        }


class SessionAgentResponse(BaseModel):
    """Schema for session agent response data."""
    
    agent_id: str = Field(
        ...,
        description="Unique identifier for the agent within the session"
    )
    state: Dict[str, Any] = Field(
        ...,
        description="Agent state data in JSON format"
    )
    conversation_manager_state: Dict[str, Any] = Field(
        ...,
        description="Conversation manager state data in JSON format"
    )
    internal_state: Dict[str, Any] = Field(
        ...,
        description="Internal agent state data in JSON format"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the agent was created"
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the agent was last updated"
    )
    
    @validator('state', 'conversation_manager_state', 'internal_state')
    def decode_binary_data(cls, v):
        """Decode binary data from base64."""
        return cls._decode_binary_data(v)
    
    @classmethod
    def _decode_binary_data(cls, data: Any) -> Any:
        """Process data to decode base64-encoded binary data."""
        if isinstance(data, dict):
            if data.get("_type") == "binary" and "_data" in data:
                # Decode base64 binary data
                try:
                    return base64.b64decode(data["_data"])
                except Exception as e:
                    raise ValueError(f"Invalid base64 data: {e}")
            else:
                # Recursively process dictionary values
                return {k: cls._decode_binary_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            # Recursively process list items
            return [cls._decode_binary_data(item) for item in data]
        else:
            # Return other data types as-is
            return data
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            bytes: lambda v: base64.b64encode(v).decode('utf-8')
        }
        schema_extra = {
            "example": {
                "agent_id": "agent-1",
                "state": {
                    "tools": ["tool1", "tool2"],
                    "config": {"temperature": 0.7}
                },
                "conversation_manager_state": {
                    "history": [],
                    "context": "conversation context"
                },
                "internal_state": {
                    "memory": {},
                    "counters": {"messages": 0}
                },
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }


class SessionAgentListResponse(BaseModel):
    """Schema for paginated session agent list response."""
    
    agents: List[SessionAgentResponse] = Field(
        ...,
        description="List of session agents"
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of agents"
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
                "agents": [
                    {
                        "agent_id": "agent-1",
                        "state": {"tools": ["tool1"]},
                        "conversation_manager_state": {"history": []},
                        "internal_state": {"memory": {}},
                        "created_at": "2024-01-01T12:00:00Z",
                        "updated_at": "2024-01-01T12:00:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10
            }
        }