"""Unit tests for PostgreSQL session repository.

This module tests the PostgreSQLSessionRepository class to ensure
all CRUD operations work correctly with proper error handling.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from postgresql_session_repository import (
    PostgreSQLSessionRepository,
    SessionNotFoundError,
    AgentNotFoundError,
    MessageNotFoundError,
    SessionRepositoryError
)


class TestPostgreSQLSessionRepository:
    """Unit tests for PostgreSQL session repository."""
    
    @pytest.fixture
    def repository(self):
        """Create a repository instance for testing."""
        return PostgreSQLSessionRepository(base_url="http://localhost:8001", timeout=10.0)
    
    @pytest.fixture
    def sample_session(self):
        """Sample session data for testing."""
        return {
            "session_id": "test-session-123",
            "multi_agent_state": {"key": "value"}
        }
    
    @pytest.fixture
    def sample_agent(self):
        """Sample agent data for testing."""
        return {
            "agent_id": "test-agent-456",
            "state": {"agent_key": "agent_value"},
            "conversation_manager_state": {"conv_key": "conv_value"},
            "internal_state": {"internal_key": "internal_value"}
        }
    
    @pytest.fixture
    def sample_message(self):
        """Sample message data for testing."""
        return {
            "message_id": 1,
            "message": {"content": "Hello world"},
            "redact_message": None
        }
    
    # Session CRUD Tests
    
    @pytest.mark.asyncio
    async def test_create_session_success(self, repository, sample_session):
        """Test successful session creation."""
        with patch.object(repository.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = sample_session
            mock_post.return_value = mock_response
            
            result = await repository.create_session(sample_session)
            
            assert result == sample_session
            mock_post.assert_called_once_with(
                "/api/v1/sessions",
                json=sample_session
            )
    
    @pytest.mark.asyncio
    async def test_create_session_http_error(self, repository, sample_session):
        """Test session creation with HTTP error."""
        with patch.object(repository.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"detail": "Invalid data"}
            mock_post.return_value = mock_response
            
            with pytest.raises(SessionRepositoryError, match="Invalid data"):
                await repository.create_session(sample_session)
    
    @pytest.mark.asyncio
    async def test_read_session_success(self, repository, sample_session):
        """Test successful session retrieval."""
        with patch.object(repository.client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_session
            mock_get.return_value = mock_response
            
            result = await repository.read_session("test-session-123")
            
            assert result == sample_session
            mock_get.assert_called_once_with("/api/v1/sessions/test-session-123")
    
    @pytest.mark.asyncio
    async def test_read_session_not_found(self, repository):
        """Test session retrieval when session doesn't exist."""
        with patch.object(repository.client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = await repository.read_session("nonexistent-session")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_session_success(self, repository, sample_session):
        """Test successful session update."""
        update_data = {"multi_agent_state": {"updated": "value"}}
        updated_session = {**sample_session, **update_data}
        
        with patch.object(repository.client, 'put') as mock_put:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = updated_session
            mock_put.return_value = mock_response
            
            result = await repository.update_session("test-session-123", update_data)
            
            assert result == updated_session
            mock_put.assert_called_once_with(
                "/api/v1/sessions/test-session-123",
                json=update_data
            )
    
    @pytest.mark.asyncio
    async def test_update_session_not_found(self, repository):
        """Test session update when session doesn't exist."""
        with patch.object(repository.client, 'put') as mock_put:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"detail": {"message": "Session not found"}}
            mock_response.url = "http://localhost:8001/api/v1/sessions/nonexistent-session"
            mock_put.return_value = mock_response
            
            with pytest.raises(SessionNotFoundError):
                await repository.update_session("nonexistent-session", {"key": "value"})
    
    @pytest.mark.asyncio
    async def test_delete_session_success(self, repository):
        """Test successful session deletion."""
        with patch.object(repository.client, 'delete') as mock_delete:
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_delete.return_value = mock_response
            
            await repository.delete_session("test-session-123")
            
            mock_delete.assert_called_once_with("/api/v1/sessions/test-session-123")
    
    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, repository):
        """Test session deletion when session doesn't exist."""
        with patch.object(repository.client, 'delete') as mock_delete:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_delete.return_value = mock_response
            
            result = await repository.delete_session("nonexistent-session")
            assert result is False
    
    # Agent CRUD Tests
    
    @pytest.mark.asyncio
    async def test_create_agent_success(self, repository, sample_agent):
        """Test successful agent creation."""
        with patch.object(repository.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = sample_agent
            mock_post.return_value = mock_response
            
            result = await repository.create_agent("test-session-123", sample_agent)
            
            assert result == sample_agent
            mock_post.assert_called_once_with(
                "/api/v1/sessions/test-session-123/agents",
                json=sample_agent
            )
    
    @pytest.mark.asyncio
    async def test_create_agent_session_not_found(self, repository, sample_agent):
        """Test agent creation when session doesn't exist."""
        with patch.object(repository.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"detail": {"message": "Session not found"}}
            mock_response.url = "http://localhost:8001/api/v1/sessions/nonexistent-session/agents"
            mock_post.return_value = mock_response
            
            with pytest.raises(SessionNotFoundError):
                await repository.create_agent("nonexistent-session", sample_agent)
    
    @pytest.mark.asyncio
    async def test_read_agent_success(self, repository, sample_agent):
        """Test successful agent retrieval."""
        with patch.object(repository.client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_agent
            mock_get.return_value = mock_response
            
            result = await repository.read_agent("test-session-123", "test-agent-456")
            
            assert result == sample_agent
            mock_get.assert_called_once_with("/api/v1/sessions/test-session-123/agents/test-agent-456")
    
    @pytest.mark.asyncio
    async def test_read_agent_not_found(self, repository):
        """Test agent retrieval when agent doesn't exist."""
        with patch.object(repository.client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = await repository.read_agent("test-session-123", "nonexistent-agent")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_agent_success(self, repository, sample_agent):
        """Test successful agent update."""
        update_data = {"state": {"updated": "agent_value"}}
        updated_agent = {**sample_agent, **update_data}
        
        with patch.object(repository.client, 'put') as mock_put:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = updated_agent
            mock_put.return_value = mock_response
            
            result = await repository.update_agent("test-session-123", "test-agent-456", update_data)
            
            assert result == updated_agent
            mock_put.assert_called_once_with(
                "/api/v1/sessions/test-session-123/agents/test-agent-456",
                json=update_data
            )
    
    @pytest.mark.asyncio
    async def test_update_agent_not_found(self, repository):
        """Test agent update when agent doesn't exist."""
        with patch.object(repository.client, 'put') as mock_put:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"detail": {"message": "Agent not found"}}
            mock_response.url = "http://localhost:8001/api/v1/sessions/test-session-123/agents/nonexistent-agent"
            mock_put.return_value = mock_response
            
            with pytest.raises(AgentNotFoundError):
                await repository.update_agent("test-session-123", "nonexistent-agent", {"key": "value"})
    
    @pytest.mark.asyncio
    async def test_delete_agent_success(self, repository):
        """Test successful agent deletion."""
        with patch.object(repository.client, 'delete') as mock_delete:
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_delete.return_value = mock_response
            
            await repository.delete_agent("test-session-123", "test-agent-456")
            
            mock_delete.assert_called_once_with("/api/v1/sessions/test-session-123/agents/test-agent-456")
    
    @pytest.mark.asyncio
    async def test_delete_agent_not_found(self, repository):
        """Test agent deletion when agent doesn't exist."""
        with patch.object(repository.client, 'delete') as mock_delete:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"detail": {"message": "Agent not found"}}
            mock_response.url = "http://localhost:8001/api/v1/sessions/test-session-123/agents/nonexistent-agent"
            mock_delete.return_value = mock_response
            
            result = await repository.delete_agent("test-session-123", "nonexistent-agent")
            assert result is False
    
    # Message CRUD Tests
    
    @pytest.mark.asyncio
    async def test_create_message_success(self, repository, sample_message):
        """Test successful message creation."""
        with patch.object(repository.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = sample_message
            mock_post.return_value = mock_response
            
            result = await repository.create_message("test-session-123", "test-agent-456", sample_message)
            
            assert result == sample_message
            mock_post.assert_called_once_with(
                "/api/v1/sessions/test-session-123/agents/test-agent-456/messages",
                json=sample_message
            )
    
    @pytest.mark.asyncio
    async def test_create_message_agent_not_found(self, repository, sample_message):
        """Test message creation when agent doesn't exist."""
        with patch.object(repository.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"detail": {"message": "Agent not found"}}
            mock_response.url = "http://localhost:8001/api/v1/sessions/test-session-123/agents/nonexistent-agent/messages"
            mock_post.return_value = mock_response
            
            with pytest.raises(AgentNotFoundError):
                await repository.create_message("test-session-123", "nonexistent-agent", sample_message)
    
    @pytest.mark.asyncio
    async def test_read_message_success(self, repository, sample_message):
        """Test successful message retrieval."""
        with patch.object(repository.client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_message
            mock_get.return_value = mock_response
            
            result = await repository.read_message("test-session-123", "test-agent-456", 1)
            
            assert result == sample_message
            mock_get.assert_called_once_with("/api/v1/sessions/test-session-123/agents/test-agent-456/messages/1")
    
    @pytest.mark.asyncio
    async def test_read_message_not_found(self, repository):
        """Test message retrieval when message doesn't exist."""
        with patch.object(repository.client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = await repository.read_message("test-session-123", "test-agent-456", 999)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_message_success(self, repository, sample_message):
        """Test successful message update."""
        update_data = {"message": {"content": "Updated message"}}
        updated_message = {**sample_message, **update_data}
        
        with patch.object(repository.client, 'put') as mock_put:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = updated_message
            mock_put.return_value = mock_response
            
            result = await repository.update_message("test-session-123", "test-agent-456", 1, update_data)
            
            assert result == updated_message
            mock_put.assert_called_once_with(
                "/api/v1/sessions/test-session-123/agents/test-agent-456/messages/1",
                json=update_data
            )
    
    @pytest.mark.asyncio
    async def test_update_message_not_found(self, repository):
        """Test message update when message doesn't exist."""
        with patch.object(repository.client, 'put') as mock_put:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"detail": {"message": "Message not found"}}
            mock_response.url = "http://localhost:8001/api/v1/sessions/test-session-123/agents/test-agent-456/messages/999"
            mock_put.return_value = mock_response
            
            with pytest.raises(MessageNotFoundError):
                await repository.update_message("test-session-123", "test-agent-456", 999, {"key": "value"})
    
    @pytest.mark.asyncio
    async def test_delete_message_success(self, repository):
        """Test successful message deletion."""
        with patch.object(repository.client, 'delete') as mock_delete:
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_delete.return_value = mock_response
            
            await repository.delete_message("test-session-123", "test-agent-456", 1)
            
            mock_delete.assert_called_once_with("/api/v1/sessions/test-session-123/agents/test-agent-456/messages/1")
    
    @pytest.mark.asyncio
    async def test_delete_message_not_found(self, repository):
        """Test message deletion when message doesn't exist."""
        with patch.object(repository.client, 'delete') as mock_delete:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"detail": {"message": "Message not found"}}
            mock_response.url = "http://localhost:8001/api/v1/sessions/test-session-123/agents/test-agent-456/messages/999"
            mock_delete.return_value = mock_response
            
            result = await repository.delete_message("test-session-123", "test-agent-456", 999)
            assert result is False
    
    # Error Handling Tests
    
    @pytest.mark.asyncio
    async def test_http_timeout_error(self, repository, sample_session):
        """Test handling of HTTP timeout errors."""
        with patch.object(repository.client, 'post') as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timeout")
            
            with pytest.raises(SessionRepositoryError, match="Request timeout"):
                await repository.create_session(sample_session)
    
    @pytest.mark.asyncio
    async def test_http_connection_error(self, repository, sample_session):
        """Test handling of HTTP connection errors."""
        with patch.object(repository.client, 'post') as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(SessionRepositoryError, match="Connection failed"):
                await repository.create_session(sample_session)
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self, repository):
        """Test handling of validation errors (422 status)."""
        with patch.object(repository.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 422
            mock_response.json.return_value = {
                "detail": [
                    {"loc": ["session_id"], "msg": "field required", "type": "value_error.missing"}
                ]
            }
            mock_post.return_value = mock_response
            
            with pytest.raises(SessionRepositoryError, match="Validation error"):
                await repository.create_session({})
    
    # Context Manager Tests
    
    @pytest.mark.asyncio
    async def test_context_manager_success(self, sample_session):
        """Test successful context manager usage."""
        async with PostgreSQLSessionRepository(base_url="http://localhost:8001") as repo:
            assert repo.client is not None
            
            # Mock a successful operation
            with patch.object(repo.client, 'post') as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 201
                mock_response.json.return_value = sample_session
                mock_post.return_value = mock_response
                
                result = await repo.create_session(sample_session)
                assert result == sample_session
    
    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self):
        """Test that context manager properly cleans up resources."""
        repo = PostgreSQLSessionRepository(base_url="http://localhost:8001")
        
        async with repo:
            client = repo.client
            assert client is not None
        
        # After exiting context, client should be closed
        assert repo.client.is_closed