# Test Session Agent

A Strands agent demonstrating session management with PostgreSQL backend integration.

## Features

- **Session Persistence**: Conversations persist across agent restarts
- **Multiple Sessions**: Support for concurrent user sessions
- **PostgreSQL Backend**: Uses our custom session backend API
- **RESTful API**: FastAPI endpoints with session management
- **Conversation History**: Retrieve and manage conversation history

## Quick Start

### 1. Start the Session Backend

```bash
cd ../session_backend
docker-compose up -d
```

Verify it's running:
```bash
curl http://localhost:8001/health
```

### 2. Install Dependencies

```bash
pip install -e .
```

### 3. Run the Demo

```bash
python test_session_demo.py
```

### 4. Start the API Server

```bash
python -m api.app
```

The API will be available at http://localhost:8000

## API Endpoints

### Process with Session Management
```bash
# Start a new conversation
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, my name is Alice", "session_id": "user-123"}'

# Continue the conversation
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is my name?", "session_id": "user-123"}'
```

### Session Management
```bash
# List active sessions
curl http://localhost:8000/sessions

# Get conversation history
curl http://localhost:8000/sessions/user-123/history

# Clear a session
curl -X DELETE http://localhost:8000/sessions/user-123
```

### Streaming Responses
```bash
curl -X POST http://localhost:8000/process-streaming \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Tell me a story", "session_id": "user-123"}'
```

## Session Management Architecture

The agent uses a custom `PostgreSQLSessionRepository` that implements the Strands `SessionRepository` interface:

```python
from strands.session.repository_session_manager import RepositorySessionManager
from agent.postgresql_session_repository import PostgreSQLSessionRepository

# Create session repository
session_repository = PostgreSQLSessionRepository(base_url="http://localhost:8001")

# Create session manager
session_manager = RepositorySessionManager(
    session_id="user-123",
    session_repository=session_repository
)

# Create agent with session management
agent = Agent(
    system_prompt=SYSTEM_PROMPT,
    tools=tools,
    session_manager=session_manager
)
```

## Configuration

Environment variables:
- `SESSION_BACKEND_URL`: URL of the session backend API (default: http://localhost:8001)
- `PORT`: API server port (default: 8000)

## Testing Session Persistence

The demo script (`test_session_demo.py`) demonstrates:

1. **Session Persistence**: Agent remembers conversations after restart
2. **Session Isolation**: Different sessions don't interfere with each other  
3. **Conversation Continuity**: Multi-turn conversations maintain context
4. **PostgreSQL Integration**: All data persisted to PostgreSQL via REST API

## Integration with Strands CLI

This agent can be built and deployed using the standard Strands CLI workflow:

```bash
# Build Docker image
strands-cli build

# Generate Kubernetes manifests
strands-cli generate helm

# Deploy to EKS (requires AWS setup)
helm install test-session-agent ./deployment/helm/
```

The session backend can be deployed alongside the agent to provide persistent session storage in production environments.

## Project Structure

```
test-session-agent/
├── agent/                          # Core agent implementation
│   ├── agent.py                   # Main agent with session management
│   ├── postgresql_session_repository.py  # Custom session repository
│   ├── prompts.py                 # System prompts
│   └── tools.py                   # Custom tools
├── api/                           # FastAPI wrapper
│   ├── app.py                     # API with session endpoints
│   └── models.py                  # Request/response models
├── deployment/                    # Docker and deployment configs
├── test_session_demo.py          # Session management demo
└── README.md                     # This file
```