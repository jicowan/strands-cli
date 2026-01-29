"""Common API schemas for error handling and responses."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Schema for API error responses."""
    
    error: str = Field(
        ...,
        description="Error type or category"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details and context"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the error occurred"
    )
    request_id: Optional[str] = Field(
        None,
        description="Unique identifier for the request that caused the error"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid session ID format",
                "details": {
                    "field": "session_id",
                    "value": "invalid-id!",
                    "constraint": "alphanumeric_with_hyphens_underscores"
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "request_id": "req-123456"
            }
        }


class HealthResponse(BaseModel):
    """Schema for health check responses."""
    
    status: str = Field(
        ...,
        description="Health status: 'healthy', 'unhealthy', or 'degraded'"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the health check"
    )
    version: Optional[str] = Field(
        None,
        description="Application version"
    )
    checks: Optional[Dict[str, Any]] = Field(
        None,
        description="Individual component health check results"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "version": "1.0.0",
                "checks": {
                    "database": {
                        "status": "healthy",
                        "response_time_ms": 15
                    },
                    "memory": {
                        "status": "healthy",
                        "usage_percent": 45
                    }
                }
            }
        }


class PaginationQuery(BaseModel):
    """Schema for pagination query parameters."""
    
    page: int = Field(
        1,
        ge=1,
        description="Page number (1-based)"
    )
    page_size: int = Field(
        10,
        ge=1,
        le=1000,
        description="Number of items per page"
    )
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "page": 1,
                "page_size": 10
            }
        }