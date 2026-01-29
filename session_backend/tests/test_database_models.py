"""Property-based tests for database models and referential integrity."""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from typing import Dict, Any

from app.models import SessionModel, SessionAgentModel, SessionMessageModel


# Test data generators
@st.composite
def session_data(draw):
    """Generate valid session data with PostgreSQL-safe characters."""
    # Use ASCII-safe characters to avoid PostgreSQL Unicode issues
    session_id = draw(st.text(
        min_size=1, 
        max_size=100, 
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    ))
    
    safe_alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !@#$%^&*()_+-=[]{}|;:,.<>?"
    
    multi_agent_state = draw(st.one_of(
        st.none(),
        st.dictionaries(
            st.text(
                min_size=1, 
                max_size=50,
                alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
            ),
            st.one_of(
                st.text(alphabet=safe_alphabet), 
                st.integers(), 
                st.booleans(), 
                st.none()
            ),
            min_size=0,
            max_size=5
        )
    ))
    return {
        "session_id": session_id,
        "multi_agent_state": multi_agent_state
    }


@st.composite
def agent_data(draw, session_id: str):
    """Generate valid agent data for a given session with PostgreSQL-safe characters."""
    agent_id = draw(st.text(
        min_size=1, 
        max_size=100, 
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    ))
    
    safe_alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !@#$%^&*()_+-=[]{}|;:,.<>?"
    
    state = draw(st.dictionaries(
        st.text(
            min_size=1, 
            max_size=50,
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        ),
        st.one_of(
            st.text(alphabet=safe_alphabet), 
            st.integers(), 
            st.booleans()
        ),
        min_size=1,
        max_size=5
    ))
    conversation_manager_state = draw(st.dictionaries(
        st.text(
            min_size=1, 
            max_size=50,
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        ),
        st.one_of(
            st.text(alphabet=safe_alphabet), 
            st.integers(), 
            st.booleans()
        ),
        min_size=1,
        max_size=5
    ))
    internal_state = draw(st.dictionaries(
        st.text(
            min_size=1, 
            max_size=50,
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        ),
        st.one_of(
            st.text(alphabet=safe_alphabet), 
            st.integers(), 
            st.booleans()
        ),
        min_size=0,
        max_size=3
    ))
    
    return {
        "session_id": session_id,
        "agent_id": agent_id,
        "state": state,
        "conversation_manager_state": conversation_manager_state,
        "internal_state": internal_state
    }


@st.composite
def message_data(draw, session_id: str, agent_id: str):
    """Generate valid message data for a given session and agent with PostgreSQL-safe characters."""
    message_id = draw(st.integers(min_value=1, max_value=1000))
    
    safe_alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !@#$%^&*()_+-=[]{}|;:,.<>?"
    
    message = draw(st.dictionaries(
        st.text(
            min_size=1, 
            max_size=50,
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        ),
        st.one_of(
            st.text(alphabet=safe_alphabet), 
            st.integers(), 
            st.booleans()
        ),
        min_size=1,
        max_size=5
    ))
    redact_message = draw(st.one_of(
        st.none(),
        st.dictionaries(
            st.text(
                min_size=1, 
                max_size=50,
                alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
            ),
            st.one_of(
                st.text(alphabet=safe_alphabet), 
                st.integers(), 
                st.booleans()
            ),
            min_size=0,
            max_size=3
        )
    ))
    
    return {
        "session_id": session_id,
        "agent_id": agent_id,
        "message_id": message_id,
        "message": message,
        "redact_message": redact_message
    }


@pytest.mark.asyncio
class TestDatabaseReferentialIntegrity:
    """Property-based tests for database referential integrity.
    
    **Feature: session-backend-api, Property 12: Database Referential Integrity**
    """

    @given(agent_data_gen=st.data())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_orphaned_agent_creation_fails(self, agent_data_gen, test_db_session):
        """
        Property 12: Database Referential Integrity
        For any attempt to create orphaned records (agents without sessions), 
        the database should reject the operation.
        **Validates: Requirements 5.2**
        """
        # Generate session data
        session_data_gen = agent_data_gen.draw(session_data())
        
        # Generate agent data for a non-existent session
        non_existent_session_id = agent_data_gen.draw(st.text(
            min_size=1, 
            max_size=50,
            alphabet=st.characters(min_codepoint=65, max_codepoint=90)  # A-Z only for uniqueness
        ))
        agent_data_dict = agent_data_gen.draw(agent_data(non_existent_session_id))
        
        # Ensure the session doesn't exist by using a unique identifier
        assume(non_existent_session_id not in ["test_session", "existing_session"])
        assume(non_existent_session_id != session_data_gen["session_id"])
        
        # Verify session doesn't exist
        result = await test_db_session.execute(select(SessionModel).where(SessionModel.session_id == non_existent_session_id))
        existing_session = result.scalar_one_or_none()
        assume(existing_session is None)
        
        # Try to create agent without session - should fail
        agent = SessionAgentModel(**agent_data_dict)
        test_db_session.add(agent)
        
        with pytest.raises(IntegrityError):
            await test_db_session.commit()
        
        await test_db_session.rollback()

    @given(message_data_gen=st.data())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_orphaned_message_creation_fails(self, message_data_gen, test_db_session):
        """
        Property 12: Database Referential Integrity
        For any attempt to create orphaned records (messages without agents), 
        the database should reject the operation.
        **Validates: Requirements 5.2**
        """
        # Generate session data
        session_data_gen = message_data_gen.draw(session_data())
        
        # Create a session first
        session = SessionModel(**session_data_gen)
        test_db_session.add(session)
        await test_db_session.commit()
        
        # Generate message data for a non-existent agent
        non_existent_agent_id = message_data_gen.draw(st.text(min_size=1, max_size=100))
        message_data_dict = message_data_gen.draw(message_data(session_data_gen["session_id"], non_existent_agent_id))
        
        # Verify agent doesn't exist
        result = await test_db_session.execute(
            select(SessionAgentModel).where(
                SessionAgentModel.session_id == session_data_gen["session_id"],
                SessionAgentModel.agent_id == non_existent_agent_id
            )
        )
        existing_agent = result.scalar_one_or_none()
        assume(existing_agent is None)
        
        # Try to create message without agent - should fail
        message = SessionMessageModel(**message_data_dict)
        test_db_session.add(message)
        
        with pytest.raises(IntegrityError):
            await test_db_session.commit()
        
        await test_db_session.rollback()

    @given(agent_data_gen=st.data())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_cascade_delete_removes_agents(self, agent_data_gen, test_db_session):
        """
        Property 12: Database Referential Integrity
        For any session with associated agents, deleting the session should 
        cascade delete all associated agents.
        **Validates: Requirements 5.2**
        """
        # Generate session data
        session_data_gen = agent_data_gen.draw(session_data())
        
        # Create session
        session = SessionModel(**session_data_gen)
        test_db_session.add(session)
        await test_db_session.flush()  # Get the session ID
        
        # Create multiple agents for the session
        agents_data = [
            agent_data_gen.draw(agent_data(session_data_gen["session_id"]))
            for _ in range(agent_data_gen.draw(st.integers(min_value=1, max_value=3)))
        ]
        
        agents = []
        for agent_data_dict in agents_data:
            agent = SessionAgentModel(**agent_data_dict)
            test_db_session.add(agent)
            agents.append(agent)
        
        await test_db_session.commit()
        
        # Verify agents exist
        result = await test_db_session.execute(
            select(SessionAgentModel).where(SessionAgentModel.session_id == session_data_gen["session_id"])
        )
        existing_agents = result.scalars().all()
        assert len(existing_agents) == len(agents_data)
        
        # Delete the session
        await test_db_session.delete(session)
        await test_db_session.commit()
        
        # Verify all agents are cascade deleted
        result = await test_db_session.execute(
            select(SessionAgentModel).where(SessionAgentModel.session_id == session_data_gen["session_id"])
        )
        remaining_agents = result.scalars().all()
        assert len(remaining_agents) == 0

    @given(message_data_gen=st.data())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_cascade_delete_removes_messages(self, message_data_gen, test_db_session):
        """
        Property 12: Database Referential Integrity
        For any agent with associated messages, deleting the agent should 
        cascade delete all associated messages.
        **Validates: Requirements 5.2**
        """
        # Generate session and agent data
        session_data_gen = message_data_gen.draw(session_data())
        agent_data_dict = message_data_gen.draw(agent_data(session_data_gen["session_id"]))
        
        # Create session
        session = SessionModel(**session_data_gen)
        test_db_session.add(session)
        await test_db_session.flush()
        
        # Create agent
        agent = SessionAgentModel(**agent_data_dict)
        test_db_session.add(agent)
        await test_db_session.flush()
        
        # Create multiple messages for the agent
        messages_data = []
        for i in range(message_data_gen.draw(st.integers(min_value=1, max_value=3))):
            message_data_dict = message_data_gen.draw(message_data(session_data_gen["session_id"], agent_data_dict["agent_id"]))
            # Ensure unique message IDs
            message_data_dict["message_id"] = i + 1
            messages_data.append(message_data_dict)
        
        messages = []
        for message_data_dict in messages_data:
            message = SessionMessageModel(**message_data_dict)
            test_db_session.add(message)
            messages.append(message)
        
        await test_db_session.commit()
        
        # Verify messages exist
        result = await test_db_session.execute(
            select(SessionMessageModel).where(
                SessionMessageModel.session_id == session_data_gen["session_id"],
                SessionMessageModel.agent_id == agent_data_dict["agent_id"]
            )
        )
        existing_messages = result.scalars().all()
        assert len(existing_messages) == len(messages_data)
        
        # Delete the agent
        await test_db_session.delete(agent)
        await test_db_session.commit()
        
        # Verify all messages are cascade deleted
        result = await test_db_session.execute(
            select(SessionMessageModel).where(
                SessionMessageModel.session_id == session_data_gen["session_id"],
                SessionMessageModel.agent_id == agent_data_dict["agent_id"]
            )
        )
        remaining_messages = result.scalars().all()
        assert len(remaining_messages) == 0