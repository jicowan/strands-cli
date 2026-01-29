"""API schemas package."""

from .session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,
)
from .agent import (
    SessionAgentCreate,
    SessionAgentUpdate,
    SessionAgentResponse,
    SessionAgentListResponse,
)
from .message import (
    SessionMessageCreate,
    SessionMessageUpdate,
    SessionMessageResponse,
    SessionMessageListResponse,
    MessagePaginationQuery,
)
from .common import (
    ErrorResponse,
    HealthResponse,
    PaginationQuery,
)

__all__ = [
    # Session schemas
    "SessionCreate",
    "SessionUpdate",
    "SessionResponse",
    "SessionListResponse",
    # Agent schemas
    "SessionAgentCreate",
    "SessionAgentUpdate",
    "SessionAgentResponse",
    "SessionAgentListResponse",
    # Message schemas
    "SessionMessageCreate",
    "SessionMessageUpdate",
    "SessionMessageResponse",
    "SessionMessageListResponse",
    "MessagePaginationQuery",
    # Common schemas
    "ErrorResponse",
    "HealthResponse",
    "PaginationQuery",
]