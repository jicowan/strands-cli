"""SessionAgent service layer for business logic."""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, and_
from sqlalchemy.orm import selectinload
import logging

from ..models.agent import SessionAgentModel
from ..models.session import SessionModel
from ..schemas.agent import SessionAgentCreate, SessionAgentUpdate, SessionAgentResponse, SessionAgentListResponse
from ..database import execute_with_retry, TransactionError

logger = logging.getLogger(__name__)


class AgentService:
    """Service layer for session agent operations."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize agent service with database session."""
        self.db_session = db_session
    
    async def create_agent(self, session_id: str, agent_data: SessionAgentCreate) -> SessionAgentResponse:
        """Create a new agent within a session."""
        try:
            # Verify session exists
            session_exists = await self._session_exists(session_id)
            if not session_exists:
                raise ValueError(f"Session '{session_id}' does not exist")
            
            # Check if agent already exists in this session
            existing_agent = await self._get_agent_by_ids(session_id, agent_data.agent_id)
            if existing_agent:
                raise ValueError(f"Agent '{agent_data.agent_id}' already exists in session '{session_id}'")
            
            # Create new agent model
            agent_model = SessionAgentModel(
                session_id=session_id,
                agent_id=agent_data.agent_id,
                state=agent_data.state,
                conversation_manager_state=agent_data.conversation_manager_state,
                internal_state=agent_data.internal_state
            )
            
            # Add to database
            self.db_session.add(agent_model)
            await self.db_session.commit()
            await self.db_session.refresh(agent_model)
            
            logger.info(f"Created agent: {agent_data.agent_id} in session: {session_id}")
            return SessionAgentResponse.model_validate(agent_model)
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to create agent {agent_data.agent_id} in session {session_id}: {str(e)}")
            raise
    
    async def get_agent(self, session_id: str, agent_id: str) -> Optional[SessionAgentResponse]:
        """Retrieve an agent by session ID and agent ID."""
        try:
            agent_model = await self._get_agent_by_ids(session_id, agent_id)
            if not agent_model:
                return None
            
            return SessionAgentResponse.model_validate(agent_model)
            
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id} in session {session_id}: {str(e)}")
            raise
    
    async def update_agent(self, session_id: str, agent_id: str, agent_data: SessionAgentUpdate) -> Optional[SessionAgentResponse]:
        """Update an existing agent."""
        try:
            agent_model = await self._get_agent_by_ids(session_id, agent_id)
            if not agent_model:
                return None
            
            # Update fields if provided
            if agent_data.state is not None:
                agent_model.state = agent_data.state
            
            if agent_data.conversation_manager_state is not None:
                agent_model.conversation_manager_state = agent_data.conversation_manager_state
            
            if agent_data.internal_state is not None:
                agent_model.internal_state = agent_data.internal_state
            
            await self.db_session.commit()
            await self.db_session.refresh(agent_model)
            
            logger.info(f"Updated agent: {agent_id} in session: {session_id}")
            return SessionAgentResponse.model_validate(agent_model)
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to update agent {agent_id} in session {session_id}: {str(e)}")
            raise
    
    async def delete_agent(self, session_id: str, agent_id: str) -> bool:
        """Delete an agent and all associated messages (cascade)."""
        try:
            agent_model = await self._get_agent_by_ids(session_id, agent_id)
            if not agent_model:
                return False
            
            # Delete agent (cascade will handle messages)
            await self.db_session.delete(agent_model)
            await self.db_session.commit()
            
            logger.info(f"Deleted agent: {agent_id} in session: {session_id}")
            return True
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to delete agent {agent_id} in session {session_id}: {str(e)}")
            raise
    
    async def list_agents_in_session(self, session_id: str, page: int = 1, page_size: int = 10) -> SessionAgentListResponse:
        """List all agents in a session with pagination."""
        try:
            # Verify session exists
            session_exists = await self._session_exists(session_id)
            if not session_exists:
                raise ValueError(f"Session '{session_id}' does not exist")
            
            # Validate pagination parameters
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 1000:
                page_size = 10
            
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Get total count
            count_query = select(func.count(SessionAgentModel.id)).where(
                SessionAgentModel.session_id == session_id
            )
            total_result = await self.db_session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Get agents for current page
            query = (
                select(SessionAgentModel)
                .options(selectinload(SessionAgentModel.messages))
                .where(SessionAgentModel.session_id == session_id)
                .order_by(SessionAgentModel.created_at.asc())
                .offset(offset)
                .limit(page_size)
            )
            
            result = await self.db_session.execute(query)
            agent_models = result.scalars().all()
            
            # Convert to response models
            agents = [SessionAgentResponse.model_validate(agent) for agent in agent_models]
            
            return SessionAgentListResponse(
                agents=agents,
                total=total,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            logger.error(f"Failed to list agents in session {session_id}: {str(e)}")
            raise
    
    async def get_agents_by_session(self, session_id: str) -> List[SessionAgentResponse]:
        """Get all agents in a session (without pagination)."""
        try:
            # Verify session exists
            session_exists = await self._session_exists(session_id)
            if not session_exists:
                return []
            
            query = (
                select(SessionAgentModel)
                .options(selectinload(SessionAgentModel.messages))
                .where(SessionAgentModel.session_id == session_id)
                .order_by(SessionAgentModel.created_at.asc())
            )
            
            result = await self.db_session.execute(query)
            agent_models = result.scalars().all()
            
            return [SessionAgentResponse.model_validate(agent) for agent in agent_models]
            
        except Exception as e:
            logger.error(f"Failed to get agents by session {session_id}: {str(e)}")
            raise
    
    async def agent_exists(self, session_id: str, agent_id: str) -> bool:
        """Check if an agent exists in a session."""
        try:
            agent_model = await self._get_agent_by_ids(session_id, agent_id)
            return agent_model is not None
        except Exception as e:
            logger.error(f"Failed to check agent existence {agent_id} in session {session_id}: {str(e)}")
            raise
    
    async def _get_agent_by_ids(self, session_id: str, agent_id: str) -> Optional[SessionAgentModel]:
        """Internal method to get agent model by session ID and agent ID."""
        query = (
            select(SessionAgentModel)
            .options(selectinload(SessionAgentModel.messages))
            .where(
                and_(
                    SessionAgentModel.session_id == session_id,
                    SessionAgentModel.agent_id == agent_id
                )
            )
        )
        
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    async def _session_exists(self, session_id: str) -> bool:
        """Internal method to check if session exists."""
        query = select(SessionModel.session_id).where(SessionModel.session_id == session_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none() is not None