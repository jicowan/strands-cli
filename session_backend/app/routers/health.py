"""Health check API endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time
import psutil
import os

from ..database import get_db_session, get_database_health, check_database_connectivity
from ..schemas.common import HealthResponse
from ..config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={
        503: {"model": HealthResponse, "description": "Service Unavailable"},
    }
)


@router.get(
    "",
    response_model=HealthResponse,
    summary="Basic health check",
    description="Basic health check endpoint that returns the service status."
)
async def health_check():
    """Basic health check endpoint."""
    settings = get_settings()
    
    return HealthResponse(
        status="healthy",
        version=settings.api_version,
        checks={
            "service": {
                "status": "healthy",
                "message": "Session Backend API is running"
            }
        }
    )


@router.get(
    "/db",
    response_model=HealthResponse,
    summary="Database health check",
    description="Database connectivity health check endpoint."
)
async def database_health_check():
    """Database connectivity health check."""
    settings = get_settings()
    
    try:
        start_time = time.time()
        health_info = await get_database_health()
        response_time_ms = (time.time() - start_time) * 1000
        
        if health_info["status"] == "healthy":
            return HealthResponse(
                status="healthy",
                version=settings.api_version,
                checks={
                    "database": {
                        "status": "healthy",
                        "response_time_ms": round(response_time_ms, 2),
                        "connection_pool": health_info.get("connection_pool", {}),
                        "message": "Database is accessible"
                    }
                }
            )
        else:
            logger.warning(f"Database health check failed: {health_info}")
            raise HTTPException(
                status_code=503,
                detail=HealthResponse(
                    status="unhealthy",
                    version=settings.api_version,
                    checks={
                        "database": {
                            "status": "unhealthy",
                            "response_time_ms": round(response_time_ms, 2),
                            "error": health_info.get("error", "Database connectivity issue"),
                            "message": "Database is not accessible"
                        }
                    }
                ).model_dump(mode='json')
            )
            
    except Exception as e:
        logger.error(f"Database health check error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=HealthResponse(
                status="unhealthy",
                version=settings.api_version,
                checks={
                    "database": {
                        "status": "unhealthy",
                        "error": str(e),
                        "message": "Database health check failed"
                    }
                }
            ).model_dump(mode='json')
        )


@router.get(
    "/ready",
    response_model=HealthResponse,
    summary="Readiness probe",
    description="Readiness probe endpoint for Kubernetes deployment."
)
async def readiness_check():
    """Readiness probe for Kubernetes."""
    settings = get_settings()
    
    try:
        # Check if database is ready
        start_time = time.time()
        is_db_ready = await check_database_connectivity()
        response_time_ms = (time.time() - start_time) * 1000
        
        if is_db_ready:
            return HealthResponse(
                status="ready",
                version=settings.api_version,
                checks={
                    "service": {
                        "status": "ready",
                        "message": "Session Backend API is ready"
                    },
                    "database": {
                        "status": "ready",
                        "response_time_ms": round(response_time_ms, 2),
                        "message": "Database is ready"
                    }
                }
            )
        else:
            logger.warning("Readiness check failed - database not ready")
            raise HTTPException(
                status_code=503,
                detail=HealthResponse(
                    status="not ready",
                    version=settings.api_version,
                    checks={
                        "service": {
                            "status": "ready",
                            "message": "Session Backend API is ready"
                        },
                        "database": {
                            "status": "not ready",
                            "response_time_ms": round(response_time_ms, 2),
                            "message": "Database is not ready"
                        }
                    }
                ).model_dump(mode='json')
            )
            
    except HTTPException:
        # Re-raise HTTPExceptions (like the 503 we raise for "not ready")
        raise
    except Exception as e:
        logger.error(f"Readiness check error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=HealthResponse(
                status="not ready",
                version=settings.api_version,
                checks={
                    "service": {
                        "status": "ready",
                        "message": "Session Backend API is ready"
                    },
                    "database": {
                        "status": "error",
                        "error": str(e),
                        "message": "Database readiness check failed"
                    }
                }
            ).model_dump(mode='json')
        )


@router.get(
    "/live",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Liveness probe endpoint for Kubernetes deployment."
)
async def liveness_check():
    """Liveness probe for Kubernetes."""
    settings = get_settings()
    
    # Liveness check should be simple and fast
    # It only checks if the application is running, not external dependencies
    return HealthResponse(
        status="alive",
        version=settings.api_version,
        checks={
            "service": {
                "status": "alive",
                "message": "Session Backend API is alive"
            }
        }
    )


@router.get(
    "/metrics",
    summary="Basic metrics",
    description="Basic application metrics for monitoring."
)
async def get_metrics(request: Request):
    """Get basic application metrics."""
    try:
        # Get process metrics
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        # Get database health for connection pool metrics
        db_health = await get_database_health()
        
        # Get metrics from app state
        metrics = getattr(request.app.state, 'metrics', {
            "requests_total": 0,
            "requests_by_status": {},
            "response_time_sum": 0.0,
            "response_time_count": 0,
            "database_connections_active": 0,
            "errors_total": 0
        })
        
        # Calculate average response time
        avg_response_time = (
            metrics["response_time_sum"] / metrics["response_time_count"]
            if metrics["response_time_count"] > 0 else 0.0
        )
        
        return {
            "timestamp": time.time(),
            "application": {
                "requests_total": metrics["requests_total"],
                "requests_by_status": metrics["requests_by_status"],
                "errors_total": metrics["errors_total"],
                "average_response_time_ms": round(avg_response_time, 2)
            },
            "system": {
                "memory_usage_bytes": memory_info.rss,
                "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2),
                "cpu_percent": process.cpu_percent()
            },
            "database": {
                "status": db_health.get("status", "unknown"),
                "connection_pool": db_health.get("pool", {})
            }
        }
        
    except Exception as e:
        logger.error(f"Metrics collection error: {str(e)}")
        return {
            "timestamp": time.time(),
            "error": "Failed to collect metrics",
            "message": str(e)
        }