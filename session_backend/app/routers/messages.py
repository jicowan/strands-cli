"""Session message management API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..database import get_db_session
from ..services.message_service import MessageService
from ..schemas.message import (
    SessionMessageCreate,
    SessionMessageUpdate,
    SessionMessageResponse,
    SessionMessageListResponse,
    MessagePaginationQuery,
)
from ..schemas.common import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sessions/{session_id}/agents/{agent_id}/messages",
    tags=["messages"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        404: {"model": ErrorResponse, "description": "Session, Agent, or Message Not Found"},
        409: {"model": ErrorResponse, "description": "Message Already Exists"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    }
)


def get_request_id(request: Request) -> Optional[str]:
    """Extract request ID from request state."""
    return getattr(request.state, 'request_id', None)


@router.post(
    "",
    response_model=SessionMessageResponse,
    status_code=201,
    summary="Create a new message",
    description="Create a new message within the specified agent's conversation."
)
async def create_message(
    session_id: str,
    agent_id: str,
    message_data: SessionMessageCreate,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new message in an agent's conversation."""
    request_id = get_request_id(request)
    
    try:
        service = MessageService(db)
        message = await service.create_message(session_id, agent_id, message_data)
        
        logger.info(
            f"Message created successfully: {message_data.message_id} for agent {agent_id} in session {session_id}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id,
                'message_id': message_data.message_id
            }
        )
        
        return message
        
    except ValueError as e:
        error_msg = str(e)
        if "does not exist" in error_msg:
            logger.warning(
                f"Message creation failed - agent not found: {agent_id} in session {session_id}",
                extra={
                    'request_id': request_id,
                    'session_id': session_id,
                    'agent_id': agent_id,
                    'message_id': message_data.message_id
                }
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NotFoundError",
                    "message": error_msg,
                    "request_id": request_id
                }
            )
        else:
            logger.warning(
                f"Message creation failed - validation error: {error_msg}",
                extra={
                    'request_id': request_id,
                    'session_id': session_id,
                    'agent_id': agent_id,
                    'message_id': message_data.message_id
                }
            )
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "ConflictError",
                    "message": error_msg,
                    "request_id": request_id
                }
            )
    except Exception as e:
        logger.error(
            f"Message creation failed - internal error: {str(e)}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id,
                'message_id': message_data.message_id
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to create message",
                "request_id": request_id
            }
        )


@router.get(
    "/{message_id}",
    response_model=SessionMessageResponse,
    summary="Get message by ID",
    description="Retrieve a specific message by its ID within the agent's conversation."
)
async def get_message(
    session_id: str,
    agent_id: str,
    message_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a message by ID within an agent's conversation."""
    request_id = get_request_id(request)
    
    try:
        service = MessageService(db)
        message = await service.get_message(session_id, agent_id, message_id)
        
        if not message:
            logger.warning(
                f"Message not found: {message_id} for agent {agent_id} in session {session_id}",
                extra={
                    'request_id': request_id,
                    'session_id': session_id,
                    'agent_id': agent_id,
                    'message_id': message_id
                }
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NotFoundError",
                    "message": f"Message {message_id} not found for agent '{agent_id}' in session '{session_id}'",
                    "request_id": request_id
                }
            )
        
        logger.info(
            f"Message retrieved successfully: {message_id} for agent {agent_id} in session {session_id}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id,
                'message_id': message_id
            }
        )
        
        return message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Message retrieval failed - internal error: {str(e)}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id,
                'message_id': message_id
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve message",
                "request_id": request_id
            }
        )


@router.put(
    "/{message_id}",
    response_model=SessionMessageResponse,
    summary="Update message",
    description="Update an existing message within the agent's conversation."
)
async def update_message(
    session_id: str,
    agent_id: str,
    message_id: int,
    message_data: SessionMessageUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a message within an agent's conversation."""
    request_id = get_request_id(request)
    
    try:
        service = MessageService(db)
        message = await service.update_message(session_id, agent_id, message_id, message_data)
        
        if not message:
            logger.warning(
                f"Message not found for update: {message_id} for agent {agent_id} in session {session_id}",
                extra={
                    'request_id': request_id,
                    'session_id': session_id,
                    'agent_id': agent_id,
                    'message_id': message_id
                }
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NotFoundError",
                    "message": f"Message {message_id} not found for agent '{agent_id}' in session '{session_id}'",
                    "request_id": request_id
                }
            )
        
        logger.info(
            f"Message updated successfully: {message_id} for agent {agent_id} in session {session_id}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id,
                'message_id': message_id
            }
        )
        
        return message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Message update failed - internal error: {str(e)}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id,
                'message_id': message_id
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to update message",
                "request_id": request_id
            }
        )


@router.delete(
    "/{message_id}",
    status_code=204,
    summary="Delete message",
    description="Delete a specific message from the agent's conversation."
)
async def delete_message(
    session_id: str,
    agent_id: str,
    message_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a message from an agent's conversation."""
    request_id = get_request_id(request)
    
    try:
        service = MessageService(db)
        deleted = await service.delete_message(session_id, agent_id, message_id)
        
        if not deleted:
            logger.warning(
                f"Message not found for deletion: {message_id} for agent {agent_id} in session {session_id}",
                extra={
                    'request_id': request_id,
                    'session_id': session_id,
                    'agent_id': agent_id,
                    'message_id': message_id
                }
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NotFoundError",
                    "message": f"Message {message_id} not found for agent '{agent_id}' in session '{session_id}'",
                    "request_id": request_id
                }
            )
        
        logger.info(
            f"Message deleted successfully: {message_id} for agent {agent_id} in session {session_id}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id,
                'message_id': message_id
            }
        )
        
        # Return 204 No Content for successful deletion
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Message deletion failed - internal error: {str(e)}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id,
                'message_id': message_id
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to delete message",
                "request_id": request_id
            }
        )


@router.get(
    "",
    response_model=SessionMessageListResponse,
    summary="List messages",
    description="List messages for an agent with pagination and chronological ordering."
)
async def list_messages(
    session_id: str,
    agent_id: str,
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=1000, description="Number of messages per page"),
    order: str = Query("asc", regex="^(asc|desc)$", description="Sort order: 'asc' for chronological, 'desc' for reverse chronological"),
    db: AsyncSession = Depends(get_db_session)
):
    """List messages for an agent with pagination and chronological ordering."""
    request_id = get_request_id(request)
    
    try:
        # Create pagination query object
        pagination = MessagePaginationQuery(
            page=page,
            page_size=page_size,
            order=order
        )
        
        service = MessageService(db)
        messages = await service.list_messages(session_id, agent_id, pagination)
        
        logger.info(
            f"Messages listed successfully for agent {agent_id} in session {session_id}: page={page}, page_size={page_size}, order={order}, total={messages.total}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id,
                'page': page,
                'page_size': page_size,
                'order': order
            }
        )
        
        return messages
        
    except ValueError as e:
        if "does not exist" in str(e):
            logger.warning(
                f"Agent not found for message listing: {agent_id} in session {session_id}",
                extra={
                    'request_id': request_id,
                    'session_id': session_id,
                    'agent_id': agent_id
                }
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NotFoundError",
                    "message": str(e),
                    "request_id": request_id
                }
            )
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "ValidationError",
                    "message": str(e),
                    "request_id": request_id
                }
            )
    except Exception as e:
        logger.error(
            f"Message listing failed - internal error: {str(e)}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id,
                'page': page,
                'page_size': page_size,
                'order': order
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to list messages",
                "request_id": request_id
            }
        )