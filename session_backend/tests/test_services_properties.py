"""Property-based tests for service layer business logic."""

import pytest
import pytest_asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.strategies import composite
from typing import Dict, Any, Optional
import uuid
import json
import base64

from app.services import SessionService, AgentService, MessageService
from app.schemas.session import SessionCreate, SessionUpdate
from app.schemas.agent import SessionAgentCreate, SessionAgentUpdate
from app.schemas.message import SessionMessageCreate, SessionMessageUpdate, MessagePaginationQuery


# Custom strategies for generating test data
@composite
def session_id_strategy(draw):
    """Generate valid session IDs."""
    # Generate unique session IDs using UUID to avoid conflicts
    import uuid
    base_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
    return base_id


@composite
def agent_id_strategy(draw):
    """Generate valid agent IDs."""
    # Generate unique agent IDs using UUID to avoid conflicts
    import uuid
    base_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
    return f"agent-{base_id}"


@composite
def json_dict_strategy(draw):
    """Generate realistic JSON dictionaries that reflect actual agent state."""
    # Generate realistic keys that would appear in agent state
    possible_keys = [
        "tools", "model", "temperature", "max_tokens", "system_prompt", 
        "conversation_history", "memory", "context", "settings", "metadata",
        "session_id", "agent_id", "timestamp", "version", "config"
    ]
    
    keys = draw(st.lists(
        st.sampled_from(possible_keys),
        min_size=1,
        max_size=5,
        unique=True
    ))
    
    result = {}
    for key in keys:
        value_type = draw(st.sampled_from(["string", "number", "boolean", "list", "null"]))
        
        if value_type == "string":
            result[key] = draw(st.text(
                alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?'-_",
                min_size=1,
                max_size=50
            ))
        elif value_type == "number":
            result[key] = draw(st.integers(min_value=0, max_value=10000))
        elif value_type == "boolean":
            result[key] = draw(st.booleans())
        elif value_type == "list":
            result[key] = draw(st.lists(
                st.text(
                    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
                    min_size=1,
                    max_size=20
                ),
                max_size=3
            ))
        else:  # null
            result[key] = None
    
    return result


@composite
def session_create_strategy(draw):
    """Generate SessionCreate objects."""
    session_id = draw(session_id_strategy())
    multi_agent_state = draw(st.one_of(st.none(), json_dict_strategy()))
    
    return SessionCreate(
        session_id=session_id,
        multi_agent_state=multi_agent_state
    )


@composite
def session_update_strategy(draw):
    """Generate SessionUpdate objects."""
    multi_agent_state = draw(st.one_of(st.none(), json_dict_strategy()))
    
    return SessionUpdate(
        multi_agent_state=multi_agent_state
    )


@composite
def agent_state_strategy(draw):
    """Generate agent state with potential binary data."""
    base_state = draw(json_dict_strategy())
    
    # Sometimes add binary data (encoded as base64)
    if draw(st.booleans()):
        binary_data = draw(st.binary(min_size=1, max_size=100))
        base_state["binary_field"] = {
            "_type": "binary",
            "_data": base64.b64encode(binary_data).decode('utf-8')
        }
    
    return base_state


@composite
def agent_create_strategy(draw):
    """Generate SessionAgentCreate objects."""
    agent_id = draw(agent_id_strategy())
    state = draw(agent_state_strategy())
    conversation_manager_state = draw(json_dict_strategy())
    internal_state = draw(json_dict_strategy())
    
    return SessionAgentCreate(
        agent_id=agent_id,
        state=state,
        conversation_manager_state=conversation_manager_state,
        internal_state=internal_state
    )


@composite
def message_strategy(draw):
    """Generate realistic Strands message format that reflects actual agent output."""
    role = draw(st.sampled_from(["user", "assistant", "system", "tool", "function"]))
    
    # Generate realistic content that an agent might actually produce
    content_type = draw(st.sampled_from([
        "plain_text",
        "code_snippet", 
        "json_response",
        "markdown",
        "tool_call"
    ]))
    
    if content_type == "plain_text":
        # Normal conversational text
        content = draw(st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?'-",
            min_size=1, 
            max_size=200
        ))
    elif content_type == "code_snippet":
        # Code-like content
        content = draw(st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 (){}[];=.,_-",
            min_size=1, 
            max_size=100
        ))
    elif content_type == "json_response":
        # JSON-like structured response
        content = '{"result": "' + draw(st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?",
            min_size=1, 
            max_size=50
        )) + '"}'
    elif content_type == "markdown":
        # Markdown content
        content = "## " + draw(st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?",
            min_size=1, 
            max_size=50
        ))
    else:  # tool_call
        # Tool call content
        content = "Calling tool: " + draw(st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
            min_size=1, 
            max_size=30
        ))
    
    message = {
        "role": role,
        "content": content
    }
    
    # Sometimes add realistic metadata
    if draw(st.booleans()):
        message["timestamp"] = "2024-01-01T12:00:00Z"
    
    if draw(st.booleans()):
        message["metadata"] = {
            "model": draw(st.sampled_from(["gpt-4", "claude-3", "bedrock-titan"])),
            "tokens": draw(st.integers(min_value=10, max_value=1000))
        }
    
    return message


