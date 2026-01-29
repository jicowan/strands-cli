"""TestSessionAgent agent implementation."""

import os
from typing import Dict, List, Any, Optional

from strands import Agent
from strands.session.repository_session_manager import RepositorySessionManager

from agent.prompts import SYSTEM_PROMPT
from agent.tools import register_tools
from agent.postgresql_session_repository import SyncPostgreSQLSessionRepository
from strands.agent.conversation_manager import SlidingWindowConversationManager


async def create_agent(session_id: Optional[str] = None, additional_tools: Optional[List] = None) -> Agent:
    """Create and configure a Strands agent with session management.

    Args:
        session_id: Optional session ID for persistence. If None, creates a new session.
        additional_tools: Optional list of additional tools to add to the agent.

    Returns:
        Agent: Configured Strands agent with session management.
    """
    # Register any custom tools
    tools = register_tools()

    if additional_tools:
        tools = tools + additional_tools
    
    conversation_manager = SlidingWindowConversationManager(
        window_size=20,
        should_truncate_results=True,
    )

    # For async contexts, create agent without session management for now
    # TODO: Implement proper async session repository
    agent = Agent(
        system_prompt=SYSTEM_PROMPT, 
        tools=tools,
        conversation_manager=conversation_manager,
        # session_manager=session_manager  # Disabled due to async/sync conflicts
    )

    return agent


def create_agent_sync(session_id: Optional[str] = None, additional_tools: Optional[List] = None) -> Agent:
    """Create and configure a Strands agent with session management (synchronous version).

    Args:
        session_id: Optional session ID for persistence. If None, creates a new session.
        additional_tools: Optional list of additional tools to add to the agent.

    Returns:
        Agent: Configured Strands agent with session management.
    """
    from agent.postgresql_session_repository import SyncPostgreSQLSessionRepository
    
    # Register any custom tools
    tools = register_tools()

    if additional_tools:
        tools = tools + additional_tools
    
    conversation_manager = SlidingWindowConversationManager(
        window_size=20,
        should_truncate_results=True,
    )

    # Set up session management with our PostgreSQL backend
    session_backend_url = os.getenv("SESSION_BACKEND_URL", "http://localhost:8001")
    
    # Create session repository
    session_repository = SyncPostgreSQLSessionRepository(base_url=session_backend_url)
    
    # Create session manager with repository
    session_manager = RepositorySessionManager(
        session_id=session_id or f"agent-session-{os.getpid()}",
        session_repository=session_repository
    )

    # Create the agent with session management
    agent = Agent(
        system_prompt=SYSTEM_PROMPT, 
        tools=tools,
        conversation_manager=conversation_manager,
        session_manager=session_manager
    )

    return agent


def process_request(prompt: str, session_id: Optional[str] = None) -> str:
    """Process a user request with the Strands agent.

    Args:
        prompt: The user prompt to process.
        session_id: Optional session ID for persistence.

    Returns:
        str: The agent's response.
    """
    agent = create_agent_sync(session_id=session_id)
    response = agent(prompt)

    return str(response)