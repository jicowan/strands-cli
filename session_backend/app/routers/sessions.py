"""Session management API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..database import get_db_session
from ..services.session_service import SessionService
from ..schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,
)
from ..schemas.common import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        404: {"model": ErrorResponse, "description": "Session Not Found"},
        409: {"model": ErrorResponse, "description": "Session Already Exists"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    }
)


def get_request_id(request: Request) -> Optional[str]:
    """Extract request ID from request state."""
    return getattr(request.state, 'request_id', None)


@router.post(
    "",
    response_model=SessionResponse,
    status_code=201,
    summary="Create a new session",
    description="Create a new session with the provided session data."
)
async def create_session(
    session_data: SessionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new session."""
    request_id = get_request_id(request)
    
    try:
        service = SessionService(db)
        session = await service.create_session(session_data)
        
        logger.info(
            f"Session created successfully: {session_data.session_id}",
            extra={'request_id': request_id, 'session_id': session_data.session_id}
        )
        
        return session
        
    except ValueError as e:
        logger.warning(
            f"Session creation failed - validation error: {str(e)}",
            extra={'request_id': request_id, 'session_id': session_data.session_id}
        )
        raise HTTPException(
            status_code=409,
            detail={
                "error": "ConflictError",
                "message": str(e),
                "request_id": request_id
            }
        )
    except Exception as e:
        logger.error(
            f"Session creation failed - internal error: {str(e)}",
            extra={'request_id': request_id, 'session_id': session_data.session_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to create session",
                "request_id": request_id
            }
        )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get session by ID",
    description="Retrieve a session by its unique identifier."
)
async def get_session(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a session by ID."""
    request_id = get_request_id(request)
    
    try:
        service = SessionService(db)
        session = await service.get_session(session_id)
        
        if not session:
            logger.warning(
                f"Session not found: {session_id}",
                extra={'request_id': request_id, 'session_id': session_id}
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NotFoundError",
                    "message": f"Session '{session_id}' not found",
                    "request_id": request_id
                }
            )
        
        logger.info(
            f"Session retrieved successfully: {session_id}",
            extra={'request_id': request_id, 'session_id': session_id}
        )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Session retrieval failed - internal error: {str(e)}",
            extra={'request_id': request_id, 'session_id': session_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve session",
                "request_id": request_id
            }
        )


@router.put(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Update session",
    description="Update an existing session with new data."
)
async def update_session(
    session_id: str,
    session_data: SessionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a session."""
    request_id = get_request_id(request)
    
    try:
        service = SessionService(db)
        session = await service.update_session(session_id, session_data)
        
        if not session:
            logger.warning(
                f"Session not found for update: {session_id}",
                extra={'request_id': request_id, 'session_id': session_id}
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NotFoundError",
                    "message": f"Session '{session_id}' not found",
                    "request_id": request_id
                }
            )
        
        logger.info(
            f"Session updated successfully: {session_id}",
            extra={'request_id': request_id, 'session_id': session_id}
        )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Session update failed - internal error: {str(e)}",
            extra={'request_id': request_id, 'session_id': session_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to update session",
                "request_id": request_id
            }
        )


@router.delete(
    "/{session_id}",
    status_code=204,
    summary="Delete session",
    description="Delete a session and all associated data (agents and messages)."
)
async def delete_session(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a session and all associated data."""
    request_id = get_request_id(request)
    
    try:
        service = SessionService(db)
        deleted = await service.delete_session(session_id)
        
        if not deleted:
            logger.warning(
                f"Session not found for deletion: {session_id}",
                extra={'request_id': request_id, 'session_id': session_id}
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NotFoundError",
                    "message": f"Session '{session_id}' not found",
                    "request_id": request_id
                }
            )
        
        logger.info(
            f"Session deleted successfully: {session_id}",
            extra={'request_id': request_id, 'session_id': session_id}
        )
        
        # Return 204 No Content for successful deletion
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Session deletion failed - internal error: {str(e)}",
            extra={'request_id': request_id, 'session_id': session_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to delete session",
                "request_id": request_id
            }
        )


@router.get(
    "",
    response_model=SessionListResponse,
    summary="List sessions",
    description="List all sessions with pagination support."
)
async def list_sessions(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=1000, description="Number of sessions per page"),
    db: AsyncSession = Depends(get_db_session)
):
    """List sessions with pagination."""
    request_id = get_request_id(request)
    
    try:
        service = SessionService(db)
        sessions = await service.list_sessions(page=page, page_size=page_size)
        
        logger.info(
            f"Sessions listed successfully: page={page}, page_size={page_size}, total={sessions.total}",
            extra={'request_id': request_id, 'page': page, 'page_size': page_size}
        )
        
        return sessions
        
    except Exception as e:
        logger.error(
            f"Session listing failed - internal error: {str(e)}",
            extra={'request_id': request_id, 'page': page, 'page_size': page_size}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to list sessions",
                "request_id": request_id
            }
        )