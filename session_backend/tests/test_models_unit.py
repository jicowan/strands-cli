"""Unit tests for database models."""

import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models import SessionModel, SessionAgentModel, SessionMessageModel


@pytest.mark.asyncio
class TestSessionModel:
    """Unit tests for SessionModel."""

    async def test_create_session_basic(self, test_db_session):
        """Test creating a basic session."""
        session_data = {
            "session_id": "test-session-123",
            "multi_agent_state": {"key": "value"}
        }
        
        session = SessionModel(**session_data)
        test_db_session.add(session)
        await test_db_session.commit()
        
        # Verify session was created
        result = await test_db_session.execute(
            select(SessionModel).where(SessionModel.session_id == "test-session-123")
        )
        retrieved_session = result.scalar_one()
        
        assert retrieved_session.session_id == "test-session-123"
        assert retrieved_session.multi_agent_state == {"key": "value"}
        assert isinstance(retrieved_session.created_at, datetime)
        assert isinstance(retrieved_session.updated_at, datetime)

    async def test_create_session_without_multi_agent_state(self, test_db_session):
        """Test creating a session without multi_agent_state."""
        session_data = {
            "session_id": "test-session-456"
        }
        
        session = SessionModel(**session_data)
        test_db_session.add(session)
        await test_db_session.commit()
        
        # Verify session was created
        result = await test_db_session.execute(
            select(SessionModel).where(SessionModel.session_id == "test-session-456")
        )
        retrieved_session = result.scalar_one()
        
        assert retrieved_session.session_id == "test-session-456"
        assert retrieved_session.multi_agent_state is None

    async def test_session_to_dict(self, test_db_session):
        """Test session to_dict method."""
        session_data = {
            "session_id": "test-session-dict",
            "multi_agent_state": {"test": True}
        }
        
        session = SessionModel(**session_data)
        test_db_session.add(session)
        await test_db_session.commit()
        
        session_dict = session.to_dict()
        
        assert session_dict["session_id"] == "test-session-dict"
        assert session_dict["multi_agent_state"] == {"test": True}
        assert "created_at" in session_dict
        assert "updated_at" in session_dict

    async def test_duplicate_session_id_fails(self, test_db_session):
        """Test that duplicate session IDs fail."""
        session_data = {
            "session_id": "duplicate-session",
            "multi_agent_state": {"key": "value1"}
        }
        
        # Create first session
        session1 = SessionModel(**session_data)
        test_db_session.add(session1)
        await test_db_session.commit()
        
        # Try to create second session with same ID
        session_data["multi_agent_state"] = {"key": "value2"}
        session2 = SessionModel(**session_data)
        test_db_session.add(session2)
        
        with pytest.raises(IntegrityError):
            await test_db_session.commit()


