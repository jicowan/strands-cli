"""SessionAgent model for SQLAlchemy ORM."""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any

from ..database import Base


class SessionAgentModel(Base):
    """SQLAlchemy model for session_agents table."""
    
    __tablename__ = "session_agents"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to sessions
    session_id = Column(
        String(255), 
        ForeignKey("sessions.session_id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # Agent identification
    agent_id = Column(String(255), nullable=False)
    
    # Agent state data
    state = Column(JSONB, nullable=False)
    conversation_manager_state = Column(JSONB, nullable=False)
    internal_state = Column(JSONB, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('session_id', 'agent_id', name='uq_session_agent'),
    )
    
    # Relationships
    session = relationship(
        "SessionModel", 
        back_populates="agents"
    )
    messages = relationship(
        "SessionMessageModel", 
        back_populates="agent", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<SessionAgentModel(session_id='{self.session_id}', agent_id='{self.agent_id}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "state": self.state,
            "conversation_manager_state": self.conversation_manager_state,
            "internal_state": self.internal_state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }