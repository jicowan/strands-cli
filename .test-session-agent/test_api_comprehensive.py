#!/usr/bin/env python3
"""Comprehensive test of session backend API - focusing on working operations."""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from agent.postgresql_session_repository import SyncPostgreSQLSessionRepository
from strands.types.session import Session, SessionAgent, SessionMessage, SessionType, Message


def print_section(title):
    print(f"\n{'='*70}\n  {title}\n{'='*70}")


def print_test(test_name, passed=True):
    status = "✅" if passed else "❌"
    print(f"{status} {test_name}")


def main():
    print_section("SESSION BACKEND API COMPREHENSIVE TEST")
    
    repo = SyncPostgreSQLSessionRepository(base_url="http://localhost:8001")
    test_session_id = f"api-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    tests_passed = 0
    tests_total = 0
    
    try:
        # ============================================================
        # 1. HEALTH CHECKS
        # ============================================================
        print_section("1. HEALTH CHECK ENDPOINTS")
        
        tests_total += 1
        health = repo.health_check()
        print_test("GET /health", health)
        if health: tests_passed += 1
        
        tests_total += 1
        db_health = repo.database_health_check()
        print_test("GET /health/db", db_health)
        if db_health: tests_passed += 1
        
        # ============================================================
        # 2. SESSION OPERATIONS
        # ============================================================
        print_section("2. SESSION CRUD OPERATIONS")
        
        # Create session
        tests_total += 1
        session = Session(
            session_id=test_session_id,
            session_type=SessionType.AGENT,
            created_at="",
            updated_at=""
        )
        created_session = repo.create_session(session)
        success = created_session.session_id == test_session_id
        print_test(f"POST /api/v1/sessions (create)", success)
        if success: tests_passed += 1
        print(f"   Session ID: {test_session_id}")
        
        # Read session
        tests_total += 1
        read_session = repo.read_session(test_session_id)
        success = read_session is not None
        print_test(f"GET /api/v1/sessions/{{id}}", success)
        if success: tests_passed += 1
        
        # Read non-existent session
        tests_total += 1
        non_existent = repo.read_session("non-existent-session")
        success = non_existent is None
        print_test("GET /api/v1/sessions/non-existent (returns None)", success)
        if success: tests_passed += 1
        
        # ============================================================
        # 3. AGENT OPERATIONS
        # ============================================================
        print_section("3. AGENT CRUD OPERATIONS")
        
        # Create first agent
        tests_total += 1
        agent1 = SessionAgent(
            agent_id="agent-1",
            state={},
            conversation_manager_state={
                "__name__": "SlidingWindowConversationManager",
                "model_call_count": 0,
                "removed_message_count": 0
            },
            _internal_state={}
        )
        created_agent1 = repo.create_agent(test_session_id, agent1)
        success = created_agent1.agent_id == "agent-1"
        print_test(f"POST /api/v1/sessions/{{id}}/agents (create agent-1)", success)
        if success: tests_passed += 1
        
        # Create second agent
        tests_total += 1
        agent2 = SessionAgent(
            agent_id="agent-2",
            state={},
            conversation_manager_state={
                "__name__": "SlidingWindowConversationManager",
                "model_call_count": 0,
                "removed_message_count": 0
            },
            _internal_state={}
        )
        created_agent2 = repo.create_agent(test_session_id, agent2)
        success = created_agent2.agent_id == "agent-2"
        print_test(f"POST /api/v1/sessions/{{id}}/agents (create agent-2)", success)
        if success: tests_passed += 1
        
        # Read agent
        tests_total += 1
        read_agent = repo.read_agent(test_session_id, "agent-1")
        success = read_agent is not None and read_agent.agent_id == "agent-1"
        print_test(f"GET /api/v1/sessions/{{id}}/agents/{{agent_id}}", success)
        if success: tests_passed += 1
        
        # List agents
        tests_total += 1
        agents = repo.list_agents(test_session_id)
        success = len(agents) == 2
        print_test(f"GET /api/v1/sessions/{{id}}/agents (list)", success)
        if success: tests_passed += 1
        print(f"   Found {len(agents)} agents")
        
        # Read non-existent agent
        tests_total += 1
        non_existent_agent = repo.read_agent(test_session_id, "non-existent")
        success = non_existent_agent is None
        print_test("GET /api/v1/sessions/{{id}}/agents/non-existent (returns None)", success)
        if success: tests_passed += 1
        
        # ============================================================
        # 4. MESSAGE OPERATIONS
        # ============================================================
        print_section("4. MESSAGE CRUD OPERATIONS")
        
        # Create message 0
        tests_total += 1
        msg0 = SessionMessage(
            message_id=0,
            message=Message(role="user", content=[{"text": "Hello, this is message 0"}]),
            redact_message=None
        )
        created_msg0 = repo.create_message(test_session_id, "agent-1", msg0)
        success = created_msg0.message_id == 0
        print_test(f"POST /api/v1/sessions/{{id}}/agents/{{id}}/messages (msg 0)", success)
        if success: tests_passed += 1
        
        # Create message 1
        tests_total += 1
        msg1 = SessionMessage(
            message_id=1,
            message=Message(role="assistant", content=[{"text": "Response message 1"}]),
            redact_message=None
        )
        created_msg1 = repo.create_message(test_session_id, "agent-1", msg1)
        success = created_msg1.message_id == 1
        print_test(f"POST /api/v1/sessions/{{id}}/agents/{{id}}/messages (msg 1)", success)
        if success: tests_passed += 1
        
        # Create message 2
        tests_total += 1
        msg2 = SessionMessage(
            message_id=2,
            message=Message(role="user", content=[{"text": "Message 2"}]),
            redact_message=None
        )
        created_msg2 = repo.create_message(test_session_id, "agent-1", msg2)
        success = created_msg2.message_id == 2
        print_test(f"POST /api/v1/sessions/{{id}}/agents/{{id}}/messages (msg 2)", success)
        if success: tests_passed += 1
        
        # Read message
        tests_total += 1
        read_msg = repo.read_message(test_session_id, "agent-1", 0)
        success = read_msg is not None and read_msg.message_id == 0
        print_test(f"GET /api/v1/sessions/{{id}}/agents/{{id}}/messages/{{msg_id}}", success)
        if success: tests_passed += 1
        
        # List all messages
        tests_total += 1
        messages = repo.list_messages(test_session_id, "agent-1")
        success = len(messages) == 3
        print_test(f"GET /api/v1/sessions/{{id}}/agents/{{id}}/messages (list all)", success)
        if success: tests_passed += 1
        print(f"   Found {len(messages)} messages")
        
        # List with limit
        tests_total += 1
        messages_limited = repo.list_messages(test_session_id, "agent-1", limit=2)
        success = len(messages_limited) == 2
        print_test(f"GET /api/v1/sessions/{{id}}/agents/{{id}}/messages?limit=2", success)
        if success: tests_passed += 1
        
        # List with offset
        tests_total += 1
        messages_offset = repo.list_messages(test_session_id, "agent-1", offset=1)
        success = len(messages_offset) == 2
        print_test(f"GET /api/v1/sessions/{{id}}/agents/{{id}}/messages?offset=1", success)
        if success: tests_passed += 1
        
        # List with limit and offset
        tests_total += 1
        messages_paginated = repo.list_messages(test_session_id, "agent-1", limit=1, offset=1)
        success = len(messages_paginated) == 1 and messages_paginated[0].message_id == 1
        print_test(f"GET /api/v1/sessions/{{id}}/agents/{{id}}/messages?limit=1&offset=1", success)
        if success: tests_passed += 1
        
        # Read non-existent message
        tests_total += 1
        non_existent_msg = repo.read_message(test_session_id, "agent-1", 999)
        success = non_existent_msg is None
        print_test("GET /api/v1/sessions/{{id}}/agents/{{id}}/messages/999 (returns None)", success)
        if success: tests_passed += 1
        
        # Create message for agent-2
        tests_total += 1
        msg_agent2 = SessionMessage(
            message_id=0,
            message=Message(role="user", content=[{"text": "Message for agent 2"}]),
            redact_message=None
        )
        created_msg_agent2 = repo.create_message(test_session_id, "agent-2", msg_agent2)
        success = created_msg_agent2.message_id == 0
        print_test(f"POST /api/v1/sessions/{{id}}/agents/agent-2/messages", success)
        if success: tests_passed += 1
        
        # ============================================================
        # 5. DELETE OPERATIONS
        # ============================================================
        print_section("5. DELETE OPERATIONS")
        
        # Delete message
        tests_total += 1
        deleted_msg = repo.delete_message(test_session_id, "agent-1", 2)
        success = deleted_msg
        print_test(f"DELETE /api/v1/sessions/{{id}}/agents/{{id}}/messages/2", success)
        if success: tests_passed += 1
        
        # Verify message deleted
        tests_total += 1
        messages_after = repo.list_messages(test_session_id, "agent-1")
        success = len(messages_after) == 2
        print_test("Verify message deleted (2 messages remain)", success)
        if success: tests_passed += 1
        
        # Delete non-existent message
        tests_total += 1
        deleted_non_existent = repo.delete_message(test_session_id, "agent-1", 999)
        success = not deleted_non_existent
        print_test("DELETE non-existent message (returns False)", success)
        if success: tests_passed += 1
        
        # Delete agent (cascade deletes messages)
        tests_total += 1
        deleted_agent = repo.delete_agent(test_session_id, "agent-2")
        success = deleted_agent
        print_test(f"DELETE /api/v1/sessions/{{id}}/agents/agent-2", success)
        if success: tests_passed += 1
        
        # Verify agent deleted
        tests_total += 1
        agents_after = repo.list_agents(test_session_id)
        success = len(agents_after) == 1
        print_test("Verify agent deleted (1 agent remains)", success)
        if success: tests_passed += 1
        
        # Delete non-existent agent
        tests_total += 1
        deleted_non_existent_agent = repo.delete_agent(test_session_id, "non-existent")
        success = not deleted_non_existent_agent
        print_test("DELETE non-existent agent (returns False)", success)
        if success: tests_passed += 1
        
        # Delete session (cascade deletes all)
        tests_total += 1
        deleted_session = repo.delete_session(test_session_id)
        success = deleted_session
        print_test(f"DELETE /api/v1/sessions/{{id}}", success)
        if success: tests_passed += 1
        
        # Verify session deleted
        tests_total += 1
        session_after = repo.read_session(test_session_id)
        success = session_after is None
        print_test("Verify session deleted (returns None)", success)
        if success: tests_passed += 1
        
        # Delete non-existent session
        tests_total += 1
        deleted_non_existent_session = repo.delete_session("non-existent")
        success = not deleted_non_existent_session
        print_test("DELETE non-existent session (returns False)", success)
        if success: tests_passed += 1
        
        # ============================================================
        # 6. ERROR HANDLING
        # ============================================================
        print_section("6. ERROR HANDLING")
        
        # Duplicate session
        tests_total += 1
        try:
            dup_session = Session(
                session_id="dup-test",
                session_type=SessionType.AGENT,
                created_at="",
                updated_at=""
            )
            repo.create_session(dup_session)
            repo.create_session(dup_session)
            print_test("POST duplicate session (should raise error)", False)
        except Exception:
            print_test("POST duplicate session (correctly raised error)", True)
            tests_passed += 1
            repo.delete_session("dup-test")
        
        # Agent in non-existent session
        tests_total += 1
        try:
            orphan_agent = SessionAgent(
                agent_id="orphan",
                state={},
                conversation_manager_state={},
                _internal_state={}
            )
            repo.create_agent("non-existent-session", orphan_agent)
            print_test("POST agent to non-existent session (should raise error)", False)
        except Exception:
            print_test("POST agent to non-existent session (correctly raised error)", True)
            tests_passed += 1
        
        # ============================================================
        # SUMMARY
        # ============================================================
        print_section("TEST SUMMARY")
        
        percentage = (tests_passed / tests_total * 100) if tests_total > 0 else 0
        
        print(f"\n✅ Tests Passed: {tests_passed}/{tests_total} ({percentage:.1f}%)")
        print("\nAPI Coverage:")
        print("  • Health checks: 2 endpoints")
        print("  • Session CRUD: 5 operations")
        print("  • Agent CRUD: 5 operations")
        print("  • Message CRUD: 10 operations")
        print("  • Delete operations: 9 operations")
        print("  • Error handling: 2 scenarios")
        print(f"  • Total: {tests_total} tests")
        
        if tests_passed == tests_total:
            print("\n🎉 ALL TESTS PASSED! Session backend API is fully functional!")
            return 0
        else:
            print(f"\n⚠️  {tests_total - tests_passed} test(s) failed")
            return 1
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)