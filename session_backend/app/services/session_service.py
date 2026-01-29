"""Session service layer for business logic."""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
import logging

from ..models.session import SessionModel, SessionTypeEnum
from ..schemas.session import SessionCreate, SessionUpdate, SessionResponse, SessionListResponse
from ..database import execute_with_retry, TransactionError

logger = logging.getLogger(__name__)


class SessionService:
    """Service layer for session operations."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize session service with database session."""
        self.db_session = db_session
    
    async def create_session(self, session_data: SessionCreate) -> SessionResponse:
        """Create a new session with validation and error handling."""
        try:
            # Check if session already exists
            existing_session = await self._get_session_by_id(session_data.session_id)
            if existing_session:
                raise ValueError(f"Session with ID '{session_data.session_id}' already exists")
            
            # Create new session model with Strands-compatible schema
            session_model = SessionModel(
                session_id=session_data.session_id,
                session_type=SessionTypeEnum[session_data.session_type.value]
            )
            
            # Add to database
            self.db_session.add(session_model)
            await self.db_session.commit()
            await self.db_session.refresh(session_model)
            
            logger.info(f"Created session: {session_data.session_id}")
            return SessionResponse.model_validate(session_model)
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to create session {session_data.session_id}: {str(e)}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[SessionResponse]:
        """Retrieve a session by ID."""
        try:
            session_model = await self._get_session_by_id(session_id)
            if not session_model:
                return None
            
            return SessionResponse.model_validate(session_model)
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {str(e)}")
            raise
    
    async def update_session(self, session_id: str, session_data: SessionUpdate) -> Optional[SessionResponse]:
        """Update an existing session."""
        try:
            session_model = await self._get_session_by_id(session_id)
            if not session_model:
                return None
            
            # Update fields if provided
            if session_data.session_type is not None:
                session_model.session_type = SessionTypeEnum[session_data.session_type.value]
            
            await self.db_session.commit()
            await self.db_session.refresh(session_model)
            
            logger.info(f"Updated session: {session_id}")
            return SessionResponse.model_validate(session_model)
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to update session {session_id}: {str(e)}")
            raise
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all associated data (cascade)."""
        try:
            session_model = await self._get_session_by_id(session_id)
            if not session_model:
                return False
            
            # Delete session (cascade will handle agents and messages)
            await self.db_session.delete(session_model)
            await self.db_session.commit()
            
            logger.info(f"Deleted session: {session_id}")
            return True
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to delete session {session_id}: {str(e)}")
            raise
    
    async def list_sessions(self, page: int = 1, page_size: int = 10) -> SessionListResponse:
        """List sessions with pagination."""
        try:
            # Validate pagination parameters
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 1000:
                page_size = 10
            
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Get total count
            count_query = select(func.count(SessionModel.session_id))
            total_result = await self.db_session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Get sessions for current page
            query = (
                select(SessionModel)
                .options(selectinload(SessionModel.agents))
                .order_by(SessionModel.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            
            result = await self.db_session.execute(query)
            session_models = result.scalars().all()
            
            # Convert to response models
            sessions = [SessionResponse.model_validate(session) for session in session_models]
            
            return SessionListResponse(
                sessions=sessions,
                total=total,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {str(e)}")
            raise
    
    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        try:
            session_model = await self._get_session_by_id(session_id)
            return session_model is not None
        except Exception as e:
            logger.error(f"Failed to check session existence {session_id}: {str(e)}")
            raise
    
    async def _get_session_by_id(self, session_id: str) -> Optional[SessionModel]:
        """Internal method to get session model by ID."""
        query = (
            select(SessionModel)
            .options(selectinload(SessionModel.agents))
            .where(SessionModel.session_id == session_id)
        )
        
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()