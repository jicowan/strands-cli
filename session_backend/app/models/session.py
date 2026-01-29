"""Session model for SQLAlchemy ORM - Strands compatible."""

from sqlalchemy import Column, String, DateTime, func, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
import enum

from ..database import Base


class SessionTypeEnum(enum.Enum):
    """Session type enumeration for database."""
    AGENT = "AGENT"


class SessionModel(Base):
    """SQLAlchemy model for sessions table - matches Strands Session format."""
    
    __tablename__ = "sessions"
    
    # Primary key
    session_id = Column(String(255), primary_key=True, nullable=False)
    
    # Session type (matches Strands SessionType)
    session_type = Column(
        Enum(SessionTypeEnum, name='session_type_enum', create_type=False), 
        nullable=False, 
        default=SessionTypeEnum.AGENT
    )
    
    # Timestamps (stored as strings to match Strands format)
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
    
    # Relationships
    agents = relationship(
        "SessionAgentModel", 
        back_populates="session", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<SessionModel(session_id='{self.session_id}', session_type='{self.session_type.value}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary in Strands format."""
        return {
            "session_id": self.session_id,
            "session_type": self.session_type.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }