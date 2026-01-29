"""SessionMessage service layer for business logic."""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, and_, desc, asc
from sqlalchemy.orm import selectinload
import logging

from ..models.message import SessionMessageModel
from ..models.agent import SessionAgentModel
from ..schemas.message import (
    SessionMessageCreate, 
    SessionMessageUpdate, 
    SessionMessageResponse, 
    SessionMessageListResponse,
    MessagePaginationQuery
)
from ..database import execute_with_retry, TransactionError

logger = logging.getLogger(__name__)


class MessageService:
    """Service layer for session message operations."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize message service with database session."""
        self.db_session = db_session
    
    async def create_message(self, session_id: str, agent_id: str, message_data: SessionMessageCreate) -> SessionMessageResponse:
        """Create a new message within an agent's conversation."""
        try:
            # Verify agent exists
            agent_exists = await self._agent_exists(session_id, agent_id)
            if not agent_exists:
                raise ValueError(f"Agent '{agent_id}' does not exist in session '{session_id}'")
            
            # Check if message already exists
            existing_message = await self._get_message_by_ids(session_id, agent_id, message_data.message_id)
            if existing_message:
                raise ValueError(f"Message {message_data.message_id} already exists for agent '{agent_id}' in session '{session_id}'")
            
            # Create new message model
            message_model = SessionMessageModel(
                session_id=session_id,
                agent_id=agent_id,
                message_id=message_data.message_id,
                message=message_data.message,
                redact_message=message_data.redact_message
            )
            
            # Add to database
            self.db_session.add(message_model)
            await self.db_session.commit()
            await self.db_session.refresh(message_model)
            
            logger.info(f"Created message {message_data.message_id} for agent {agent_id} in session {session_id}")
            return SessionMessageResponse.model_validate(message_model)
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to create message {message_data.message_id} for agent {agent_id} in session {session_id}: {str(e)}")
            raise
    
    async def get_message(self, session_id: str, agent_id: str, message_id: int) -> Optional[SessionMessageResponse]:
        """Retrieve a specific message by IDs."""
        try:
            message_model = await self._get_message_by_ids(session_id, agent_id, message_id)
            if not message_model:
                return None
            
            return SessionMessageResponse.model_validate(message_model)
            
        except Exception as e:
            logger.error(f"Failed to get message {message_id} for agent {agent_id} in session {session_id}: {str(e)}")
            raise
    
    async def update_message(self, session_id: str, agent_id: str, message_id: int, message_data: SessionMessageUpdate) -> Optional[SessionMessageResponse]:
        """Update an existing message."""
        try:
            message_model = await self._get_message_by_ids(session_id, agent_id, message_id)
            if not message_model:
                return None
            
            # Update fields if provided
            if message_data.message is not None:
                message_model.message = message_data.message
            
            if message_data.redact_message is not None:
                message_model.redact_message = message_data.redact_message
            
            await self.db_session.commit()
            await self.db_session.refresh(message_model)
            
            logger.info(f"Updated message {message_id} for agent {agent_id} in session {session_id}")
            return SessionMessageResponse.model_validate(message_model)
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to update message {message_id} for agent {agent_id} in session {session_id}: {str(e)}")
            raise
    
    async def delete_message(self, session_id: str, agent_id: str, message_id: int) -> bool:
        """Delete a specific message."""
        try:
            message_model = await self._get_message_by_ids(session_id, agent_id, message_id)
            if not message_model:
                return False
            
            await self.db_session.delete(message_model)
            await self.db_session.commit()
            
            logger.info(f"Deleted message {message_id} for agent {agent_id} in session {session_id}")
            return True
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to delete message {message_id} for agent {agent_id} in session {session_id}: {str(e)}")
            raise
    
    async def list_messages(self, session_id: str, agent_id: str, pagination: MessagePaginationQuery) -> SessionMessageListResponse:
        """List messages for an agent with pagination and chronological ordering."""
        try:
            # Verify agent exists
            agent_exists = await self._agent_exists(session_id, agent_id)
            if not agent_exists:
                raise ValueError(f"Agent '{agent_id}' does not exist in session '{session_id}'")
            
            # Validate pagination parameters
            page = max(1, pagination.page)
            page_size = max(1, min(1000, pagination.page_size))
            
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Get total count
            count_query = select(func.count(SessionMessageModel.id)).where(
                and_(
                    SessionMessageModel.session_id == session_id,
                    SessionMessageModel.agent_id == agent_id
                )
            )
            total_result = await self.db_session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Determine sort order - chronological ordering based on message_id and created_at
            if pagination.order == "desc":
                order_by = [
                    desc(SessionMessageModel.message_id),
                    desc(SessionMessageModel.created_at)
                ]
            else:  # default to "asc"
                order_by = [
                    asc(SessionMessageModel.message_id),
                    asc(SessionMessageModel.created_at)
                ]
            
            # Get messages for current page
            query = (
                select(SessionMessageModel)
                .where(
                    and_(
                        SessionMessageModel.session_id == session_id,
                        SessionMessageModel.agent_id == agent_id
                    )
                )
                .order_by(*order_by)
                .offset(offset)
                .limit(page_size)
            )
            
            result = await self.db_session.execute(query)
            message_models = result.scalars().all()
            
            # Convert to response models
            messages = [SessionMessageResponse.model_validate(message) for message in message_models]
            
            return SessionMessageListResponse(
                messages=messages,
                total=total,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            logger.error(f"Failed to list messages for agent {agent_id} in session {session_id}: {str(e)}")
            raise
    
    async def get_messages_by_agent(self, session_id: str, agent_id: str, order: str = "asc") -> List[SessionMessageResponse]:
        """Get all messages for an agent (without pagination) in chronological order."""
        try:
            # Verify agent exists
            agent_exists = await self._agent_exists(session_id, agent_id)
            if not agent_exists:
                return []
            
            # Determine sort order
            if order == "desc":
                order_by = [
                    desc(SessionMessageModel.message_id),
                    desc(SessionMessageModel.created_at)
                ]
            else:  # default to "asc"
                order_by = [
                    asc(SessionMessageModel.message_id),
                    asc(SessionMessageModel.created_at)
                ]
            
            query = (
                select(SessionMessageModel)
                .where(
                    and_(
                        SessionMessageModel.session_id == session_id,
                        SessionMessageModel.agent_id == agent_id
                    )
                )
                .order_by(*order_by)
            )
            
            result = await self.db_session.execute(query)
            message_models = result.scalars().all()
            
            return [SessionMessageResponse.model_validate(message) for message in message_models]
            
        except Exception as e:
            logger.error(f"Failed to get messages for agent {agent_id} in session {session_id}: {str(e)}")
            raise
    
    async def get_latest_message_id(self, session_id: str, agent_id: str) -> Optional[int]:
        """Get the latest (highest) message ID for an agent."""
        try:
            query = (
                select(func.max(SessionMessageModel.message_id))
                .where(
                    and_(
                        SessionMessageModel.session_id == session_id,
                        SessionMessageModel.agent_id == agent_id
                    )
                )
            )
            
            result = await self.db_session.execute(query)
            return result.scalar()
            
        except Exception as e:
            logger.error(f"Failed to get latest message ID for agent {agent_id} in session {session_id}: {str(e)}")
            raise
    
    async def get_message_count(self, session_id: str, agent_id: str) -> int:
        """Get the total number of messages for an agent."""
        try:
            query = select(func.count(SessionMessageModel.id)).where(
                and_(
                    SessionMessageModel.session_id == session_id,
                    SessionMessageModel.agent_id == agent_id
                )
            )
            
            result = await self.db_session.execute(query)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Failed to get message count for agent {agent_id} in session {session_id}: {str(e)}")
            raise
    
    async def message_exists(self, session_id: str, agent_id: str, message_id: int) -> bool:
        """Check if a message exists."""
        try:
            message_model = await self._get_message_by_ids(session_id, agent_id, message_id)
            return message_model is not None
        except Exception as e:
            logger.error(f"Failed to check message existence {message_id} for agent {agent_id} in session {session_id}: {str(e)}")
            raise
    
    async def _get_message_by_ids(self, session_id: str, agent_id: str, message_id: int) -> Optional[SessionMessageModel]:
        """Internal method to get message model by IDs."""
        query = select(SessionMessageModel).where(
            and_(
                SessionMessageModel.session_id == session_id,
                SessionMessageModel.agent_id == agent_id,
                SessionMessageModel.message_id == message_id
            )
        )
        
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    async def _agent_exists(self, session_id: str, agent_id: str) -> bool:
        """Internal method to check if agent exists."""
        query = select(SessionAgentModel.id).where(
            and_(
                SessionAgentModel.session_id == session_id,
                SessionAgentModel.agent_id == agent_id
            )
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none() is not None