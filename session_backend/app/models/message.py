"""SessionMessage model for SQLAlchemy ORM."""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint, ForeignKeyConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional

from ..database import Base


class SessionMessageModel(Base):
    """SQLAlchemy model for session_messages table."""
    
    __tablename__ = "session_messages"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    session_id = Column(String(255), nullable=False)
    agent_id = Column(String(255), nullable=False)
    
    # Message identification
    message_id = Column(Integer, nullable=False)
    
    # Message data
    message = Column(JSONB, nullable=False)
    redact_message = Column(JSONB, nullable=True)
    
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
        UniqueConstraint('session_id', 'agent_id', 'message_id', name='uq_session_agent_message'),
        ForeignKeyConstraint(
            ['session_id', 'agent_id'], 
            ['session_agents.session_id', 'session_agents.agent_id'],
            ondelete="CASCADE",
            name='fk_session_agent'
        ),
    )
    
    # Relationships
    agent = relationship(
        "SessionAgentModel", 
        back_populates="messages"
    )
    
    def __repr__(self) -> str:
        return f"<SessionMessageModel(session_id='{self.session_id}', agent_id='{self.agent_id}', message_id={self.message_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "message_id": self.message_id,
            "message": self.message,
            "redact_message": self.redact_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }