"""FastAPI application for the test-session-agent agent."""

import os
from collections.abc import Callable
from queue import Queue
from threading import Thread
from typing import Iterator, Dict, Optional, Any
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from strands import Agent, tool

from agent.agent import create_agent
from api.models import PromptRequest, SessionResponse

app = FastAPI(title="test-session-agent", description="Test agent for session backend integration")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/health')
def health_check():
    """Health check endpoint for the load balancer."""
    return {"status": "healthy"}

# Define the ready_to_summarize tool
@tool
def ready_to_summarize():
    """Tool that is called by the agent right before summarizing the response."""
    return "Ok - continue providing the summary!"

# Store active agents by session ID for reuse
active_agents: Dict[str, Agent] = {}

def get_or_create_agent(session_id: Optional[str] = None) -> tuple[Agent, str]:
    """Get existing agent or create new one with session management.
    
    Args:
        session_id: Optional session ID. If None, creates a new session.
        
    Returns:
        tuple: (agent, actual_session_id)
    """
    # Generate session ID if not provided
    if not session_id:
        session_id = f"session-{uuid4()}"
    
    # Check if we already have an agent for this session
    if session_id in active_agents:
        return active_agents[session_id], session_id
    
    # Create new agent with session management
    agent = create_agent(session_id=session_id, additional_tools=[ready_to_summarize])
    active_agents[session_id] = agent
    
    return agent, session_id

@app.post('/process', response_model=SessionResponse)
async def process_prompt(request: PromptRequest):
    """Process a prompt with the agent using session management."""
    prompt = request.prompt
    session_id = request.session_id

    if not prompt:
        raise HTTPException(status_code=400, detail="No prompt provided")

    try:
        agent, actual_session_id = get_or_create_agent(session_id)
        response = agent(prompt)
        content = str(response)
        
        return SessionResponse(
            session_id=actual_session_id,
            response=content
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_agent_and_stream_response(prompt: str, session_id: Optional[str] = None):
    """Stream agent responses incrementally with session management.

    Args:
        prompt: The user prompt to process.
        session_id: Optional session ID for conversation persistence.

    Yields:
        str: Chunks of the agent's response.
    """
    # Send initial message to help client detect the start of streaming
    yield "Starting response stream...\n\n"

    try:
        agent, actual_session_id = get_or_create_agent(session_id)
        
        # Send session ID info
        yield f"Session ID: {actual_session_id}\n\n"
        
        # Stream agent response
        async for item in agent.stream_async(prompt):
            # Stream all data
            if "data" in item:
                yield item['data']
    except Exception as e:
        yield f"\n\nError during streaming: {str(e)}"


@app.post('/process-streaming')
async def process_prompt_streaming(request: PromptRequest):
    """Stream the agent's response with session management."""
    try:
        prompt = request.prompt
        session_id = request.session_id

        if not prompt:
            raise HTTPException(status_code=400, detail="No prompt provided")

        return StreamingResponse(
            run_agent_and_stream_response(prompt, session_id),
            media_type="text/plain"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/sessions/{session_id}/history')
async def get_session_history(session_id: str):
    """Get conversation history for a session."""
    try:
        if session_id not in active_agents:
            raise HTTPException(status_code=404, detail="Session not found")
        
        agent = active_agents[session_id]
        
        # Get conversation history from the agent
        messages = []
        if hasattr(agent, 'conversation_manager') and agent.conversation_manager:
            # Extract messages from conversation manager
            for message in agent.conversation_manager.messages:
                messages.append({
                    "role": getattr(message, 'role', 'unknown'),
                    "content": str(message.content) if hasattr(message, 'content') else str(message)
                })
        
        return {
            "session_id": session_id,
            "messages": messages,
            "message_count": len(messages)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete('/sessions/{session_id}')
async def clear_session(session_id: str):
    """Clear a session and its conversation history."""
    try:
        if session_id in active_agents:
            # Remove from active agents
            del active_agents[session_id]
            
        return {"message": f"Session {session_id} cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/sessions')
async def list_active_sessions():
    """List all active sessions."""
    return {
        "active_sessions": list(active_agents.keys()),
        "session_count": len(active_agents)
    }


if __name__ == '__main__':
    # Get port from environment variable or default to 8000
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host='0.0.0.0', port=port)