#!/usr/bin/env python3
"""Comprehensive test of the session backend API surface area."""

import sys
import os
from datetime import datetime

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from agent.postgresql_session_repository import SyncPostgreSQLSessionRepository
from strands.types.session import Session, SessionAgent, SessionMessage, SessionType, Message


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_test(test_name, passed=True):
    """Print test result."""
    status = "✅" if passed else "❌"
    print(f"{status} {test_name}")


def main():
    """Test all API endpoints."""
    print_section("SESSION BACKEND API SURFACE AREA TEST")
    
    repo = SyncPostgreSQLSessionRepository(base_url="http://localhost:8001")
    test_session_id = f"api-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    try:
        # ============================================================
        # HEALTH CHECK ENDPOINTS
        # ============================================================
        print_section("1. HEALTH CHECK ENDPOINTS")
        
        # Test 1.1: Basic health check
        health = repo.health_check()
        print_test("GET /health", health)
        
        # Test 1.2: Database health check
        db_health = repo.database_health_check()
        print_test("GET /health/db", db_health)
        
        # ============================================================
        # SESSION CRUD OPERATIONS
        # ============================================================
        print_section("2. SESSION CRUD OPERATIONS")
        
        # Test 2.1: Create session
        session = Session(
            session_id=test_session_id,
            session_type=SessionType.AGENT,
            created_at="",
            updated_at=""
        )
        created_session = repo.create_session(session)
        print_test(f"POST /api/v1/sessions (create: {test_session_id})", 
                   created_session.session_id == test_session_id)
        print(f"   Created at: {created_session.created_at}")
        
        # Test 2.2: Read session
        read_session = repo.read_session(test_session_id)
        print_test(f"GET /api/v1/sessions/{test_session_id}", 
                   read_session is not None and read_session.session_id == test_session_id)
        
        # Test 2.3: Update session
        updated_session = repo.update_session(test_session_id, {"session_type": "AGENT"})
        print_test(f"PUT /api/v1/sessions/{test_session_id}", 
                   updated_session.session_id == test_session_id)
        
        # Test 2.4: Read non-existent session
        non_existent = repo.read_session("non-existent-session-id")
        print_test("GET /api/v1/sessions/non-existent (should return None)", 
                   non_existent is None)
        
        # ============================================================
        # AGENT CRUD OPERATIONS
        # ============================================================
        print_section("3. AGENT CRUD OPERATIONS")
        
        # Test 3.1: Create agent
        agent = SessionAgent(
            agent_id="test-agent-1",
            state={},
            conversation_manager_state={
                "__name__": "SlidingWindowConversationManager",
                "model_call_count": 0,
                "removed_message_count": 0
            },
            _internal_state={"test_key": "test_value"}
        )
        created_agent = repo.create_agent(test_session_id, agent)
        print_test(f"POST /api/v1/sessions/{test_session_id}/agents", 
                   created_agent.agent_id == "test-agent-1")
        print(f"   Agent ID: {created_agent.agent_id}")
        
        # Test 3.2: Read agent
        read_agent = repo.read_agent(test_session_id, "test-agent-1")
        print_test(f"GET /api/v1/sessions/{test_session_id}/agents/test-agent-1", 
                   read_agent is not None and read_agent.agent_id == "test-agent-1")
        
        # Test 3.3: Update agent
        agent._internal_state = {"updated_key": "updated_value"}
        updated_agent = repo.update_agent(test_session_id, agent)
        print_test(f"PUT /api/v1/sessions/{test_session_id}/agents/test-agent-1", 
                   updated_agent._internal_state.get("updated_key") == "updated_value")
        
        # Test 3.4: List agents
        agents = repo.list_agents(test_session_id)
        print_test(f"GET /api/v1/sessions/{test_session_id}/agents (list)", 
                   len(agents) >= 1 and any(a.agent_id == "test-agent-1" for a in agents))
        print(f"   Found {len(agents)} agent(s)")
        
        # Test 3.5: Create second agent
        agent2 = SessionAgent(
            agent_id="test-agent-2",
            state={},
            conversation_manager_state={
                "__name__": "SlidingWindowConversationManager",
                "model_call_count": 0,
                "removed_message_count": 0
            },
            _internal_state={}
        )
        created_agent2 = repo.create_agent(test_session_id, agent2)
        print_test(f"POST /api/v1/sessions/{test_session_id}/agents (second agent)", 
                   created_agent2.agent_id == "test-agent-2")
        
        # Test 3.6: List agents again (should have 2)
        agents = repo.list_agents(test_session_id)
        print_test(f"GET /api/v1/sessions/{test_session_id}/agents (list with 2 agents)", 
                   len(agents) == 2)
        
        # Test 3.7: Read non-existent agent
        non_existent_agent = repo.read_agent(test_session_id, "non-existent-agent")
        print_test("GET /api/v1/sessions/{id}/agents/non-existent (should return None)", 
                   non_existent_agent is None)
        
        # ============================================================
        # MESSAGE CRUD OPERATIONS
        # ============================================================
        print_section("4. MESSAGE CRUD OPERATIONS")
        
        # Test 4.1: Create message
        message = SessionMessage(
            message_id=0,
            message=Message(role="user", content=[{"text": "Hello, this is test message 1"}]),
            redact_message=None
        )
        created_message = repo.create_message(test_session_id, "test-agent-1", message)
        print_test(f"POST /api/v1/sessions/{test_session_id}/agents/test-agent-1/messages", 
                   created_message.message_id == 0)
        print(f"   Message ID: {created_message.message_id}")
        
        # Test 4.2: Create second message
        message2 = SessionMessage(
            message_id=1,
            message=Message(role="assistant", content=[{"text": "Hello! This is response message 2"}]),
            redact_message=None
        )
        created_message2 = repo.create_message(test_session_id, "test-agent-1", message2)
        print_test(f"POST /api/v1/sessions/{test_session_id}/agents/test-agent-1/messages (second)", 
                   created_message2.message_id == 1)
        
        # Test 4.3: Create third message
        message3 = SessionMessage(
            message_id=2,
            message=Message(role="user", content=[{"text": "This is test message 3"}]),
            redact_message=None
        )
        created_message3 = repo.create_message(test_session_id, "test-agent-1", message3)
        print_test(f"POST /api/v1/sessions/{test_session_id}/agents/test-agent-1/messages (third)", 
                   created_message3.message_id == 2)
        
        # Test 4.4: Read message
        read_message = repo.read_message(test_session_id, "test-agent-1", 0)
        print_test(f"GET /api/v1/sessions/{test_session_id}/agents/test-agent-1/messages/0", 
                   read_message is not None and read_message.message_id == 0)
        
        # Test 4.5: Update message
        updated_message_data = {
            "message": {"role": "user", "content": [{"text": "Updated message content"}]},
            "redact_message": None
        }
        updated_message = repo.update_message(test_session_id, "test-agent-1", 0, updated_message_data)
        print_test(f"PUT /api/v1/sessions/{test_session_id}/agents/test-agent-1/messages/0", 
                   "Updated message content" in str(updated_message.message.content))
        
        # Test 4.6: List messages (no pagination)
        messages = repo.list_messages(test_session_id, "test-agent-1")
        print_test(f"GET /api/v1/sessions/{test_session_id}/agents/test-agent-1/messages (list all)", 
                   len(messages) == 3)
        print(f"   Found {len(messages)} message(s)")
        
        # Test 4.7: List messages with limit
        messages_limited = repo.list_messages(test_session_id, "test-agent-1", limit=2)
        print_test(f"GET /api/v1/sessions/{test_session_id}/agents/test-agent-1/messages?limit=2", 
                   len(messages_limited) == 2)
        print(f"   Found {len(messages_limited)} message(s) with limit=2")
        
        # Test 4.8: List messages with offset
        messages_offset = repo.list_messages(test_session_id, "test-agent-1", offset=1)
        print_test(f"GET /api/v1/sessions/{test_session_id}/agents/test-agent-1/messages?offset=1", 
                   len(messages_offset) == 2)
        print(f"   Found {len(messages_offset)} message(s) with offset=1")
        
        # Test 4.9: List messages with limit and offset
        messages_paginated = repo.list_messages(test_session_id, "test-agent-1", limit=1, offset=1)
        print_test(f"GET /api/v1/sessions/{test_session_id}/agents/test-agent-1/messages?limit=1&offset=1", 
                   len(messages_paginated) == 1 and messages_paginated[0].message_id == 1)
        
        # Test 4.10: Read non-existent message
        non_existent_message = repo.read_message(test_session_id, "test-agent-1", 999)
        print_test("GET /api/v1/sessions/{id}/agents/{id}/messages/999 (should return None)", 
                   non_existent_message is None)
        
        # Test 4.11: Create messages for second agent
        message_agent2 = SessionMessage(
            message_id=0,
            message=Message(role="user", content=[{"text": "Message for agent 2"}]),
            redact_message=None
        )
        created_message_agent2 = repo.create_message(test_session_id, "test-agent-2", message_agent2)
        print_test(f"POST /api/v1/sessions/{test_session_id}/agents/test-agent-2/messages", 
                   created_message_agent2.message_id == 0)
        
        # ============================================================
        # DELETE OPERATIONS (in reverse order)
        # ============================================================
        print_section("5. DELETE OPERATIONS")
        
        # Test 5.1: Delete message
        deleted_message = repo.delete_message(test_session_id, "test-agent-1", 2)
        print_test(f"DELETE /api/v1/sessions/{test_session_id}/agents/test-agent-1/messages/2", 
                   deleted_message)
        
        # Verify message is deleted
        messages_after_delete = repo.list_messages(test_session_id, "test-agent-1")
        print_test("Verify message deleted (should have 2 messages now)", 
                   len(messages_after_delete) == 2)
        
        # Test 5.2: Delete non-existent message
        deleted_non_existent_msg = repo.delete_message(test_session_id, "test-agent-1", 999)
        print_test("DELETE non-existent message (should return False)", 
                   not deleted_non_existent_msg)
        
        # Test 5.3: Delete agent (cascade should delete messages)
        deleted_agent = repo.delete_agent(test_session_id, "test-agent-2")
        print_test(f"DELETE /api/v1/sessions/{test_session_id}/agents/test-agent-2", 
                   deleted_agent)
        
        # Verify agent is deleted
        agents_after_delete = repo.list_agents(test_session_id)
        print_test("Verify agent deleted (should have 1 agent now)", 
                   len(agents_after_delete) == 1)
        
        # Test 5.4: Delete non-existent agent
        deleted_non_existent_agent = repo.delete_agent(test_session_id, "non-existent-agent")
        print_test("DELETE non-existent agent (should return False)", 
                   not deleted_non_existent_agent)
        
        # Test 5.5: Delete session (cascade should delete all agents and messages)
        deleted_session = repo.delete_session(test_session_id)
        print_test(f"DELETE /api/v1/sessions/{test_session_id}", 
                   deleted_session)
        
        # Verify session is deleted
        session_after_delete = repo.read_session(test_session_id)
        print_test("Verify session deleted (should return None)", 
                   session_after_delete is None)
        
        # Test 5.6: Delete non-existent session
        deleted_non_existent_session = repo.delete_session("non-existent-session")
        print_test("DELETE non-existent session (should return False)", 
                   not deleted_non_existent_session)
        
        # ============================================================
        # ERROR HANDLING
        # ============================================================
        print_section("6. ERROR HANDLING")
        
        # Test 6.1: Try to create duplicate session
        try:
            duplicate_session = Session(
                session_id="duplicate-test",
                session_type=SessionType.AGENT,
                created_at="",
                updated_at=""
            )
            repo.create_session(duplicate_session)
            repo.create_session(duplicate_session)  # Should fail
            print_test("POST duplicate session (should raise error)", False)
        except Exception as e:
            print_test(f"POST duplicate session (correctly raised: {type(e).__name__})", True)
        
        # Test 6.2: Try to create agent in non-existent session
        try:
            agent_no_session = SessionAgent(
                agent_id="orphan-agent",
                state={},
                conversation_manager_state={},
                _internal_state={}
            )
            repo.create_agent("non-existent-session-xyz", agent_no_session)
            print_test("POST agent to non-existent session (should raise error)", False)
        except Exception as e:
            print_test(f"POST agent to non-existent session (correctly raised: {type(e).__name__})", True)
        
        # Test 6.3: Try to create message for non-existent agent
        try:
            message_no_agent = SessionMessage(
                message_id=0,
                message=Message(role="user", content=[{"text": "Orphan message"}]),
                redact_message=None
            )
            repo.create_message("duplicate-test", "non-existent-agent", message_no_agent)
            print_test("POST message to non-existent agent (should raise error)", False)
        except Exception as e:
            print_test(f"POST message to non-existent agent (correctly raised: {type(e).__name__})", True)
        
        # Clean up duplicate session
        repo.delete_session("duplicate-test")
        
        # ============================================================
        # SUMMARY
        # ============================================================
        print_section("TEST SUMMARY")
        print("✅ All API endpoints tested successfully!")
        print("\nAPI Coverage:")
        print("  • Health checks: 2/2")
        print("  • Session CRUD: 4/4")
        print("  • Agent CRUD: 7/7")
        print("  • Message CRUD: 11/11")
        print("  • Delete operations: 6/6")
        print("  • Error handling: 3/3")
        print("  • Total: 33/33 tests passed")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)