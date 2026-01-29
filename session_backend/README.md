# Session Backend API

A FastAPI-based session management backend for Strands agents, providing persistent storage for sessions, agents, and messages using PostgreSQL.

## Overview

The Session Backend provides:
- **RESTful API** for session management
- **PostgreSQL persistence** for conversations and agent state
- **Strands-compatible schema** matching Strands session types
- **Client-side repository** for easy integration with Strands agents
- **Docker deployment** with Docker Compose and Kubernetes/Helm support

## Quick Start

### 1. Start the Session Backend

Using Docker Compose (recommended):

```bash
cd session_backend
docker-compose up -d
```

Verify it's running:
```bash
curl http://localhost:8001/health
curl http://localhost:8001/health/db
```

View API documentation:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### 2. Stop the Services

```bash
docker-compose down
```

### Development with pgAdmin

Start with pgAdmin for database management:
```bash
docker-compose --profile dev-tools up -d
```

Access pgAdmin at http://localhost:8080 (admin@example.com / admin)

## API Endpoints

### Health Checks
- `GET /health` - Service health
- `GET /health/db` - Database connectivity

### Sessions
- `POST /api/v1/sessions` - Create session
- `GET /api/v1/sessions/{session_id}` - Get session
- `PUT /api/v1/sessions/{session_id}` - Update session
- `DELETE /api/v1/sessions/{session_id}` - Delete session (cascades to agents and messages)

### Agents
- `POST /api/v1/sessions/{session_id}/agents` - Create agent
- `GET /api/v1/sessions/{session_id}/agents/{agent_id}` - Get agent
- `PUT /api/v1/sessions/{session_id}/agents/{agent_id}` - Update agent
- `DELETE /api/v1/sessions/{session_id}/agents/{agent_id}` - Delete agent (cascades to messages)
- `GET /api/v1/sessions/{session_id}/agents` - List agents

### Messages
- `POST /api/v1/sessions/{session_id}/agents/{agent_id}/messages` - Create message
- `GET /api/v1/sessions/{session_id}/agents/{agent_id}/messages/{message_id}` - Get message
- `PUT /api/v1/sessions/{session_id}/agents/{agent_id}/messages/{message_id}` - Update message
- `DELETE /api/v1/sessions/{session_id}/agents/{agent_id}/messages/{message_id}` - Delete message
- `GET /api/v1/sessions/{session_id}/agents/{agent_id}/messages` - List messages (with pagination)

## Integration with Strands Agents

### Overview

The session backend integrates with Strands agents through a client-side repository that implements the Strands `SessionRepository` interface. This repository acts as a shim/adapter that translates Strands method calls into HTTP API requests.

### Step-by-Step Integration

#### 1. Copy the Repository File

Copy `postgresql_session_repository.py` to your agent project:

```bash
# From the session_backend directory
cp postgresql_session_repository.py /path/to/your-agent/agent/
```

Or from the test-session-agent example:
```bash
cp test-session-agent/agent/postgresql_session_repository.py /path/to/your-agent/agent/
```

#### 2. Install Required Dependencies

Add to your agent's `pyproject.toml` or `requirements.txt`:

```toml
# pyproject.toml
dependencies = [
    "strands-agents>=0.1.0",
    "requests>=2.31.0",  # For HTTP client
]
```

Or in `requirements.txt`:
```
strands-agents>=0.1.0
requests>=2.31.0
```

#### 3. Update Your Agent Code

Modify your agent's factory function to use the session repository:

```python
# agent/agent.py
from strands.agent import Agent
from strands.session.repository_session_manager import RepositorySessionManager
from agent.postgresql_session_repository import SyncPostgreSQLSessionRepository
from agent.prompts import SYSTEM_PROMPT
from agent.tools import register_tools

def create_agent(
    session_id: str,
    session_backend_url: str = "http://localhost:8001"
) -> Agent:
    """Create a Strands agent with PostgreSQL session management.
    
    Args:
        session_id: Unique identifier for the session
        session_backend_url: URL of the session backend API
        
    Returns:
        Agent: Configured Strands agent with session persistence
    """
    # Register any custom tools
    tools = register_tools()
    
    # Create session repository (client-side adapter)
    session_repository = SyncPostgreSQLSessionRepository(
        base_url=session_backend_url
    )
    
    # Create session manager with repository
    session_manager = RepositorySessionManager(
        session_id=session_id,
        repository=session_repository
    )
    
    # Create agent with session management
    agent = Agent(
        agent_id="my-agent",  # Unique agent identifier
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        session_manager=session_manager
    )
    
    return agent
```