@pytest.mark.asyncio
class TestSessionAgentModel:
    """Unit tests for SessionAgentModel."""

    async def test_create_agent_basic(self, test_db_session):
        """Test creating a basic agent."""
        # Create session first
        session = SessionModel(session_id="test-session-agent")
        test_db_session.add(session)
        await test_db_session.flush()
        
        agent_data = {
            "session_id": "test-session-agent",
            "agent_id": "test-agent-123",
            "state": {"agent_state": "active"},
            "conversation_manager_state": {"messages": []},
            "internal_state": {"internal": "data"}
        }
        
        agent = SessionAgentModel(**agent_data)
        test_db_session.add(agent)
        await test_db_session.commit()
        
        # Verify agent was created
        result = await test_db_session.execute(
            select(SessionAgentModel).where(
                SessionAgentModel.session_id == "test-session-agent",
                SessionAgentModel.agent_id == "test-agent-123"
            )
        )
        retrieved_agent = result.scalar_one()
        
        assert retrieved_agent.session_id == "test-session-agent"
        assert retrieved_agent.agent_id == "test-agent-123"
        assert retrieved_agent.state == {"agent_state": "active"}
        assert retrieved_agent.conversation_manager_state == {"messages": []}
        assert retrieved_agent.internal_state == {"internal": "data"}

    async def test_create_agent_without_internal_state(self, test_db_session):
        """Test creating an agent without internal_state (should default to empty dict)."""
        # Create session first
        session = SessionModel(session_id="test-session-agent-2")
        test_db_session.add(session)
        await test_db_session.flush()
        
        agent_data = {
            "session_id": "test-session-agent-2",
            "agent_id": "test-agent-456",
            "state": {"agent_state": "active"},
            "conversation_manager_state": {"messages": []}
        }
        
        agent = SessionAgentModel(**agent_data)
        test_db_session.add(agent)
        await test_db_session.commit()
        
        # Verify agent was created with default internal_state
        result = await test_db_session.execute(
            select(SessionAgentModel).where(
                SessionAgentModel.session_id == "test-session-agent-2",
                SessionAgentModel.agent_id == "test-agent-456"
            )
        )
        retrieved_agent = result.scalar_one()
        
        assert retrieved_agent.internal_state == {}

    async def test_agent_foreign_key_constraint(self, test_db_session):
        """Test that agent creation fails without valid session."""
        agent_data = {
            "session_id": "non-existent-session",
            "agent_id": "test-agent-orphan",
            "state": {"agent_state": "active"},
            "conversation_manager_state": {"messages": []}
        }
        
        agent = SessionAgentModel(**agent_data)
        test_db_session.add(agent)
        
        with pytest.raises(IntegrityError):
            await test_db_session.commit()

    async def test_duplicate_agent_in_session_fails(self, test_db_session):
        """Test that duplicate agent IDs in same session fail."""
        # Create session first
        session = SessionModel(session_id="test-session-duplicate")
        test_db_session.add(session)
        await test_db_session.flush()
        
        agent_data = {
            "session_id": "test-session-duplicate",
            "agent_id": "duplicate-agent",
            "state": {"agent_state": "active"},
            "conversation_manager_state": {"messages": []}
        }
        
        # Create first agent
        agent1 = SessionAgentModel(**agent_data)
        test_db_session.add(agent1)
        await test_db_session.commit()
        
        # Try to create second agent with same session_id and agent_id
        agent2 = SessionAgentModel(**agent_data)
        test_db_session.add(agent2)
        
        with pytest.raises(IntegrityError):
            await test_db_session.commit()

    async def test_agent_to_dict(self, test_db_session):
        """Test agent to_dict method."""
        # Create session first
        session = SessionModel(session_id="test-session-dict-agent")
        test_db_session.add(session)
        await test_db_session.flush()
        
        agent_data = {
            "session_id": "test-session-dict-agent",
            "agent_id": "test-agent-dict",
            "state": {"test": True},
            "conversation_manager_state": {"messages": []},
            "internal_state": {"internal": "data"}
        }
        
        agent = SessionAgentModel(**agent_data)
        test_db_session.add(agent)
        await test_db_session.commit()
        
        agent_dict = agent.to_dict()
        
        assert agent_dict["session_id"] == "test-session-dict-agent"
        assert agent_dict["agent_id"] == "test-agent-dict"
        assert agent_dict["state"] == {"test": True}
        assert agent_dict["conversation_manager_state"] == {"messages": []}
        assert agent_dict["internal_state"] == {"internal": "data"}
        assert "id" in agent_dict
        assert "created_at" in agent_dict
        assert "updated_at" in agent_dict


