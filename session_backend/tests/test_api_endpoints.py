"""Tests for API endpoints and HTTP status codes."""

import pytest
import asyncio
from fastapi.testclient import TestClient
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.strategies import composite
import json
from typing import Dict, Any, List, Tuple
import uuid

from app.main import app
from app.database import get_db_session


class TestAPIEndpoints:
    """Unit tests for API endpoints."""
    
    def test_create_session_success(self, test_client):
        """Test successful session creation."""
        session_data = {
            "session_id": "test-session-1",
            "multi_agent_state": {"key": "value"}
        }
        
        response = test_client.post("/api/v1/sessions", json=session_data)
        
        # Debug: Print response details if not 201
        if response.status_code != 201:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        
        assert response.status_code == 201
        data = response.json()
        assert data["session_id"] == "test-session-1"
        assert data["multi_agent_state"] == {"key": "value"}
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_session_conflict(self, test_client):
        """Test session creation conflict (duplicate ID)."""
        session_data = {
            "session_id": "test-session-duplicate",
            "multi_agent_state": {"key": "value"}
        }
        
        # Create first session
        response1 = test_client.post("/api/v1/sessions", json=session_data)
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = test_client.post("/api/v1/sessions", json=session_data)
        assert response2.status_code == 409
        data = response2.json()
        assert data["detail"]["error"] == "ConflictError"
    
    def test_get_session_success(self, test_client):
        """Test successful session retrieval."""
        # Create session first
        session_data = {
            "session_id": "test-session-get",
            "multi_agent_state": {"key": "value"}
        }
        create_response = test_client.post("/api/v1/sessions", json=session_data)
        assert create_response.status_code == 201
        
        # Get session
        response = test_client.get("/api/v1/sessions/test-session-get")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-get"
    
    def test_get_session_not_found(self, test_client):
        """Test session retrieval when session doesn't exist."""
        response = test_client.get("/api/v1/sessions/nonexistent-session")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "NotFoundError"
    
    def test_update_session_success(self, test_client):
        """Test successful session update."""
        # Create session first
        session_data = {
            "session_id": "test-session-update",
            "multi_agent_state": {"key": "value"}
        }
        create_response = test_client.post("/api/v1/sessions", json=session_data)
        assert create_response.status_code == 201
        
        # Update session
        update_data = {"multi_agent_state": {"key": "updated_value"}}
        response = test_client.put("/api/v1/sessions/test-session-update", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["multi_agent_state"]["key"] == "updated_value"
    
    def test_update_session_not_found(self, test_client):
        """Test session update when session doesn't exist."""
        update_data = {"multi_agent_state": {"key": "value"}}
        response = test_client.put("/api/v1/sessions/nonexistent-session", json=update_data)
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "NotFoundError"
    
    def test_delete_session_success(self, test_client):
        """Test successful session deletion."""
        # Create session first
        session_data = {
            "session_id": "test-session-delete",
            "multi_agent_state": {"key": "value"}
        }
        create_response = test_client.post("/api/v1/sessions", json=session_data)
        assert create_response.status_code == 201
        
        # Delete session
        response = test_client.delete("/api/v1/sessions/test-session-delete")
        assert response.status_code == 204
    
    def test_delete_session_not_found(self, test_client):
        """Test session deletion when session doesn't exist."""
        response = test_client.delete("/api/v1/sessions/nonexistent-session")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "NotFoundError"
    
    def test_list_sessions_empty(self, test_client):
        """Test listing sessions when none exist."""
        response = test_client.get("/api/v1/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data["sessions"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 10
    
    def test_create_agent_success(self, test_client):
        """Test successful agent creation."""
        # Create session first
        session_data = {
            "session_id": "test-session-agent",
            "multi_agent_state": {"key": "value"}
        }
        create_response = test_client.post("/api/v1/sessions", json=session_data)
        assert create_response.status_code == 201
        
        # Create agent
        agent_data = {
            "agent_id": "test-agent-1",
            "state": {"tools": ["tool1"]},
            "conversation_manager_state": {"history": []},
            "internal_state": {"memory": {}}
        }
        response = test_client.post("/api/v1/sessions/test-session-agent/agents", json=agent_data)
        assert response.status_code == 201
        data = response.json()
        assert data["agent_id"] == "test-agent-1"
    
    def test_create_agent_session_not_found(self, test_client):
        """Test agent creation when session doesn't exist."""
        agent_data = {
            "agent_id": "test-agent-1",
            "state": {"tools": ["tool1"]},
            "conversation_manager_state": {"history": []},
            "internal_state": {"memory": {}}
        }
        response = test_client.post("/api/v1/sessions/nonexistent-session/agents", json=agent_data)
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "NotFoundError"
    
    def test_create_message_success(self, test_client):
        """Test successful message creation."""
        # Create session and agent first
        session_data = {
            "session_id": "test-session-message",
            "multi_agent_state": {"key": "value"}
        }
        test_client.post("/api/v1/sessions", json=session_data)
        
        agent_data = {
            "agent_id": "test-agent-message",
            "state": {"tools": ["tool1"]},
            "conversation_manager_state": {"history": []},
            "internal_state": {"memory": {}}
        }
        test_client.post("/api/v1/sessions/test-session-message/agents", json=agent_data)
        
        # Create message
        message_data = {
            "message_id": 1,
            "message": {
                "role": "user",
                "content": "Hello, world!"
            }
        }
        response = test_client.post(
            "/api/v1/sessions/test-session-message/agents/test-agent-message/messages",
            json=message_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["message_id"] == 1
        assert data["message"]["content"] == "Hello, world!"
    
    def test_create_message_agent_not_found(self, test_client):
        """Test message creation when agent doesn't exist."""
        message_data = {
            "message_id": 1,
            "message": {
                "role": "user",
                "content": "Hello, world!"
            }
        }
        response = test_client.post(
            "/api/v1/sessions/nonexistent-session/agents/nonexistent-agent/messages",
            json=message_data
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "NotFoundError"
    
    def test_health_endpoints(self, test_client):
        """Test health check endpoints."""
        # Basic health check
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
        # Liveness probe
        response = test_client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


# Property-based test strategies
@composite
def valid_session_id(draw):
    """Generate valid session IDs that match the regex pattern ^[a-zA-Z0-9_-]+$."""
    # Generate a string with valid characters only
    # Must be at least 1 character and at most 50 characters
    length = draw(st.integers(min_value=1, max_value=50))
    chars = draw(st.lists(
        st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"),
        min_size=length,
        max_size=length
    ))
    return ''.join(chars)


@composite
def valid_agent_id(draw):
    """Generate valid agent IDs that match the regex pattern ^[a-zA-Z0-9_-]+$."""
    # Generate a string with valid characters only
    # Must be at least 1 character and at most 50 characters
    length = draw(st.integers(min_value=1, max_value=50))
    chars = draw(st.lists(
        st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"),
        min_size=length,
        max_size=length
    ))
    return ''.join(chars)


@composite
def valid_session_data(draw):
    """Generate valid session creation data."""
    session_id = draw(valid_session_id())
    
    # Generate realistic multi-agent state that a Strands agent would produce
    multi_agent_state = draw(st.one_of(
        st.none(),
        st.dictionaries(
            # Realistic keys that agents might use
            st.sampled_from([
                "current_agent", "active_agents", "conversation_state", "workflow_state",
                "shared_memory", "coordination_data", "task_queue", "agent_roles",
                "session_metadata", "execution_context", "tool_results", "user_preferences"
            ]),
            # Realistic values that agents might store
            st.one_of(
                st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=100),  # ASCII printable
                st.integers(min_value=0, max_value=1000000),
                st.booleans(),
                st.lists(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=20), max_size=5),
                st.dictionaries(
                    st.sampled_from(["id", "name", "type", "status", "timestamp", "data"]),
                    st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=50),
                    max_size=3
                )
            ),
            min_size=0,
            max_size=5
        )
    ))
    
    return {
        "session_id": session_id,
        "multi_agent_state": multi_agent_state
    }


@composite
def valid_agent_data(draw):
    """Generate valid agent creation data."""
    agent_id = draw(valid_agent_id())
    
    # Generate realistic agent state that a Strands agent would produce
    state = draw(st.dictionaries(
        # Realistic state keys for agents
        st.sampled_from([
            "tools", "capabilities", "model_config", "system_prompt", "memory",
            "conversation_history", "tool_results", "execution_state", "preferences",
            "context_window", "temperature", "max_tokens", "stop_sequences"
        ]),
        # Realistic state values
        st.one_of(
            st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=200),  # ASCII printable
            st.integers(min_value=0, max_value=10000),
            st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.lists(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=30), max_size=10),
            st.dictionaries(
                st.sampled_from(["name", "description", "parameters", "required", "type"]),
                st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=100),
                max_size=5
            )
        ),
        min_size=1,
        max_size=8
    ))
    
    conversation_manager_state = draw(st.dictionaries(
        # Realistic conversation manager keys
        st.sampled_from([
            "history", "current_turn", "participants", "message_count", "last_activity",
            "conversation_id", "thread_id", "context_summary", "turn_count"
        ]),
        # Realistic conversation values
        st.one_of(
            st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=150),
            st.integers(min_value=0, max_value=1000),
            st.booleans(),
            st.lists(
                st.dictionaries(
                    st.sampled_from(["role", "content", "timestamp", "message_id"]),
                    st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=100),
                    max_size=4
                ),
                max_size=5
            )
        ),
        min_size=1,
        max_size=6
    ))
    
    internal_state = draw(st.dictionaries(
        # Realistic internal state keys
        st.sampled_from([
            "memory", "cache", "session_data", "user_context", "execution_log",
            "error_count", "last_error", "performance_metrics", "debug_info"
        ]),
        # Realistic internal values
        st.one_of(
            st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=100),
            st.integers(min_value=0, max_value=1000),
            st.booleans(),
            st.dictionaries(
                st.sampled_from(["timestamp", "level", "message", "context"]),
                st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=80),
                max_size=4
            )
        ),
        min_size=0,
        max_size=6
    ))
    
    return {
        "agent_id": agent_id,
        "state": state,
        "conversation_manager_state": conversation_manager_state,
        "internal_state": internal_state
    }