#### 4. Use the Agent

```python
# Create agent with session management
agent = create_agent(session_id="user-123")

# Process messages - conversation history is automatically persisted
response = agent.process("Hello, my name is Alice")
print(response)

# Later, create a new agent instance with the same session_id
# It will automatically load the conversation history
agent2 = create_agent(session_id="user-123")
response2 = agent2.process("What is my name?")
print(response2)  # Agent remembers: "Your name is Alice"
```

#### 5. Environment Configuration

Set the session backend URL via environment variable:

```python
import os

def create_agent(session_id: str) -> Agent:
    session_backend_url = os.getenv(
        "SESSION_BACKEND_URL", 
        "http://localhost:8001"
    )
    
    session_repository = SyncPostgreSQLSessionRepository(
        base_url=session_backend_url
    )
    # ... rest of the code
```

### Complete Example

See the `test-session-agent` directory for a complete working example:

```bash
# Start session backend
cd session_backend
docker-compose up -d

# Run the demo
cd ../test-session-agent
python test_session_demo.py
```

The demo demonstrates:
- Session persistence across agent restarts
- Multiple concurrent sessions
- Conversation continuity
- PostgreSQL integration

### API Integration Example

If you're building a FastAPI wrapper for your agent:

```python
# api/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent.agent import create_agent

app = FastAPI()

class ProcessRequest(BaseModel):
    prompt: str
    session_id: str

@app.post("/process")
async def process_message(request: ProcessRequest):
    """Process a message with session management."""
    try:
        # Create agent with session
        agent = create_agent(session_id=request.session_id)
        
        # Process message (automatically persisted)
        response = agent.process(request.prompt)
        
        return {
            "response": response,
            "session_id": request.session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}/history")
async def get_history(session_id: str):
    """Get conversation history for a session."""
    from agent.postgresql_session_repository import SyncPostgreSQLSessionRepository
    
    repo = SyncPostgreSQLSessionRepository(base_url="http://localhost:8001")
    
    # Get messages for the session
    messages = repo.list_messages(session_id, "my-agent")
    
    return {
        "session_id": session_id,
        "message_count": len(messages),
        "messages": [msg.to_dict() for msg in messages]
    }
```

### Session Management Features

The repository provides:

- **Automatic Persistence**: All messages and agent state automatically saved
- **Session Isolation**: Different sessions don't interfere with each other
- **Conversation History**: Full conversation history maintained
- **Multi-Agent Support**: Multiple agents per session
- **Pagination**: Efficient message retrieval with limit/offset
- **Error Handling**: Proper exception handling with custom error types
- **Connection Management**: Context manager support for resource cleanup

### Repository Methods

The `SyncPostgreSQLSessionRepository` implements all Strands SessionRepository methods:

**Session Management:**
- `create_session(session)` - Create new session
- `read_session(session_id)` - Get session by ID
- `update_session(session_id, data)` - Update session
- `delete_session(session_id)` - Delete session

**Agent Management:**
- `create_agent(session_id, agent)` - Create agent in session
- `read_agent(session_id, agent_id)` - Get agent
- `update_agent(session_id, agent)` - Update agent state
- `delete_agent(session_id, agent_id)` - Delete agent
- `list_agents(session_id)` - List all agents in session

**Message Management:**
- `create_message(session_id, agent_id, message)` - Create message
- `read_message(session_id, agent_id, message_id)` - Get message
- `update_message(session_id, agent_id, message_id, data)` - Update message
- `delete_message(session_id, agent_id, message_id)` - Delete message
- `list_messages(session_id, agent_id, limit, offset)` - List messages with pagination

**Health Checks:**
- `health_check()` - Check API health
- `database_health_check()` - Check database connectivity

## Configuration

### Environment Variables