@composite
def message_create_strategy(draw):
    """Generate SessionMessageCreate objects."""
    message_id = draw(st.integers(min_value=0, max_value=10000))
    message = draw(message_strategy())
    redact_message = draw(st.one_of(st.none(), message_strategy()))
    
    return SessionMessageCreate(
        message_id=message_id,
        message=message,
        redact_message=redact_message
    )


class TestSessionServiceProperties:
    """Property-based tests for SessionService."""
    
    @given(session_data=session_create_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_session_storage_and_retrieval_integrity(self, test_db_session, session_data):
        """
        Property 1: Session Storage and Retrieval Integrity
        For any valid session data, creating a session then retrieving it should return equivalent session data with the same session ID.
        **Validates: Requirements 1.1, 1.2**
        """
        # Feature: session-backend-api, Property 1: Session Storage and Retrieval Integrity
        service = SessionService(test_db_session)
        
        # Create session
        created_session = await service.create_session(session_data)
        
        # Retrieve session
        retrieved_session = await service.get_session(session_data.session_id)
        
        # Verify session was retrieved
        assert retrieved_session is not None
        
        # Verify session ID matches
        assert retrieved_session.session_id == session_data.session_id
        assert retrieved_session.session_id == created_session.session_id
        
        # Verify multi_agent_state matches
        assert retrieved_session.multi_agent_state == session_data.multi_agent_state
        assert retrieved_session.multi_agent_state == created_session.multi_agent_state
        
        # Verify timestamps are present and consistent
        assert retrieved_session.created_at == created_session.created_at
        assert retrieved_session.updated_at == created_session.updated_at
    
    @given(session_data=session_create_strategy(), update_data=session_update_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_session_update_persistence(self, test_db_session, session_data, update_data):
        """
        Property 2: Session Update Persistence
        For any existing session and valid update data, updating the session then retrieving it should return the updated data.
        **Validates: Requirements 1.3**
        """
        # Feature: session-backend-api, Property 2: Session Update Persistence
        service = SessionService(test_db_session)
        
        # Create initial session
        created_session = await service.create_session(session_data)
        
        # Update session
        updated_session = await service.update_session(session_data.session_id, update_data)
        
        # Verify update was successful
        assert updated_session is not None
        
        # Retrieve session again
        retrieved_session = await service.get_session(session_data.session_id)
        
        # Verify session was retrieved
        assert retrieved_session is not None
        
        # Verify session ID remains the same
        assert retrieved_session.session_id == session_data.session_id
        
        # Verify updated data persisted
        expected_state = update_data.multi_agent_state if update_data.multi_agent_state is not None else session_data.multi_agent_state
        assert retrieved_session.multi_agent_state == expected_state
        assert retrieved_session.multi_agent_state == updated_session.multi_agent_state
        
        # Verify updated_at timestamp changed (should be >= created_at)
        assert retrieved_session.updated_at >= retrieved_session.created_at


class TestAgentServiceProperties:
    """Property-based tests for AgentService."""
    
    @given(session_data=session_create_strategy(), agent_data=agent_create_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_agent_association_and_retrieval(self, test_db_session, session_data, agent_data):
        """
        Property 4: Agent Association and Retrieval
        For any valid agent data and existing session, creating an agent then retrieving it should return equivalent agent data with proper session association.
        **Validates: Requirements 2.1, 2.3**
        """
        # Feature: session-backend-api, Property 4: Agent Association and Retrieval
        session_service = SessionService(test_db_session)
        agent_service = AgentService(test_db_session)
        
        # Create session first
        await session_service.create_session(session_data)
        
        # Create agent
        created_agent = await agent_service.create_agent(session_data.session_id, agent_data)
        
        # Retrieve agent
        retrieved_agent = await agent_service.get_agent(session_data.session_id, agent_data.agent_id)
        
        # Verify agent was retrieved
        assert retrieved_agent is not None
        
        # Verify agent ID matches
        assert retrieved_agent.agent_id == agent_data.agent_id
        assert retrieved_agent.agent_id == created_agent.agent_id
        
        # Verify state data matches
        assert retrieved_agent.state == agent_data.state
        assert retrieved_agent.conversation_manager_state == agent_data.conversation_manager_state
        assert retrieved_agent.internal_state == agent_data.internal_state
        
        # Verify state data matches created agent
        assert retrieved_agent.state == created_agent.state
        assert retrieved_agent.conversation_manager_state == created_agent.conversation_manager_state
        assert retrieved_agent.internal_state == created_agent.internal_state
        
        # Verify timestamps are present and consistent
        assert retrieved_agent.created_at == created_agent.created_at
        assert retrieved_agent.updated_at == created_agent.updated_at
    
    @given(session_data=session_create_strategy(), agent_list=st.lists(agent_create_strategy(), min_size=2, max_size=5))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_multiple_agents_per_session(self, test_db_session, session_data, agent_list):
        """
        Property 5: Multiple Agents Per Session
        For any session, creating multiple agents with different agent IDs should result in all agents being retrievable from that session.
        **Validates: Requirements 2.4**
        """
        # Feature: session-backend-api, Property 5: Multiple Agents Per Session
        
        # Ensure all agent IDs are unique
        unique_agents = []
        seen_ids = set()
        for agent in agent_list:
            if agent.agent_id not in seen_ids:
                unique_agents.append(agent)
                seen_ids.add(agent.agent_id)
        
        assume(len(unique_agents) >= 2)  # Need at least 2 unique agents
        
        session_service = SessionService(test_db_session)
        agent_service = AgentService(test_db_session)
        
        # Create session first
        await session_service.create_session(session_data)
        
        # Create all agents
        created_agents = []
        for agent_data in unique_agents:
            created_agent = await agent_service.create_agent(session_data.session_id, agent_data)
            created_agents.append(created_agent)
        
        # Retrieve all agents from session
        retrieved_agents = await agent_service.get_agents_by_session(session_data.session_id)
        
        # Verify all agents were retrieved
        assert len(retrieved_agents) == len(unique_agents)
        
        # Verify all agent IDs are present
        retrieved_agent_ids = {agent.agent_id for agent in retrieved_agents}
        expected_agent_ids = {agent.agent_id for agent in unique_agents}
        assert retrieved_agent_ids == expected_agent_ids
        
        # Verify each agent can be retrieved individually
        for agent_data in unique_agents:
            individual_agent = await agent_service.get_agent(session_data.session_id, agent_data.agent_id)
            assert individual_agent is not None
            assert individual_agent.agent_id == agent_data.agent_id


class TestSessionCascadeDeletion:
    """Property-based tests for session cascade deletion."""
    
    @given(
        session_data=session_create_strategy(),
        agent_list=st.lists(agent_create_strategy(), min_size=1, max_size=3),
        message_list=st.lists(message_create_strategy(), min_size=1, max_size=5)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_session_cascade_deletion(self, test_db_session, session_data, agent_list, message_list):
        """
        Property 3: Session Cascade Deletion
        For any session with associated agents and messages, deleting the session should remove all associated data from the database.
        **Validates: Requirements 1.4**
        """
        # Feature: session-backend-api, Property 3: Session Cascade Deletion
        
        # Ensure all agent IDs are unique
        unique_agents = []
        seen_ids = set()
        for agent in agent_list:
            if agent.agent_id not in seen_ids:
                unique_agents.append(agent)
                seen_ids.add(agent.agent_id)
        
        assume(len(unique_agents) >= 1)  # Need at least 1 unique agent
        
        # Ensure all message IDs are unique per agent
        unique_messages = []
        seen_message_ids = set()
        for message in message_list:
            if message.message_id not in seen_message_ids:
                unique_messages.append(message)
                seen_message_ids.add(message.message_id)
        
        assume(len(unique_messages) >= 1)  # Need at least 1 unique message
        
        session_service = SessionService(test_db_session)
        agent_service = AgentService(test_db_session)
        message_service = MessageService(test_db_session)
        
        # Create session
        await session_service.create_session(session_data)
        
        # Create agents
        created_agents = []
        for agent_data in unique_agents:
            created_agent = await agent_service.create_agent(session_data.session_id, agent_data)
            created_agents.append(created_agent)
        
        # Create messages for each agent
        created_messages = []
        for agent_data in unique_agents:
            for message_data in unique_messages:
                # Create unique message ID per agent to avoid conflicts
                unique_message_data = SessionMessageCreate(
                    message_id=message_data.message_id,
                    message=message_data.message,
                    redact_message=message_data.redact_message
                )
                created_message = await message_service.create_message(
                    session_data.session_id, 
                    agent_data.agent_id, 
                    unique_message_data
                )
                created_messages.append(created_message)
        
        # Verify all data exists before deletion
        retrieved_session = await session_service.get_session(session_data.session_id)
        assert retrieved_session is not None
        
        retrieved_agents = await agent_service.get_agents_by_session(session_data.session_id)
        assert len(retrieved_agents) == len(unique_agents)
        
        # Count total messages across all agents
        total_messages = 0
        for agent_data in unique_agents:
            pagination = MessagePaginationQuery(page=1, page_size=100, order="asc")
            result = await message_service.list_messages(session_data.session_id, agent_data.agent_id, pagination)
            total_messages += len(result.messages)
        
        assert total_messages == len(unique_agents) * len(unique_messages)
        
        # Delete the session (should cascade delete all associated data)
        await session_service.delete_session(session_data.session_id)
        
        # Verify session is deleted
        deleted_session = await session_service.get_session(session_data.session_id)
        assert deleted_session is None
        
        # Verify all agents are deleted
        remaining_agents = await agent_service.get_agents_by_session(session_data.session_id)
        assert len(remaining_agents) == 0
        
        # Verify all messages are deleted
        for agent_data in unique_agents:
            pagination = MessagePaginationQuery(page=1, page_size=100, order="asc")
            result = await message_service.list_messages(session_data.session_id, agent_data.agent_id, pagination)
            assert len(result.messages) == 0


class TestMessageServiceProperties:
    """Property-based tests for MessageService."""
    
    @given(
        session_data=session_create_strategy(),
        agent_data=agent_create_strategy(),
        message_list=st.lists(message_create_strategy(), min_size=3, max_size=10)
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_message_chronological_ordering(self, test_db_session, session_data, agent_data, message_list):
        """
        Property 7: Message Chronological Ordering
        For any sequence of messages added to a session, retrieving the messages should return them in chronological order regardless of insertion order.
        **Validates: Requirements 3.1, 3.2**
        """
        # Feature: session-backend-api, Property 7: Message Chronological Ordering
        
        # Ensure all message IDs are unique
        unique_messages = []
        seen_ids = set()
        for message in message_list:
            if message.message_id not in seen_ids:
                unique_messages.append(message)
                seen_ids.add(message.message_id)
        
        assume(len(unique_messages) >= 3)  # Need at least 3 unique messages
        
        session_service = SessionService(test_db_session)
        agent_service = AgentService(test_db_session)
        message_service = MessageService(test_db_session)
        
        # Create session and agent
        await session_service.create_session(session_data)
        await agent_service.create_agent(session_data.session_id, agent_data)
        
        # Insert messages in random order (shuffle the list)
        import random
        shuffled_messages = unique_messages.copy()
        random.shuffle(shuffled_messages)
        
        # Create all messages
        for message_data in shuffled_messages:
            await message_service.create_message(session_data.session_id, agent_data.agent_id, message_data)
        
        # Retrieve messages in ascending order
        pagination = MessagePaginationQuery(page=1, page_size=100, order="asc")
        result = await message_service.list_messages(session_data.session_id, agent_data.agent_id, pagination)
        
        # Verify messages are in chronological order (ascending by message_id)
        retrieved_message_ids = [msg.message_id for msg in result.messages]
        expected_message_ids = sorted([msg.message_id for msg in unique_messages])
        assert retrieved_message_ids == expected_message_ids
        
        # Verify all messages were retrieved
        assert len(result.messages) == len(unique_messages)
        
        # Test descending order as well
        pagination_desc = MessagePaginationQuery(page=1, page_size=100, order="desc")
        result_desc = await message_service.list_messages(session_data.session_id, agent_data.agent_id, pagination_desc)
        
        # Verify messages are in reverse chronological order
        retrieved_message_ids_desc = [msg.message_id for msg in result_desc.messages]
        expected_message_ids_desc = sorted([msg.message_id for msg in unique_messages], reverse=True)
        assert retrieved_message_ids_desc == expected_message_ids_desc
    
    @given(
        session_data=session_create_strategy(),
        agent_data=agent_create_strategy(),
        message_list=st.lists(message_create_strategy(), min_size=25, max_size=50),
        page_size=st.integers(min_value=5, max_value=15)
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_message_pagination_consistency(self, test_db_session, session_data, agent_data, message_list, page_size):
        """
        Property 8: Message Pagination Consistency
        For any large set of messages, paginated retrieval should return all messages exactly once across all pages in correct order.
        **Validates: Requirements 3.3**
        """
        # Feature: session-backend-api, Property 8: Message Pagination Consistency
        
        # Ensure all message IDs are unique
        unique_messages = []
        seen_ids = set()
        for message in message_list:
            if message.message_id not in seen_ids:
                unique_messages.append(message)
                seen_ids.add(message.message_id)
        
        assume(len(unique_messages) >= 25)  # Need enough messages for pagination
        
        session_service = SessionService(test_db_session)
        agent_service = AgentService(test_db_session)
        message_service = MessageService(test_db_session)
        
        # Create session and agent
        await session_service.create_session(session_data)
        await agent_service.create_agent(session_data.session_id, agent_data)
        
        # Create all messages
        for message_data in unique_messages:
            await message_service.create_message(session_data.session_id, agent_data.agent_id, message_data)
        
        # Retrieve all messages through pagination
        all_paginated_messages = []
        page = 1
        
        while True:
            pagination = MessagePaginationQuery(page=page, page_size=page_size, order="asc")
            result = await message_service.list_messages(session_data.session_id, agent_data.agent_id, pagination)
            
            if not result.messages:
                break
            
            all_paginated_messages.extend(result.messages)
            
            # Verify pagination metadata
            assert result.page == page
            assert result.page_size == page_size
            assert result.total == len(unique_messages)
            
            # If this is the last page, break
            if len(result.messages) < page_size:
                break
            
            page += 1
        
        # Verify all messages were retrieved exactly once
        paginated_message_ids = [msg.message_id for msg in all_paginated_messages]
        expected_message_ids = sorted([msg.message_id for msg in unique_messages])
        
        assert len(paginated_message_ids) == len(expected_message_ids)
        assert paginated_message_ids == expected_message_ids
        
        # Verify no duplicates
        assert len(set(paginated_message_ids)) == len(paginated_message_ids)
    
    @given(
        session_data=session_create_strategy(),
        agent_data=agent_create_strategy(),
        message_data=message_create_strategy()
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_message_metadata_preservation(self, test_db_session, session_data, agent_data, message_data):
        """
        Property 9: Message Metadata Preservation
        For any message with metadata, storing then retrieving the message should preserve all timestamps, roles, and content types.
        **Validates: Requirements 3.4**
        """
        # Feature: session-backend-api, Property 9: Message Metadata Preservation
        
        session_service = SessionService(test_db_session)
        agent_service = AgentService(test_db_session)
        message_service = MessageService(test_db_session)
        
        # Create session and agent
        await session_service.create_session(session_data)
        await agent_service.create_agent(session_data.session_id, agent_data)
        
        # Create message with metadata
        created_message = await message_service.create_message(session_data.session_id, agent_data.agent_id, message_data)
        
        # Retrieve the message
        retrieved_message = await message_service.get_message(
            session_data.session_id, 
            agent_data.agent_id, 
            message_data.message_id
        )
        
        # Verify message was retrieved
        assert retrieved_message is not None
        
        # Verify message ID matches
        assert retrieved_message.message_id == message_data.message_id
        assert retrieved_message.message_id == created_message.message_id
        
        # Verify message content is preserved exactly
        assert retrieved_message.message == message_data.message
        assert retrieved_message.message == created_message.message
        
        # Verify redact_message is preserved exactly
        assert retrieved_message.redact_message == message_data.redact_message
        assert retrieved_message.redact_message == created_message.redact_message
        
        # Verify timestamps are preserved and consistent
        assert retrieved_message.created_at == created_message.created_at
        assert retrieved_message.updated_at == created_message.updated_at
        
        # Verify timestamps are present (not None)
        assert retrieved_message.created_at is not None
        assert retrieved_message.updated_at is not None
        
        # Verify message metadata within the message content is preserved
        if "metadata" in message_data.message:
            assert "metadata" in retrieved_message.message
            assert retrieved_message.message["metadata"] == message_data.message["metadata"]
        
        if "role" in message_data.message:
            assert "role" in retrieved_message.message
            assert retrieved_message.message["role"] == message_data.message["role"]
        
        if "timestamp" in message_data.message:
            assert "timestamp" in retrieved_message.message
            assert retrieved_message.message["timestamp"] == message_data.message["timestamp"]
        
        # Verify content type preservation (if present)
        if "content" in message_data.message:
            assert "content" in retrieved_message.message
            assert retrieved_message.message["content"] == message_data.message["content"]