@pytest.mark.asyncio
class TestSessionMessageModel:
    """Unit tests for SessionMessageModel."""

    async def test_create_message_basic(self, test_db_session):
        """Test creating a basic message."""
        # Create session and agent first
        session = SessionModel(session_id="test-session-message")
        test_db_session.add(session)
        await test_db_session.flush()
        
        agent = SessionAgentModel(
            session_id="test-session-message",
            agent_id="test-agent-message",
            state={"agent_state": "active"},
            conversation_manager_state={"messages": []}
        )
        test_db_session.add(agent)
        await test_db_session.flush()
        
        message_data = {
            "session_id": "test-session-message",
            "agent_id": "test-agent-message",
            "message_id": 1,
            "message": {"content": "Hello, world!", "role": "user"},
            "redact_message": {"content": "[REDACTED]", "role": "user"}
        }
        
        message = SessionMessageModel(**message_data)
        test_db_session.add(message)
        await test_db_session.commit()
        
        # Verify message was created
        result = await test_db_session.execute(
            select(SessionMessageModel).where(
                SessionMessageModel.session_id == "test-session-message",
                SessionMessageModel.agent_id == "test-agent-message",
                SessionMessageModel.message_id == 1
            )
        )
        retrieved_message = result.scalar_one()
        
        assert retrieved_message.session_id == "test-session-message"
        assert retrieved_message.agent_id == "test-agent-message"
        assert retrieved_message.message_id == 1
        assert retrieved_message.message == {"content": "Hello, world!", "role": "user"}
        assert retrieved_message.redact_message == {"content": "[REDACTED]", "role": "user"}

    async def test_create_message_without_redact(self, test_db_session):
        """Test creating a message without redact_message."""
        # Create session and agent first
        session = SessionModel(session_id="test-session-message-2")
        test_db_session.add(session)
        await test_db_session.flush()
        
        agent = SessionAgentModel(
            session_id="test-session-message-2",
            agent_id="test-agent-message-2",
            state={"agent_state": "active"},
            conversation_manager_state={"messages": []}
        )
        test_db_session.add(agent)
        await test_db_session.flush()
        
        message_data = {
            "session_id": "test-session-message-2",
            "agent_id": "test-agent-message-2",
            "message_id": 1,
            "message": {"content": "Hello, world!", "role": "user"}
        }
        
        message = SessionMessageModel(**message_data)
        test_db_session.add(message)
        await test_db_session.commit()
        
        # Verify message was created without redact_message
        result = await test_db_session.execute(
            select(SessionMessageModel).where(
                SessionMessageModel.session_id == "test-session-message-2",
                SessionMessageModel.agent_id == "test-agent-message-2",
                SessionMessageModel.message_id == 1
            )
        )
        retrieved_message = result.scalar_one()
        
        assert retrieved_message.redact_message is None

    async def test_message_foreign_key_constraint(self, test_db_session):
        """Test that message creation fails without valid agent."""
        # Create session but no agent
        session = SessionModel(session_id="test-session-message-orphan")
        test_db_session.add(session)
        await test_db_session.flush()
        
        message_data = {
            "session_id": "test-session-message-orphan",
            "agent_id": "non-existent-agent",
            "message_id": 1,
            "message": {"content": "Hello, world!", "role": "user"}
        }
        
        message = SessionMessageModel(**message_data)
        test_db_session.add(message)
        
        with pytest.raises(IntegrityError):
            await test_db_session.commit()

    async def test_duplicate_message_id_fails(self, test_db_session):
        """Test that duplicate message IDs in same session/agent fail."""
        # Create session and agent first
        session = SessionModel(session_id="test-session-message-dup")
        test_db_session.add(session)
        await test_db_session.flush()
        
        agent = SessionAgentModel(
            session_id="test-session-message-dup",
            agent_id="test-agent-message-dup",
            state={"agent_state": "active"},
            conversation_manager_state={"messages": []}
        )
        test_db_session.add(agent)
        await test_db_session.flush()
        
        message_data = {
            "session_id": "test-session-message-dup",
            "agent_id": "test-agent-message-dup",
            "message_id": 1,
            "message": {"content": "First message", "role": "user"}
        }
        
        # Create first message
        message1 = SessionMessageModel(**message_data)
        test_db_session.add(message1)
        await test_db_session.commit()
        
        # Try to create second message with same session_id, agent_id, and message_id
        message_data["message"] = {"content": "Second message", "role": "user"}
        message2 = SessionMessageModel(**message_data)
        test_db_session.add(message2)
        
        with pytest.raises(IntegrityError):
            await test_db_session.commit()

    async def test_message_to_dict(self, test_db_session):
        """Test message to_dict method."""
        # Create session and agent first
        session = SessionModel(session_id="test-session-dict-message")
        test_db_session.add(session)
        await test_db_session.flush()
        
        agent = SessionAgentModel(
            session_id="test-session-dict-message",
            agent_id="test-agent-dict-message",
            state={"agent_state": "active"},
            conversation_manager_state={"messages": []}
        )
        test_db_session.add(agent)
        await test_db_session.flush()
        
        message_data = {
            "session_id": "test-session-dict-message",
            "agent_id": "test-agent-dict-message",
            "message_id": 1,
            "message": {"content": "Test message", "role": "user"},
            "redact_message": {"content": "[REDACTED]", "role": "user"}
        }
        
        message = SessionMessageModel(**message_data)
        test_db_session.add(message)
        await test_db_session.commit()
        
        message_dict = message.to_dict()
        
        assert message_dict["session_id"] == "test-session-dict-message"
        assert message_dict["agent_id"] == "test-agent-dict-message"
        assert message_dict["message_id"] == 1
        assert message_dict["message"] == {"content": "Test message", "role": "user"}
        assert message_dict["redact_message"] == {"content": "[REDACTED]", "role": "user"}
        assert "id" in message_dict
        assert "created_at" in message_dict
        assert "updated_at" in message_dict