**Session Backend API:**
- `DATABASE_URL` - PostgreSQL connection string (default: postgresql+asyncpg://postgres:password@postgres:5432/sessions)
- `LOG_LEVEL` - Logging level (default: INFO)
- `ENVIRONMENT` - Environment name (default: development)
- `API_PORT` - API port (default: 8000)

**Agent Integration:**
- `SESSION_BACKEND_URL` - URL of session backend API (default: http://localhost:8001)

## Architecture

### Backend Components
- **FastAPI** - Web framework with automatic OpenAPI documentation
- **PostgreSQL** - Primary database with async support via asyncpg
- **SQLAlchemy** - ORM with async support
- **Pydantic** - Data validation and serialization
- **Docker** - Multi-stage containerization

### Client Components
- **SyncPostgreSQLSessionRepository** - Synchronous HTTP client implementing Strands SessionRepository interface
- **requests** - HTTP library for API communication
- **Strands Types** - Session, SessionAgent, SessionMessage types

### Data Flow

```
Strands Agent
    ↓
RepositorySessionManager
    ↓
SyncPostgreSQLSessionRepository (client-side shim)
    ↓ HTTP/REST
Session Backend API
    ↓
PostgreSQL Database
```

## Database Schema

The PostgreSQL schema is Strands-compatible:

```sql
-- Sessions table
CREATE TABLE sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    session_type session_type_enum NOT NULL DEFAULT 'AGENT',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agents table
CREATE TABLE session_agents (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    state JSONB NOT NULL,
    conversation_manager_state JSONB NOT NULL,
    internal_state JSONB NOT NULL DEFAULT '{}',
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    UNIQUE (session_id, agent_id)
);

-- Messages table
CREATE TABLE session_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    message_id INTEGER NOT NULL,
    message JSONB NOT NULL,
    redact_message JSONB,
    FOREIGN KEY (session_id, agent_id) REFERENCES session_agents(session_id, agent_id) ON DELETE CASCADE,
    UNIQUE (session_id, agent_id, message_id)
);
```

## Testing

### Backend Tests

Run the test suite:
```bash
cd session_backend
pip install -e ".[dev]"
pytest
```

### Integration Tests

Test the complete integration:
```bash
# Start session backend
cd session_backend
docker-compose up -d

# Run integration tests
cd ../test-session-agent
python test_api_comprehensive.py  # Tests all API endpoints
python test_final_verification.py  # Tests agent integration
```

## Deployment

### Docker Compose (Development)

```bash
docker-compose up -d
```

### Kubernetes/Helm (Production)

See the [Helm deployment guide](helm/DEPLOYMENT_GUIDE.md) for complete instructions:

```bash
cd helm

# Development
helm install session-backend ./session-backend \
  -f session-backend/values-development.yaml

# Production
helm install session-backend ./session-backend \
  -f session-backend/values-production.yaml
```

## Troubleshooting

### Connection Issues

**Agent can't connect to session backend:**
```bash
# Check if session backend is running
curl http://localhost:8001/health

# Check Docker containers
docker ps | grep session

# View logs
docker logs session_backend-session-api-1
```

**Database connection failed:**
```bash
# Check PostgreSQL
docker logs session_backend-postgres-1

# Test connection
docker exec session_backend-postgres-1 psql -U postgres -d sessions -c "SELECT 1"
```

### Session Not Persisting

**Verify data is being saved:**
```bash
# Connect to PostgreSQL
docker exec -it session_backend-postgres-1 psql -U postgres -d sessions

# Check data
SELECT COUNT(*) FROM sessions;
SELECT COUNT(*) FROM session_agents;
SELECT COUNT(*) FROM session_messages;
```

### Import Errors

**Module not found:**
```bash
# Ensure repository file is in agent directory
ls agent/postgresql_session_repository.py

# Install dependencies
pip install requests strands-agents
```

## Documentation

- **[API Test Results](test-session-agent/API_TEST_RESULTS.md)** - Comprehensive API test coverage
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Technical architecture details
- **[Pagination Fix](PAGINATION_FIX.md)** - Details on limit/offset translation
- **[Helm Deployment](helm/DEPLOYMENT_GUIDE.md)** - Kubernetes deployment guide
- **[Test Agent Example](test-session-agent/README.md)** - Complete working example

## Support

For issues and questions:
- Documentation: https://strandsagents.com/documentation
- GitHub: https://github.com/your-org/strands-cli

## License

Copyright © 2026 Strands Team