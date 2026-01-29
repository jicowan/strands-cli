"""Pydantic models for the test-session-agent API."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class PromptRequest(BaseModel):
    """Request model for agent prompts."""

    prompt: str
    """The prompt to send to the agent."""

    session_id: Optional[str] = None
    """Optional session ID for conversation persistence."""

    metadata: Optional[Dict[str, Any]] = None
    """Optional metadata to include with the request."""


class SessionResponse(BaseModel):
    """Response model for session information."""
    
    session_id: str
    """The session ID used for this conversation."""
    
    response: str
    """The agent's response."""