@composite
def valid_message_data(draw):
    """Generate valid message creation data."""
    message_id = draw(st.integers(min_value=0, max_value=1000))
    role = draw(st.sampled_from(["user", "assistant", "system", "tool"]))
    
    # Generate realistic message content that agents would produce
    content = draw(st.one_of(
        # Simple text messages
        st.text(
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),  # ASCII printable
            min_size=1, 
            max_size=500
        ),
        # Agent-like responses
        st.sampled_from([
            "Hello! How can I help you today?",
            "I understand your request. Let me process that for you.",
            "Based on the information provided, I recommend the following approach:",
            "I've completed the task successfully. Here are the results:",
            "I need more information to proceed. Could you please clarify:",
            "The analysis shows the following key findings:",
            "I've executed the requested action. The output is:",
            "Let me search for that information and get back to you.",
            "I've reviewed the data and here's my assessment:",
            "The task has been completed. Summary of actions taken:"
        ]),
        # Tool responses
        st.sampled_from([
            '{"status": "success", "result": "Operation completed"}',
            '{"error": "Invalid parameter", "code": 400}',
            '{"data": [{"id": 1, "name": "example"}], "count": 1}',
            '{"message": "Processing complete", "timestamp": "2024-01-01T00:00:00Z"}',
            '{"response": "Query executed successfully", "rows_affected": 5}'
        ])
    ))
    
    message = {
        "role": role,
        "content": content
    }
    
    # Sometimes add realistic metadata
    if draw(st.booleans()):
        message["metadata"] = draw(st.dictionaries(
            st.sampled_from([
                "timestamp", "source", "tool_name", "execution_time", "model",
                "temperature", "tokens_used", "confidence", "session_id"
            ]),
            st.one_of(
                st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=50),
                st.integers(min_value=0, max_value=10000),
                st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
            ),
            min_size=1,
            max_size=5
        ))
    
    return {
        "message_id": message_id,
        "message": message
    }


