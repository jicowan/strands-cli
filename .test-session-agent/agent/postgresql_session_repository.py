"""Synchronous PostgreSQL Session Repository using requests library."""

import json
import logging
from typing import Any, Dict, List, Optional

import requests

# Import Strands session types
from strands.types.session import Session, SessionAgent, SessionMessage

logger = logging.getLogger(__name__)


class SessionRepositoryError(Exception):
    """Base exception for session repository errors."""
    pass


class SessionNotFoundError(SessionRepositoryError):
    """Raised when a session is not found."""
    pass


class AgentNotFoundError(SessionRepositoryError):
    """Raised when an agent is not found."""
    pass


class MessageNotFoundError(SessionRepositoryError):
    """Raised when a message is not found."""
    pass


class DatabaseConnectionError(SessionRepositoryError):
    """Raised when database connection fails."""
    pass


class SyncPostgreSQLSessionRepository:
    """Synchronous PostgreSQL implementation of Strands SessionRepository interface.
    
    This repository communicates with the session backend API via HTTP calls using requests.
    """
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize the PostgreSQL session repository.
        
        Args:
            base_url: Base URL of the session backend API
            timeout: HTTP request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Create session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close()
    
    def _handle_http_error(self, response: requests.Response) -> None:
        """Handle HTTP error responses and raise appropriate exceptions."""
        if response.status_code == 404:
            try:
                error_data = response.json()
                error_message = error_data.get("detail", {}).get("message", "Not found")
                
                # Determine specific error type based on URL path
                if "/messages/" in response.url:
                    raise MessageNotFoundError(error_message)
                elif "/agents/" in response.url:
                    raise AgentNotFoundError(error_message)
                else:
                    raise SessionNotFoundError(error_message)
            except (json.JSONDecodeError, KeyError):
                raise SessionNotFoundError("Resource not found")
        
        elif response.status_code >= 500:
            try:
                error_data = response.json()
                error_message = error_data.get("detail", {}).get("message", "Database error")
            except (json.JSONDecodeError, KeyError):
                error_message = f"Database error: HTTP {response.status_code}"
            raise DatabaseConnectionError(error_message)
        
        else:
            try:
                error_data = response.json()
                if isinstance(error_data, dict) and "detail" in error_data:
                    detail = error_data["detail"]
                    if isinstance(detail, list) and detail:
                        first_error = detail[0]
                        if isinstance(first_error, dict) and "msg" in first_error:
                            error_message = f"Validation error: {first_error['msg']}"
                        else:
                            error_message = f"Validation error: {str(first_error)}"
                    elif isinstance(detail, dict):
                        error_message = detail.get("message", f"HTTP {response.status_code}")
                    else:
                        error_message = str(detail) if detail else f"HTTP {response.status_code}"
                else:
                    error_message = f"HTTP {response.status_code}"
            except (json.JSONDecodeError, KeyError):
                error_message = f"HTTP error: {response.status_code}"
            raise SessionRepositoryError(error_message)
    
    # Session Management Methods
    
    def create_session(self, session: Session, **kwargs: Any) -> Session:
        """Create a new session via API call."""
        try:
            session_dict = {
                "session_id": session.session_id,
                "session_type": session.session_type.value,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/sessions", 
                json=session_dict,
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                response_data = response.json()
                from strands.types.session import SessionType
                return Session(
                    session_id=response_data["session_id"],
                    session_type=SessionType[response_data["session_type"]],
                    created_at=response_data["created_at"],
                    updated_at=response_data["updated_at"]
                )
            else:
                self._handle_http_error(response)
                
        except requests.RequestException as e:
            logger.error(f"Request error creating session: {e}")
            raise DatabaseConnectionError(f"Failed to connect to session backend: {e}")
    
    def read_session(self, session_id: str, **kwargs: Any) -> Optional[Session]:
        """Read session via API call."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/sessions/{session_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                from strands.types.session import SessionType
                return Session(
                    session_id=response_data["session_id"],
                    session_type=SessionType[response_data["session_type"]],
                    created_at=response_data["created_at"],
                    updated_at=response_data["updated_at"]
                )
            elif response.status_code == 404:
                return None
            else:
                self._handle_http_error(response)
                
        except requests.RequestException as e:
            logger.error(f"Request error reading session {session_id}: {e}")
            raise DatabaseConnectionError(f"Failed to connect to session backend: {e}")
    
    def update_session(self, session_id: str, session_data: Dict[str, Any], **kwargs: Any) -> Session:
        """Update session via API call."""
        try:
            response = self.session.put(
                f"{self.base_url}/api/v1/sessions/{session_id}", 
                json=session_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                from strands.types.session import SessionType
                return Session(
                    session_id=response_data["session_id"],
                    session_type=SessionType[response_data["session_type"]],
                    created_at=response_data["created_at"],
                    updated_at=response_data["updated_at"]
                )
            else:
                self._handle_http_error(response)
                
        except requests.RequestException as e:
            logger.error(f"Request error updating session {session_id}: {e}")
            raise DatabaseConnectionError(f"Failed to connect to session backend: {e}")
    
    def delete_session(self, session_id: str, **kwargs: Any) -> bool:
        """Delete session via API call."""
        try:
            response = self.session.delete(
                f"{self.base_url}/api/v1/sessions/{session_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 204:
                return True
            elif response.status_code == 404:
                return False
            else:
                self._handle_http_error(response)
                
        except requests.RequestException as e:
            logger.error(f"Request error deleting session {session_id}: {e}")
            raise DatabaseConnectionError(f"Failed to connect to session backend: {e}")
    
    # Agent Management Methods
    
    def create_agent(self, session_id: str, agent: SessionAgent, **kwargs: Any) -> SessionAgent:
        """Create agent in session via API call."""
        try:
            agent_dict = agent.to_dict()
            response = self.session.post(
                f"{self.base_url}/api/v1/sessions/{session_id}/agents", 
                json=agent_dict,
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                response_data = response.json()
                return SessionAgent.from_dict(response_data)
            else:
                self._handle_http_error(response)
                
        except requests.RequestException as e:
            logger.error(f"Request error creating agent in session {session_id}: {e}")
            raise DatabaseConnectionError(f"Failed to connect to session backend: {e}")
    
    def read_agent(self, session_id: str, agent_id: str, **kwargs: Any) -> Optional[SessionAgent]:
        """Read agent via API call."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/sessions/{session_id}/agents/{agent_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return SessionAgent.from_dict(response_data)
            elif response.status_code == 404:
                return None
            else:
                self._handle_http_error(response)
                
        except requests.RequestException as e:
            logger.error(f"Request error reading agent {agent_id} in session {session_id}: {e}")
            raise DatabaseConnectionError(f"Failed to connect to session backend: {e}")
    
    def update_agent(self, session_id: str, agent: SessionAgent, **kwargs: Any) -> SessionAgent:
        """Update agent via API call."""
        try:
            agent_data = agent.to_dict()
            response = self.session.put(
                f"{self.base_url}/api/v1/sessions/{session_id}/agents/{agent.agent_id}", 
                json=agent_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return SessionAgent.from_dict(response_data)
            else:
                self._handle_http_error(response)
                
        except requests.RequestException as e:
            logger.error(f"Request error updating agent {agent.agent_id} in session {session_id}: {e}")
            raise DatabaseConnectionError(f"Failed to connect to session backend: {e}")
    
    def delete_agent(self, session_id: str, agent_id: str, **kwargs: Any) -> bool:
        """Delete agent via API call."""
        try:
            response = self.session.delete(
                f"{self.base_url}/api/v1/sessions/{session_id}/agents/{agent_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 204:
                return True
            elif response.status_code == 404:
                return False
            else:
                self._handle_http_error(response)
                
        except requests.RequestException as e:
            logger.error(f"Request error deleting agent {agent_id} in session {session_id}: {e}")
            raise DatabaseConnectionError(f"Failed to connect to session backend: {e}")
    
    def list_agents(self, session_id: str, **kwargs: Any) -> List[SessionAgent]:
        """List all agents in a session via API call."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/sessions/{session_id}/agents",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                # Handle paginated response format
                if isinstance(response_data, dict) and "agents" in response_data:
                    agents_data = response_data["agents"]
                else:
                    agents_data = response_data
                return [SessionAgent.from_dict(agent_data) for agent_data in agents_data]
            else:
                self._handle_http_error(response)
                
        except requests.RequestException as e:
            logger.error(f"Request error listing agents in session {session_id}: {e}")
            raise DatabaseConnectionError(f"Failed to connect to session backend: {e}")
    
    # Message Management Methods
    
    def create_message(self, session_id: str, agent_id: str, message: SessionMessage, **kwargs: Any) -> SessionMessage:
        """Create message via API call."""
        try:
            message_dict = message.to_dict()
            response = self.session.post(
                f"{self.base_url}/api/v1/sessions/{session_id}/agents/{agent_id}/messages", 
                json=message_dict,
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                response_data = response.json()
                return SessionMessage.from_dict(response_data)
            else:
                self._handle_http_error(response)
                
        except requests.RequestException as e:
            logger.error(f"Request error creating message in session {session_id}, agent {agent_id}: {e}")
            raise DatabaseConnectionError(f"Failed to connect to session backend: {e}")
    
    def read_message(self, session_id: str, agent_id: str, message_id: int, **kwargs: Any) -> Optional[SessionMessage]:
        """Read message via API call."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/sessions/{session_id}/agents/{agent_id}/messages/{message_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return SessionMessage.from_dict(response_data)
            elif response.status_code == 404:
                return None
            else:
                self._handle_http_error(response)
                
        except requests.RequestException as e:
            logger.error(f"Request error reading message {message_id} in session {session_id}, agent {agent_id}: {e}")
            raise DatabaseConnectionError(f"Failed to connect to session backend: {e}")
    
    def update_message(self, session_id: str, agent_id: str, message_id: int, message_data: Dict[str, Any], **kwargs: Any) -> SessionMessage:
        """Update message via API call."""
        try:
            response = self.session.put(
                f"{self.base_url}/api/v1/sessions/{session_id}/agents/{agent_id}/messages/{message_id}", 
                json=message_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return SessionMessage.from_dict(response_data)
            else:
                self._handle_http_error(response)
                
        except requests.RequestException as e:
            logger.error(f"Request error updating message {message_id} in session {session_id}, agent {agent_id}: {e}")
            raise DatabaseConnectionError(f"Failed to connect to session backend: {e}")
    
    def delete_message(self, session_id: str, agent_id: str, message_id: int, **kwargs: Any) -> bool:
        """Delete message via API call."""
        try:
            response = self.session.delete(
                f"{self.base_url}/api/v1/sessions/{session_id}/agents/{agent_id}/messages/{message_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 204:
                return True
            elif response.status_code == 404:
                return False
            else:
                self._handle_http_error(response)
                
        except requests.RequestException as e:
            logger.error(f"Request error deleting message {message_id} in session {session_id}, agent {agent_id}: {e}")
            raise DatabaseConnectionError(f"Failed to connect to session backend: {e}")
    
    def list_messages(self, session_id: str, agent_id: str, limit: Optional[int] = None, offset: Optional[int] = None, **kwargs: Any) -> List[SessionMessage]:
        """List messages in chronological order with pagination via API call."""
        try:
            params = {}
            
            # Convert limit/offset to page/page_size for the API
            if limit is not None or offset is not None:
                # Default page_size to 10 if not specified
                page_size = limit if limit is not None else 10
                offset_val = offset if offset is not None else 0
                
                # Calculate page number based on offset and page_size
                # If offset is provided without limit, we need to fetch from that offset
                if offset is not None and limit is None:
                    # Use a large page_size to get all remaining messages
                    page = 1
                    page_size = 1000  # Max allowed by API
                    # We'll need to skip the first offset_val items from the result
                    params["page"] = page
                    params["page_size"] = page_size
                else:
                    page = (offset_val // page_size) + 1
                    params["page"] = page
                    params["page_size"] = page_size
            
            response = self.session.get(
                f"{self.base_url}/api/v1/sessions/{session_id}/agents/{agent_id}/messages", 
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                # Handle paginated response format
                if isinstance(response_data, dict) and "messages" in response_data:
                    messages_data = response_data["messages"]
                else:
                    messages_data = response_data
                
                messages = [SessionMessage.from_dict(message_data) for message_data in messages_data]
                
                # If offset was provided without limit, skip the first offset messages
                if offset is not None and limit is None:
                    messages = messages[offset:]
                
                return messages
            else:
                self._handle_http_error(response)
                
        except requests.RequestException as e:
            logger.error(f"Request error listing messages in session {session_id}, agent {agent_id}: {e}")
            raise DatabaseConnectionError(f"Failed to connect to session backend: {e}")
    
    # Health Check Methods
    
    def health_check(self) -> bool:
        """Check if the session backend API is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def database_health_check(self) -> bool:
        """Check if the database connection is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health/db", timeout=self.timeout)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False