@pytest.mark.asyncio
class TestModelRelationships:
    """Unit tests for model relationships and cascade behavior."""

    async def test_session_agent_relationship(self, test_db_session):
        """Test session-agent relationship."""
        # Create session
        session = SessionModel(session_id="test-relationship-session")
        test_db_session.add(session)
        await test_db_session.flush()
        
        # Create agents
        agent1 = SessionAgentModel(
            session_id="test-relationship-session",
            agent_id="agent-1",
            state={"state": "1"},
            conversation_manager_state={"messages": []}
        )
        agent2 = SessionAgentModel(
            session_id="test-relationship-session",
            agent_id="agent-2",
            state={"state": "2"},
            conversation_manager_state={"messages": []}
        )
        test_db_session.add_all([agent1, agent2])
        await test_db_session.commit()
        
        # Verify relationship
        result = await test_db_session.execute(
            select(SessionModel).where(SessionModel.session_id == "test-relationship-session")
        )
        retrieved_session = result.scalar_one()
        
        assert len(retrieved_session.agents) == 2
        agent_ids = [agent.agent_id for agent in retrieved_session.agents]
        assert "agent-1" in agent_ids
        assert "agent-2" in agent_ids

    async def test_agent_message_relationship(self, test_db_session):
        """Test agent-message relationship."""
        # Create session and agent
        session = SessionModel(session_id="test-message-relationship")
        test_db_session.add(session)
        await test_db_session.flush()
        
        agent = SessionAgentModel(
            session_id="test-message-relationship",
            agent_id="test-agent-rel",
            state={"state": "active"},
            conversation_manager_state={"messages": []}
        )
        test_db_session.add(agent)
        await test_db_session.flush()
        
        # Create messages
        message1 = SessionMessageModel(
            session_id="test-message-relationship",
            agent_id="test-agent-rel",
            message_id=1,
            message={"content": "Message 1", "role": "user"}
        )
        message2 = SessionMessageModel(
            session_id="test-message-relationship",
            agent_id="test-agent-rel",
            message_id=2,
            message={"content": "Message 2", "role": "assistant"}
        )
        test_db_session.add_all([message1, message2])
        await test_db_session.commit()
        
        # Verify relationship
        result = await test_db_session.execute(
            select(SessionAgentModel).where(
                SessionAgentModel.session_id == "test-message-relationship",
                SessionAgentModel.agent_id == "test-agent-rel"
            )
        )
        retrieved_agent = result.scalar_one()
        
        assert len(retrieved_agent.messages) == 2
        message_ids = [msg.message_id for msg in retrieved_agent.messages]
        assert 1 in message_ids
        assert 2 in message_ids

    async def test_cascade_delete_session_removes_agents_and_messages(self, test_db_session):
        """Test that deleting a session cascades to agents and messages."""
        # Create session
        session = SessionModel(session_id="test-cascade-delete")
        test_db_session.add(session)
        await test_db_session.flush()
        
        # Create agent
        agent = SessionAgentModel(
            session_id="test-cascade-delete",
            agent_id="test-agent-cascade",
            state={"state": "active"},
            conversation_manager_state={"messages": []}
        )
        test_db_session.add(agent)
        await test_db_session.flush()
        
        # Create message
        message = SessionMessageModel(
            session_id="test-cascade-delete",
            agent_id="test-agent-cascade",
            message_id=1,
            message={"content": "Test message", "role": "user"}
        )
        test_db_session.add(message)
        await test_db_session.commit()
        
        # Verify everything exists
        session_count = await test_db_session.scalar(
            select(SessionModel).where(SessionModel.session_id == "test-cascade-delete")
        )
        agent_count = await test_db_session.scalar(
            select(SessionAgentModel).where(SessionAgentModel.session_id == "test-cascade-delete")
        )
        message_count = await test_db_session.scalar(
            select(SessionMessageModel).where(SessionMessageModel.session_id == "test-cascade-delete")
        )
        
        assert session_count is not None
        assert agent_count is not None
        assert message_count is not None
        
        # Delete session
        await test_db_session.delete(session)
        await test_db_session.commit()
        
        # Verify cascade delete worked
        remaining_agents = await test_db_session.execute(
            select(SessionAgentModel).where(SessionAgentModel.session_id == "test-cascade-delete")
        )
        remaining_messages = await test_db_session.execute(
            select(SessionMessageModel).where(SessionMessageModel.session_id == "test-cascade-delete")
        )
        
        assert len(remaining_agents.scalars().all()) == 0
        assert len(remaining_messages.scalars().all()) == 0