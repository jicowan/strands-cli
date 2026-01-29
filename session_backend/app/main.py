"""FastAPI application main module."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid

from .config import get_settings, validate_configuration
from .logging_config import setup_logging, log_request_response, get_logger
from .database import initialize_database, close_database, get_database_health, check_database_connectivity
from .routers import sessions, agents, messages, health


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Session Backend API")
    
    # Validate configuration
    try:
        validate_configuration()
        logger.info("Configuration validation successful")
    except Exception as e:
        logger.error("Configuration validation failed: %s", str(e))
        raise
    
    # Initialize database
    try:
        await initialize_database()
        logger.info("Database initialization successful")
    except Exception as e:
        logger.error("Database initialization failed: %s", str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Session Backend API")
    await close_database()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    # Set up logging first
    setup_logging(settings)
    
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request logging and metrics middleware
    @app.middleware("http")
    async def log_requests_and_collect_metrics(request: Request, call_next):
        """Log HTTP requests and responses, and collect metrics."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        # Increment total requests
        app.state.metrics["requests_total"] += 1
        
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Update metrics
            status_code = response.status_code
            if status_code not in app.state.metrics["requests_by_status"]:
                app.state.metrics["requests_by_status"][status_code] = 0
            app.state.metrics["requests_by_status"][status_code] += 1
            
            app.state.metrics["response_time_sum"] += duration_ms
            app.state.metrics["response_time_count"] += 1
            
            if status_code >= 400:
                app.state.metrics["errors_total"] += 1
            
            log_request_response(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
            return response
            
        except HTTPException as http_exc:
            # Re-raise HTTPExceptions to preserve status codes (like 503 from health checks)
            duration_ms = (time.time() - start_time) * 1000
            
            # Update metrics for HTTP exceptions
            status_code = http_exc.status_code
            if status_code not in app.state.metrics["requests_by_status"]:
                app.state.metrics["requests_by_status"][status_code] = 0
            app.state.metrics["requests_by_status"][status_code] += 1
            
            app.state.metrics["response_time_sum"] += duration_ms
            app.state.metrics["response_time_count"] += 1
            
            if status_code >= 400:
                app.state.metrics["errors_total"] += 1
            
            log_request_response(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms
            )
            
            raise http_exc
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            app.state.metrics["errors_total"] += 1
            
            logger.error(
                "Request failed with exception",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': duration_ms,
                    'error': str(e),
                    'event_type': 'http_error'
                }
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "request_id": request_id
                }
            )
    
    # Metrics collection
    app.state.metrics = {
        "requests_total": 0,
        "requests_by_status": {},
        "response_time_sum": 0.0,
        "response_time_count": 0,
        "database_connections_active": 0,
        "errors_total": 0
    }
    
    # Include API routers
    app.include_router(sessions.router, prefix="/api/v1")
    app.include_router(agents.router, prefix="/api/v1")
    app.include_router(messages.router, prefix="/api/v1")
    app.include_router(health.router)
    
    logger.info("FastAPI application created successfully")
    return app


# Create the application instance
app = create_app()