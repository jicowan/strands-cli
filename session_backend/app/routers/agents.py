"""Session agent management API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..database import get_db_session
from ..services.agent_service import AgentService
from ..services.session_service import SessionService
from ..schemas.agent import (
    SessionAgentCreate,
    SessionAgentUpdate,
    SessionAgentResponse,
    SessionAgentListResponse,
)
from ..schemas.common import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sessions/{session_id}/agents",
    tags=["agents"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        404: {"model": ErrorResponse, "description": "Session or Agent Not Found"},
        409: {"model": ErrorResponse, "description": "Agent Already Exists"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    }
)


def get_request_id(request: Request) -> Optional[str]:
    """Extract request ID from request state."""
    return getattr(request.state, 'request_id', None)


@router.post(
    "",
    response_model=SessionAgentResponse,
    status_code=201,
    summary="Create a new agent in session",
    description="Create a new agent within the specified session."
)
async def create_agent(
    session_id: str,
    agent_data: SessionAgentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new agent in a session."""
    request_id = get_request_id(request)
    
    try:
        service = AgentService(db)
        agent = await service.create_agent(session_id, agent_data)
        
        logger.info(
            f"Agent created successfully: {agent_data.agent_id} in session {session_id}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_data.agent_id
            }
        )
        
        return agent
        
    except ValueError as e:
        error_msg = str(e)
        if "does not exist" in error_msg:
            logger.warning(
                f"Agent creation failed - session not found: {session_id}",
                extra={
                    'request_id': request_id,
                    'session_id': session_id,
                    'agent_id': agent_data.agent_id
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
                f"Agent creation failed - validation error: {error_msg}",
                extra={
                    'request_id': request_id,
                    'session_id': session_id,
                    'agent_id': agent_data.agent_id
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
            f"Agent creation failed - internal error: {str(e)}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_data.agent_id
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to create agent",
                "request_id": request_id
            }
        )


@router.get(
    "/{agent_id}",
    response_model=SessionAgentResponse,
    summary="Get agent by ID",
    description="Retrieve an agent by its ID within the specified session."
)
async def get_agent(
    session_id: str,
    agent_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Get an agent by ID within a session."""
    request_id = get_request_id(request)
    
    try:
        service = AgentService(db)
        agent = await service.get_agent(session_id, agent_id)
        
        if not agent:
            logger.warning(
                f"Agent not found: {agent_id} in session {session_id}",
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
                    "message": f"Agent '{agent_id}' not found in session '{session_id}'",
                    "request_id": request_id
                }
            )
        
        logger.info(
            f"Agent retrieved successfully: {agent_id} in session {session_id}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id
            }
        )
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Agent retrieval failed - internal error: {str(e)}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve agent",
                "request_id": request_id
            }
        )


@router.put(
    "/{agent_id}",
    response_model=SessionAgentResponse,
    summary="Update agent",
    description="Update an existing agent within the specified session."
)
async def update_agent(
    session_id: str,
    agent_id: str,
    agent_data: SessionAgentUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Update an agent within a session."""
    request_id = get_request_id(request)
    
    try:
        service = AgentService(db)
        agent = await service.update_agent(session_id, agent_id, agent_data)
        
        if not agent:
            logger.warning(
                f"Agent not found for update: {agent_id} in session {session_id}",
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
                    "message": f"Agent '{agent_id}' not found in session '{session_id}'",
                    "request_id": request_id
                }
            )
        
        logger.info(
            f"Agent updated successfully: {agent_id} in session {session_id}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id
            }
        )
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Agent update failed - internal error: {str(e)}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to update agent",
                "request_id": request_id
            }
        )


@router.delete(
    "/{agent_id}",
    status_code=204,
    summary="Delete agent",
    description="Delete an agent and all associated messages from the session."
)
async def delete_agent(
    session_id: str,
    agent_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete an agent and all associated messages."""
    request_id = get_request_id(request)
    
    try:
        service = AgentService(db)
        deleted = await service.delete_agent(session_id, agent_id)
        
        if not deleted:
            logger.warning(
                f"Agent not found for deletion: {agent_id} in session {session_id}",
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
                    "message": f"Agent '{agent_id}' not found in session '{session_id}'",
                    "request_id": request_id
                }
            )
        
        logger.info(
            f"Agent deleted successfully: {agent_id} in session {session_id}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id
            }
        )
        
        # Return 204 No Content for successful deletion
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Agent deletion failed - internal error: {str(e)}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'agent_id': agent_id
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to delete agent",
                "request_id": request_id
            }
        )


@router.get(
    "",
    response_model=SessionAgentListResponse,
    summary="List agents in session",
    description="List all agents within the specified session with pagination support."
)
async def list_agents(
    session_id: str,
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=1000, description="Number of agents per page"),
    db: AsyncSession = Depends(get_db_session)
):
    """List agents in a session with pagination."""
    request_id = get_request_id(request)
    
    try:
        service = AgentService(db)
        agents = await service.list_agents_in_session(
            session_id, page=page, page_size=page_size
        )
        
        logger.info(
            f"Agents listed successfully for session {session_id}: page={page}, page_size={page_size}, total={agents.total}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'page': page,
                'page_size': page_size
            }
        )
        
        return agents
        
    except ValueError as e:
        if "does not exist" in str(e):
            logger.warning(
                f"Session not found for agent listing: {session_id}",
                extra={
                    'request_id': request_id,
                    'session_id': session_id
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
            f"Agent listing failed - internal error: {str(e)}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'page': page,
                'page_size': page_size
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to list agents",
                "request_id": request_id
            }
        )