@composite
def api_operation(draw):
    """Generate API operations for testing HTTP status codes."""
    operation_type = draw(st.sampled_from([
        "create_session", "get_session", "update_session", "delete_session", "list_sessions",
        "create_agent", "get_agent", "update_agent", "delete_agent", "list_agents",
        "create_message", "get_message", "update_message", "delete_message", "list_messages",
        "health_check", "db_health_check", "readiness_check", "liveness_check"
    ]))
    
    # Generate appropriate data based on operation type
    if operation_type.startswith("create_session") or operation_type.startswith("update_session"):
        data = draw(valid_session_data())
    elif operation_type.startswith("create_agent") or operation_type.startswith("update_agent"):
        data = draw(valid_agent_data())
    elif operation_type.startswith("create_message") or operation_type.startswith("update_message"):
        data = draw(valid_message_data())
    else:
        data = None
    
    # Generate IDs for operations that need them
    session_id = draw(valid_session_id()) if "session" in operation_type else None
    agent_id = draw(valid_agent_id()) if "agent" in operation_type else None
    message_id = draw(st.integers(min_value=0, max_value=100)) if "message" in operation_type else None
    
    return {
        "operation": operation_type,
        "data": data,
        "session_id": session_id,
        "agent_id": agent_id,
        "message_id": message_id
    }


class TestHTTPStatusCodeProperties:
    """Property-based tests for HTTP status codes."""
    
    @given(session_data=valid_session_data())
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_http_status_code_correctness_sessions(self, test_client, session_data):
        """
        Property 10: HTTP Status Code Correctness
        For any valid session operation, the returned HTTP status code should match the operation result.
        **Feature: session-backend-api, Property 10: HTTP Status Code Correctness**
        **Validates: Requirements 4.5**
        """
        # Test successful session creation
        response = test_client.post("/api/v1/sessions", json=session_data)
        
        # Should return 201 for successful creation
        assert response.status_code == 201, f"Expected 201 for session creation, got {response.status_code}"
        
        # Test successful retrieval
        response = test_client.get(f"/api/v1/sessions/{session_data['session_id']}")
        assert response.status_code == 200, f"Expected 200 for session retrieval, got {response.status_code}"
        
        # Test successful update
        update_data = {"multi_agent_state": {"updated": True}}
        response = test_client.put(f"/api/v1/sessions/{session_data['session_id']}", json=update_data)
        assert response.status_code == 200, f"Expected 200 for session update, got {response.status_code}"
        
        # Test successful deletion
        response = test_client.delete(f"/api/v1/sessions/{session_data['session_id']}")
        assert response.status_code == 204, f"Expected 204 for session deletion, got {response.status_code}"
        
        # Test not found after deletion
        response = test_client.get(f"/api/v1/sessions/{session_data['session_id']}")
        assert response.status_code == 404, f"Expected 404 for deleted session retrieval, got {response.status_code}"
    
    @given(st.one_of(
        # Generate realistic but nonexistent IDs
        st.text(
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),
            min_size=1, 
            max_size=50
        ).filter(lambda x: x.isalnum() or all(c in '-_' for c in x if not c.isalnum())),
        st.sampled_from([
            "nonexistent-session", "missing-agent", "invalid-id", 
            "deleted-resource", "unknown-entity", "test-not-found"
        ])
    ))
    @settings(max_examples=10, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_http_status_code_not_found_operations(self, test_client, nonexistent_id):
        """
        Property 10: HTTP Status Code Correctness - Not Found Cases
        For any operation on nonexistent resources, should return 404.
        **Feature: session-backend-api, Property 10: HTTP Status Code Correctness**
        **Validates: Requirements 4.5**
        """
        # Clean the ID to make it valid format
        clean_id = ''.join(c for c in nonexistent_id if c.isalnum() or c in '-_')
        if not clean_id:
            clean_id = "nonexistent"
        
        # Test session not found
        response = test_client.get(f"/api/v1/sessions/{clean_id}")
        assert response.status_code == 404, f"Expected 404 for nonexistent session, got {response.status_code}"
        
        # Test agent not found
        response = test_client.get(f"/api/v1/sessions/{clean_id}/agents/{clean_id}")
        assert response.status_code == 404, f"Expected 404 for nonexistent agent, got {response.status_code}"
        
        # Test message not found
        response = test_client.get(f"/api/v1/sessions/{clean_id}/agents/{clean_id}/messages/1")
        assert response.status_code == 404, f"Expected 404 for nonexistent message, got {response.status_code}"
    
    @given(st.dictionaries(
        # Use realistic but invalid field names
        st.sampled_from([
            "invalid_field", "wrong_key", "bad_parameter", "missing_required",
            "extra_field", "malformed_data", "incorrect_type"
        ]), 
        st.one_of(
            st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=50),
            st.integers(),
            st.booleans()
        ), 
        min_size=1, 
        max_size=3
    ))
    @settings(max_examples=10, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_http_status_code_validation_errors(self, test_client, invalid_data):
        """
        Property 10: HTTP Status Code Correctness - Validation Errors
        For any invalid request payload, should return 4xx status codes.
        **Feature: session-backend-api, Property 10: HTTP Status Code Correctness**
        **Validates: Requirements 4.5**
        """
        # Test invalid session creation (missing required fields)
        response = test_client.post("/api/v1/sessions", json=invalid_data)
        assert 400 <= response.status_code < 500, f"Expected 4xx for invalid session data, got {response.status_code}"
        
        # Test invalid agent creation (missing required fields)
        response = test_client.post("/api/v1/sessions/test-session/agents", json=invalid_data)
        assert 400 <= response.status_code < 500, f"Expected 4xx for invalid agent data, got {response.status_code}"
        
        # Test invalid message creation (missing required fields)
        response = test_client.post("/api/v1/sessions/test-session/agents/test-agent/messages", json=invalid_data)
        assert 400 <= response.status_code < 500, f"Expected 4xx for invalid message data, got {response.status_code}"
    
    def test_property_http_status_code_health_endpoints(self, test_client):
        """
        Property 10: HTTP Status Code Correctness - Health Endpoints
        Health endpoints should return appropriate status codes.
        **Feature: session-backend-api, Property 10: HTTP Status Code Correctness**
        **Validates: Requirements 4.5**
        """
        # Basic health check should always return 200
        response = test_client.get("/health")
        assert response.status_code == 200, f"Expected 200 for health check, got {response.status_code}"
        
        # Liveness probe should always return 200
        response = test_client.get("/health/live")
        assert response.status_code == 200, f"Expected 200 for liveness probe, got {response.status_code}"
        
        # Database health check should return 200 or 503
        response = test_client.get("/health/db")
        assert response.status_code in [200, 503], f"Expected 200 or 503 for db health check, got {response.status_code}"
        
        # Readiness probe should return 200 or 503
        response = test_client.get("/health/ready")
        assert response.status_code in [200, 503], f"Expected 200 or 503 for readiness probe, got {response.status_code}"
    
    @given(session_data=valid_session_data())
    @settings(max_examples=10, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_http_status_code_conflict_errors(self, test_client, session_data):
        """
        Property 10: HTTP Status Code Correctness - Conflict Errors
        For any duplicate resource creation, should return 409.
        **Feature: session-backend-api, Property 10: HTTP Status Code Correctness**
        **Validates: Requirements 4.5**
        """
        # Create session first
        response = test_client.post("/api/v1/sessions", json=session_data)
        assert response.status_code == 201
        
        # Try to create duplicate session
        response = test_client.post("/api/v1/sessions", json=session_data)
        assert response.status_code == 409, f"Expected 409 for duplicate session, got {response.status_code}"
        
        # Create agent in the session
        agent_data = {
            "agent_id": "test-agent",
            "state": {"tools": ["tool1"]},
            "conversation_manager_state": {"history": []},
            "internal_state": {"memory": {}}
        }
        response = test_client.post(f"/api/v1/sessions/{session_data['session_id']}/agents", json=agent_data)
        assert response.status_code == 201
        
        # Try to create duplicate agent
        response = test_client.post(f"/api/v1/sessions/{session_data['session_id']}/agents", json=agent_data)
        assert response.status_code == 409, f"Expected 409 for duplicate agent, got {response.status_code}"