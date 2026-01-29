# Design Document: Session Backend API

## Overview

The Session Backend API is a FastAPI-based microservice that provides persistent session storage for Strands agents using PostgreSQL as the backend database. The service implements the Strands `SessionRepository` interface, enabling agents to maintain state and conversation history across multiple interactions in distributed environments.

The API follows RESTful principles and provides comprehensive CRUD operations for sessions, agents, and messages. It integrates seamlessly with the existing strands-cli toolchain through new command-line options and Jinja2 templates.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Strands Agent Application"
        A[Strands Agent] --> B[Custom Session Repository]
        B --> C[HTTP Client]
    end
    
    subgraph "Session Backend API"
        C --> D[FastAPI Application]
        D --> E[Session Service Layer]
        E --> F[Database Repository]
        F --> G[SQLAlchemy ORM]
        G --> H[PostgreSQL Database]
    end
    
    subgraph "Container Environment"
        I[API Container] --> D
        J[PostgreSQL Container] --> H
        K[Docker Compose] --> I
        K --> J
    end
    
    subgraph "Strands CLI Integration"
        L[strands-cli init] --> M[Template Generation]
        M --> N[Session Repository Code]
        M --> O[Docker Compose Config]
        P[strands-cli run] --> K
    end
```

### Component Architecture

The system is organized into the following layers:

1. **API Layer**: FastAPI application with REST endpoints
2. **Service Layer**: Business logic and data validation
3. **Repository Layer**: Database operations and ORM mapping
4. **Database Layer**: PostgreSQL with optimized schema
5. **Integration Layer**: Custom session repository for Strands agents

## Components and Interfaces

### 1. FastAPI Application Structure

```python
# Directory structure
session_backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection and session management
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── session.py       # Session model
│   │   ├── agent.py         # SessionAgent model
│   │   └── message.py       # SessionMessage model
│   ├── schemas/             # Pydantic models for API
│   │   ├── __init__.py
│   │   ├── session.py       # Session schemas
│   │   ├── agent.py         # Agent schemas
│   │   └── message.py       # Message schemas
│   ├── services/            # Business logic layer
│   │   ├── __init__.py
│   │   ├── session_service.py
│   │   ├── agent_service.py
│   │   └── message_service.py
│   └── routers/             # API route handlers
│       ├── __init__.py
│       ├── sessions.py      # Session endpoints
│       ├── agents.py        # Agent endpoints
│       ├── messages.py      # Message endpoints
│       └── health.py        # Health check endpoints
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### 2. Database Models

#### Session Model
```python
class SessionModel(Base):
    __tablename__ = "sessions"
    
    session_id = Column(String, primary_key=True)
    multi_agent_state = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    agents = relationship("SessionAgentModel", back_populates="session", cascade="all, delete-orphan")
```

#### SessionAgent Model
```python
class SessionAgentModel(Base):
    __tablename__ = "session_agents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=False)
    agent_id = Column(String, nullable=False)
    state = Column(JSON, nullable=False)
    conversation_manager_state = Column(JSON, nullable=False)
    internal_state = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Composite unique constraint
    __table_args__ = (UniqueConstraint('session_id', 'agent_id'),)
    
    # Relationships
    session = relationship("SessionModel", back_populates="agents")
    messages = relationship("SessionMessageModel", back_populates="agent", cascade="all, delete-orphan")
```

#### SessionMessage Model
```python
class SessionMessageModel(Base):
    __tablename__ = "session_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=False)
    agent_id = Column(String, nullable=False)
    message_id = Column(Integer, nullable=False)
    message = Column(JSON, nullable=False)
    redact_message = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint('session_id', 'agent_id', 'message_id'),
        ForeignKeyConstraint(['session_id', 'agent_id'], ['session_agents.session_id', 'session_agents.agent_id'])
    )
    
    # Relationships
    agent = relationship("SessionAgentModel", back_populates="messages")
```

### 3. API Endpoints

#### Session Endpoints
- `POST /sessions` - Create a new session
- `GET /sessions/{session_id}` - Retrieve session by ID
- `PUT /sessions/{session_id}` - Update session
- `DELETE /sessions/{session_id}` - Delete session and all associated data

#### Agent Endpoints
- `POST /sessions/{session_id}/agents` - Create agent in session
- `GET /sessions/{session_id}/agents/{agent_id}` - Retrieve agent
- `PUT /sessions/{session_id}/agents/{agent_id}` - Update agent
- `DELETE /sessions/{session_id}/agents/{agent_id}` - Delete agent

#### Message Endpoints
- `POST /sessions/{session_id}/agents/{agent_id}/messages` - Create message
- `GET /sessions/{session_id}/agents/{agent_id}/messages` - List messages (with pagination)
- `GET /sessions/{session_id}/agents/{agent_id}/messages/{message_id}` - Retrieve specific message
- `PUT /sessions/{session_id}/agents/{agent_id}/messages/{message_id}` - Update message

#### Health Endpoints
- `GET /health` - Basic health check
- `GET /health/db` - Database connectivity check

### 4. Custom Session Repository Implementation

```python
class PostgreSQLSessionRepository(SessionRepository):
    """PostgreSQL implementation of Strands SessionRepository interface."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
    
    def create_session(self, session: Session, **kwargs: Any) -> Session:
        """Create a new session via API call."""
        
    def read_session(self, session_id: str, **kwargs: Any) -> Optional[Session]:
        """Read session via API call."""
        
    # ... implement all required methods
```

## Data Models

### Strands Data Model Mapping

The API uses Pydantic schemas that map directly to Strands session data models:

#### Session Schema
```python
class SessionCreate(BaseModel):
    session_id: str
    multi_agent_state: Optional[Dict[str, Any]] = None

class SessionResponse(BaseModel):
    session_id: str
    multi_agent_state: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

#### SessionAgent Schema
```python
class SessionAgentCreate(BaseModel):
    agent_id: str
    state: Dict[str, Any]
    conversation_manager_state: Dict[str, Any]
    internal_state: Dict[str, Any] = Field(default_factory=dict)

class SessionAgentResponse(BaseModel):
    agent_id: str
    state: Dict[str, Any]
    conversation_manager_state: Dict[str, Any]
    internal_state: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

#### SessionMessage Schema
```python
class SessionMessageCreate(BaseModel):
    message_id: int
    message: Dict[str, Any]  # Strands Message format
    redact_message: Optional[Dict[str, Any]] = None

class SessionMessageResponse(BaseModel):
    message_id: int
    message: Dict[str, Any]
    redact_message: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### Database Schema Optimizations

#### Indexes
```sql
-- Performance indexes
CREATE INDEX idx_session_agents_session_id ON session_agents(session_id);
CREATE INDEX idx_session_messages_session_agent ON session_messages(session_id, agent_id);
CREATE INDEX idx_session_messages_created_at ON session_messages(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_messages_pagination ON session_messages(session_id, agent_id, message_id);
```

#### Constraints
- Foreign key constraints ensure referential integrity
- Unique constraints prevent duplicate session/agent/message combinations
- Check constraints validate JSON structure where applicable

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Now I need to analyze the acceptance criteria to determine which ones can be tested as properties:

<function_calls>
<invoke name="prework">
<parameter name="featureName">session-backend-api

### Property Reflection

After analyzing all acceptance criteria, I identified several areas where properties can be consolidated:

**Redundancy Analysis:**
- Properties 1.2 and 2.3 both test round-trip data integrity - these can be combined into comprehensive round-trip properties
- Properties 3.1 and 3.2 both relate to message ordering - these can be combined into a single ordering property
- Properties 4.7 and 9.2 both test error message quality - these can be combined
- Properties 8.3 and 9.4 both test error reporting quality - these can be combined
- Properties 5.6 and 9.3 both test transaction integrity - these can be combined

The following properties provide unique validation value and will be implemented:

### Core Data Properties

**Property 1: Session Storage and Retrieval Integrity**
*For any* valid session data, creating a session then retrieving it should return equivalent session data with the same session ID
**Validates: Requirements 1.1, 1.2**

**Property 2: Session Update Persistence**
*For any* existing session and valid update data, updating the session then retrieving it should return the updated data
**Validates: Requirements 1.3**

**Property 3: Session Cascade Deletion**
*For any* session with associated agents and messages, deleting the session should remove all associated data from the database
**Validates: Requirements 1.4**

**Property 4: Agent Association and Retrieval**
*For any* valid agent data and existing session, creating an agent then retrieving it should return equivalent agent data with proper session association
**Validates: Requirements 2.1, 2.3**

**Property 5: Multiple Agents Per Session**
*For any* session, creating multiple agents with different agent IDs should result in all agents being retrievable from that session
**Validates: Requirements 2.4**

**Property 6: Agent State Serialization Round-trip**
*For any* agent state containing binary data, storing then retrieving the agent should preserve all data through base64 encoding
**Validates: Requirements 2.5**

**Property 7: Message Chronological Ordering**
*For any* sequence of messages added to a session, retrieving the messages should return them in chronological order regardless of insertion order
**Validates: Requirements 3.1, 3.2**

**Property 8: Message Pagination Consistency**
*For any* large set of messages, paginated retrieval should return all messages exactly once across all pages in correct order
**Validates: Requirements 3.3**

**Property 9: Message Metadata Preservation**
*For any* message with metadata, storing then retrieving the message should preserve all timestamps, roles, and content types
**Validates: Requirements 3.4**

### API and Validation Properties

**Property 10: HTTP Status Code Correctness**
*For any* API operation, the returned HTTP status code should match the operation result (2xx for success, 4xx for client errors, 5xx for server errors)
**Validates: Requirements 4.5**

**Property 11: Input Validation and Error Reporting**
*For any* invalid request payload, the API should reject it and return a descriptive error message explaining the validation failure
**Validates: Requirements 1.5, 4.7, 9.2**

**Property 12: Database Referential Integrity**
*For any* attempt to create orphaned records (agents without sessions, messages without agents), the database should reject the operation
**Validates: Requirements 5.2**

**Property 13: Transaction Atomicity**
*For any* multi-step database operation, either all steps should succeed or all should be rolled back, maintaining data consistency
**Validates: Requirements 5.6, 9.3**

### Configuration and Resilience Properties

**Property 14: Environment Configuration Flexibility**
*For any* valid environment variable configuration, changing the configuration should result in corresponding behavior changes in the API
**Validates: Requirements 8.1, 8.4**

**Property 15: Configuration Validation and Error Reporting**
*For any* invalid configuration, the API should fail to start and provide clear error messages describing the configuration problems
**Validates: Requirements 8.3, 9.4**

**Property 16: Log Level Configuration**
*For any* log level setting, changing the log level should result in appropriate filtering of log messages
**Validates: Requirements 8.5**

**Property 17: Database Connection Resilience**
*For any* temporary database connection failure, the API should implement retry logic with exponential backoff before giving up
**Validates: Requirements 9.1**

**Property 18: Concurrent Request Safety**
*For any* set of concurrent requests operating on the same data, the final state should be consistent and no data corruption should occur
**Validates: Requirements 10.1**

**Property 19: Caching Consistency**
*For any* cached data, updates to the underlying data should invalidate or update the cache to maintain consistency
**Validates: Requirements 10.5**

## Error Handling

### Error Categories

1. **Validation Errors (400 Bad Request)**
   - Invalid session ID format
   - Missing required fields
   - Invalid JSON structure
   - Schema validation failures

2. **Not Found Errors (404 Not Found)**
   - Session not found
   - Agent not found
   - Message not found

3. **Conflict Errors (409 Conflict)**
   - Duplicate session ID
   - Duplicate agent ID within session
   - Duplicate message ID within agent

4. **Database Errors (500 Internal Server Error)**
   - Connection failures
   - Transaction failures
   - Constraint violations

5. **Configuration Errors (500 Internal Server Error)**
   - Invalid database connection parameters
   - Missing required environment variables
   - Invalid configuration values

### Error Response Format

```python
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    request_id: str
```

### Retry and Circuit Breaker Logic

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(DatabaseConnectionError)
)
async def execute_with_retry(operation):
    """Execute database operation with retry logic."""
    pass
```

## Testing Strategy

### Dual Testing Approach

The testing strategy employs both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests:**
- Test specific examples and edge cases
- Verify API endpoint functionality
- Test error conditions and edge cases
- Validate configuration scenarios
- Test container deployment scenarios

**Property-Based Tests:**
- Verify universal properties across all inputs using Hypothesis
- Test data integrity and consistency properties
- Validate concurrent access scenarios
- Test serialization/deserialization round-trips
- Verify database constraint enforcement

**Property Test Configuration:**
- Minimum 100 iterations per property test
- Each property test references its design document property
- Tag format: **Feature: session-backend-api, Property {number}: {property_text}**

### Testing Framework Selection

- **Unit Testing**: pytest with async support
- **Property-Based Testing**: Hypothesis for Python
- **API Testing**: httpx for async HTTP client testing
- **Database Testing**: pytest-postgresql for isolated database testing
- **Container Testing**: testcontainers-python for integration testing

### Test Data Generation

Property-based tests will use smart generators that:
- Generate valid Strands session data structures
- Create realistic agent state with binary data
- Generate message sequences with proper metadata
- Create concurrent request scenarios
- Generate various configuration combinations

## Strands CLI Integration

### Template Structure

New Jinja2 templates will be added to the strands-cli templates directory:

```
src/strands_cli/templates/session-backend/
├── app/
│   ├── __init__.py.j2
│   ├── main.py.j2
│   ├── config.py.j2
│   ├── database.py.j2
│   ├── models/
│   │   ├── __init__.py.j2
│   │   ├── session.py.j2
│   │   ├── agent.py.j2
│   │   └── message.py.j2
│   ├── schemas/
│   │   ├── __init__.py.j2
│   │   ├── session.py.j2
│   │   ├── agent.py.j2
│   │   └── message.py.j2
│   ├── services/
│   │   ├── __init__.py.j2
│   │   ├── session_service.py.j2
│   │   ├── agent_service.py.j2
│   │   └── message_service.py.j2
│   └── routers/
│       ├── __init__.py.j2
│       ├── sessions.py.j2
│       ├── agents.py.j2
│       ├── messages.py.j2
│       └── health.py.j2
├── requirements.txt.j2
├── Dockerfile.j2
├── docker-compose.yml.j2
└── session_repository.py.j2  # Custom repository implementation
```

### CLI Command Extensions

#### Modified `init` Command
```python
@click.option(
    '--session-state',
    type=click.Choice(['file', 'postgresql']),
    default='file',
    help='Session state storage backend'
)
def init(name: str, session_state: str, **kwargs):
    """Initialize a new Strands agent project."""
    if session_state == 'postgresql':
        # Generate session backend API templates
        # Include custom session repository in agent code
        # Add session backend service to docker-compose template
        pass
```

#### Extended `run` Command Integration
The `run` command will be extended to programmatically manage the session backend services:

```python
def run(name: str, ui: bool = True, **kwargs):
    """Run the agent locally with Docker Compose."""
    project_path = Path(name)
    
    # Check if project uses PostgreSQL sessions
    if has_postgresql_sessions(project_path):
        # Add session backend services to compose configuration
        compose_config = load_compose_config(project_path)
        compose_config = add_session_backend_services(compose_config)
        
        # Start all services including session backend
        start_services_with_session_backend(compose_config, ui)
    else:
        # Use existing run logic for file-based sessions
        start_services(project_path, ui)

def add_session_backend_services(compose_config: dict) -> dict:
    """Add session backend API and PostgreSQL services to compose config."""
    compose_config['services'].update({
        'session-api': {
            'build': './session_backend',
            'ports': ['8001:8000'],  # Different port to avoid conflicts
            'environment': [
                'DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/sessions',
                'LOG_LEVEL=INFO'
            ],
            'depends_on': {
                'postgres': {'condition': 'service_healthy'}
            },
            'healthcheck': {
                'test': ['CMD', 'curl', '-f', 'http://localhost:8000/health'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            }
        },
        'postgres': {
            'image': 'postgres:15',
            'environment': [
                'POSTGRES_DB=sessions',
                'POSTGRES_USER=postgres',
                'POSTGRES_PASSWORD=password'
            ],
            'volumes': [
                'postgres_data:/var/lib/postgresql/data',
                './session_backend/init.sql:/docker-entrypoint-initdb.d/init.sql'
            ],
            'healthcheck': {
                'test': ['CMD-SHELL', 'pg_isready -U postgres'],
                'interval': '10s',
                'timeout': '5s',
                'retries': 5
            }
        }
    })
    
    if 'volumes' not in compose_config:
        compose_config['volumes'] = {}
    compose_config['volumes']['postgres_data'] = None
    
    return compose_config
```

#### Extended `build` Command Integration
The `build` command will be extended to build session backend containers:

```python
def build(name: str, push: bool = False, **kwargs):
    """Build container images for the agent project."""
    project_path = Path(name)
    
    # Build standard agent container
    build_agent_container(project_path, push, **kwargs)
    
    # Build session backend container if PostgreSQL sessions are enabled
    if has_postgresql_sessions(project_path):
        build_session_backend_container(project_path, push, **kwargs)

def build_session_backend_container(project_path: Path, push: bool, **kwargs):
    """Build the session backend API container."""
    session_backend_path = project_path / "session_backend"
    
    if not session_backend_path.exists():
        raise click.ClickException(f"Session backend directory not found: {session_backend_path}")
    
    # Build session backend API image
    image_name = f"{project_path.name}-session-api"
    tag = kwargs.get('tag', 'latest')
    full_image_name = f"{image_name}:{tag}"
    
    click.echo(f"Building session backend API image: {full_image_name}")
    
    # Use Docker SDK to build the image
    client = docker.from_env()
    try:
        image, build_logs = client.images.build(
            path=str(session_backend_path),
            tag=full_image_name,
            rm=True,
            forcerm=True
        )
        
        # Print build logs
        for log in build_logs:
            if 'stream' in log:
                click.echo(log['stream'].strip())
        
        click.echo(f"✅ Successfully built session backend API image: {full_image_name}")
        
        # Push if requested
        if push:
            push_session_backend_image(client, full_image_name, **kwargs)
            
    except docker.errors.BuildError as e:
        click.echo(f"❌ Failed to build session backend API image: {e}")
        raise click.ClickException("Session backend build failed")

def push_session_backend_image(client, image_name: str, **kwargs):
    """Push session backend image to registry."""
    registry = kwargs.get('registry')
    if registry:
        # Tag for registry
        registry_image = f"{registry}/{image_name}"
        client.images.get(image_name).tag(registry_image)
        
        # Push to registry
        click.echo(f"Pushing session backend API image to registry: {registry_image}")
        push_logs = client.images.push(registry_image, stream=True, decode=True)
        
        for log in push_logs:
            if 'status' in log:
                click.echo(f"{log['status']}: {log.get('progress', '')}")
        
        click.echo(f"✅ Successfully pushed session backend API image: {registry_image}")
    else:
        click.echo("⚠️  No registry specified, skipping session backend push")
```

#### Extended Build Scripts
The generated build scripts will also be extended:

```bash
# scripts/build.sh (extended for PostgreSQL sessions)
#!/bin/bash
set -e

PROJECT_NAME="{{ name }}"
TAG=${1:-latest}

echo "Building agent container..."
docker build -t "${PROJECT_NAME}:${TAG}" .

{% if session_state == 'postgresql' %}
echo "Building session backend API container..."
docker build -t "${PROJECT_NAME}-session-api:${TAG}" ./session_backend

echo "✅ Built containers:"
echo "  - ${PROJECT_NAME}:${TAG}"
echo "  - ${PROJECT_NAME}-session-api:${TAG}"
{% else %}
echo "✅ Built container: ${PROJECT_NAME}:${TAG}"
{% endif %}
```

```bash
# scripts/push.sh (extended for PostgreSQL sessions)
#!/bin/bash
set -e

PROJECT_NAME="{{ name }}"
REGISTRY=${1:-}
TAG=${2:-latest}

if [ -z "$REGISTRY" ]; then
    echo "Usage: $0 <registry> [tag]"
    echo "Example: $0 my-registry.com/myproject latest"
    exit 1
fi

echo "Pushing agent container..."
docker tag "${PROJECT_NAME}:${TAG}" "${REGISTRY}/${PROJECT_NAME}:${TAG}"
docker push "${REGISTRY}/${PROJECT_NAME}:${TAG}"

{% if session_state == 'postgresql' %}
echo "Pushing session backend API container..."
docker tag "${PROJECT_NAME}-session-api:${TAG}" "${REGISTRY}/${PROJECT_NAME}-session-api:${TAG}"
docker push "${REGISTRY}/${PROJECT_NAME}-session-api:${TAG}"

echo "✅ Pushed containers:"
echo "  - ${REGISTRY}/${PROJECT_NAME}:${TAG}"
echo "  - ${REGISTRY}/${PROJECT_NAME}-session-api:${TAG}"
{% else %}
echo "✅ Pushed container: ${REGISTRY}/${PROJECT_NAME}:${TAG}"
{% endif %}
```

#### Multi-Stage Docker Build Support
For efficiency, the session backend can use multi-stage builds:

```dockerfile
# session_backend/Dockerfile.j2
# Multi-stage build for session backend API
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app/ ./app/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Add local packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
The `generate` command will be extended to create Kubernetes manifests for the session backend:

```python
def generate(name: str, output_format: str = "helm", **kwargs):
    """Generate deployment manifests."""
    project_path = Path(name)
    
    if has_postgresql_sessions(project_path):
        if output_format == "helm":
            generate_helm_with_session_backend(project_path, **kwargs)
        else:
            generate_k8s_with_session_backend(project_path, **kwargs)
    else:
        # Use existing generate logic
        generate_standard_manifests(project_path, output_format, **kwargs)

def generate_helm_with_session_backend(project_path: Path, **kwargs):
    """Generate Helm chart including session backend services."""
    # Generate standard agent helm chart
    generate_standard_helm_chart(project_path, **kwargs)
    
    # Add session backend templates
    add_session_backend_helm_templates(project_path, **kwargs)

def add_session_backend_helm_templates(project_path: Path, **kwargs):
    """Add session backend Kubernetes resources to Helm chart."""
    helm_templates_dir = project_path / "deployment" / "helm" / "templates"
    
    # Session API Deployment
    render_template(
        "session-backend/helm/session-api-deployment.yaml.j2",
        helm_templates_dir / "session-api-deployment.yaml",
        **kwargs
    )
    
    # Session API Service (ClusterIP)
    render_template(
        "session-backend/helm/session-api-service.yaml.j2",
        helm_templates_dir / "session-api-service.yaml",
        **kwargs
    )
    
    # PostgreSQL StatefulSet
    render_template(
        "session-backend/helm/postgresql-statefulset.yaml.j2",
        helm_templates_dir / "postgresql-statefulset.yaml",
        **kwargs
    )
    
    # PostgreSQL Headless Service
    render_template(
        "session-backend/helm/postgresql-service.yaml.j2",
        helm_templates_dir / "postgresql-service.yaml",
        **kwargs
    )
    
    # PostgreSQL PVC
    render_template(
        "session-backend/helm/postgresql-pvc.yaml.j2",
        helm_templates_dir / "postgresql-pvc.yaml",
        **kwargs
    )
    
    # ConfigMap for PostgreSQL initialization
    render_template(
        "session-backend/helm/postgresql-configmap.yaml.j2",
        helm_templates_dir / "postgresql-configmap.yaml",
        **kwargs
    )
```

### Kubernetes Deployment Templates

#### Session API Deployment Template
```yaml
# session-backend/helm/session-api-deployment.yaml.j2
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "chart.fullname" . }}-session-api
  labels:
    {{- include "chart.labels" . | nindent 4 }}
    app.kubernetes.io/component: session-api
spec:
  replicas: {{ .Values.sessionApi.replicaCount | default 2 }}
  selector:
    matchLabels:
      {{- include "chart.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: session-api
  template:
    metadata:
      labels:
        {{- include "chart.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: session-api
    spec:
      serviceAccountName: {{ include "chart.serviceAccountName" . }}
      containers:
      - name: session-api
        image: "{{ .Values.sessionApi.image.repository }}:{{ .Values.sessionApi.image.tag }}"
        imagePullPolicy: {{ .Values.sessionApi.image.pullPolicy }}
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        env:
        - name: DATABASE_URL
          value: "postgresql+asyncpg://postgres:{{ .Values.postgresql.auth.password }}@{{ include "chart.fullname" . }}-postgresql:5432/sessions"
        - name: LOG_LEVEL
          value: {{ .Values.sessionApi.logLevel | default "INFO" }}
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          {{- toYaml .Values.sessionApi.resources | nindent 10 }}
```

#### Session API Service Template
```yaml
# session-backend/helm/session-api-service.yaml.j2
apiVersion: v1
kind: Service
metadata:
  name: {{ include "chart.fullname" . }}-session-api
  labels:
    {{- include "chart.labels" . | nindent 4 }}
    app.kubernetes.io/component: session-api
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: http
    protocol: TCP
    name: http
  selector:
    {{- include "chart.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/component: session-api
```

#### PostgreSQL StatefulSet Template
```yaml
# session-backend/helm/postgresql-statefulset.yaml.j2
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {{ include "chart.fullname" . }}-postgresql
  labels:
    {{- include "chart.labels" . | nindent 4 }}
    app.kubernetes.io/component: postgresql
spec:
  serviceName: {{ include "chart.fullname" . }}-postgresql-headless
  replicas: 1
  selector:
    matchLabels:
      {{- include "chart.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: postgresql
  template:
    metadata:
      labels:
        {{- include "chart.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: sessions
        - name: POSTGRES_USER
          value: postgres
        - name: POSTGRES_PASSWORD
          value: {{ .Values.postgresql.auth.password }}
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        ports:
        - name: postgresql
          containerPort: 5432
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
        - name: init-scripts
          mountPath: /docker-entrypoint-initdb.d
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U postgres
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U postgres
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          {{- toYaml .Values.postgresql.resources | nindent 10 }}
      volumes:
      - name: init-scripts
        configMap:
          name: {{ include "chart.fullname" . }}-postgresql-init
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: {{ .Values.postgresql.persistence.size | default "8Gi" }}
      {{- if .Values.postgresql.persistence.storageClass }}
      storageClassName: {{ .Values.postgresql.persistence.storageClass }}
      {{- end }}
```

#### PostgreSQL Headless Service Template
```yaml
# session-backend/helm/postgresql-service.yaml.j2
apiVersion: v1
kind: Service
metadata:
  name: {{ include "chart.fullname" . }}-postgresql-headless
  labels:
    {{- include "chart.labels" . | nindent 4 }}
    app.kubernetes.io/component: postgresql
spec:
  type: ClusterIP
  clusterIP: None
  ports:
  - name: postgresql
    port: 5432
    targetPort: postgresql
  selector:
    {{- include "chart.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/component: postgresql
---
apiVersion: v1
kind: Service
metadata:
  name: {{ include "chart.fullname" . }}-postgresql
  labels:
    {{- include "chart.labels" . | nindent 4 }}
    app.kubernetes.io/component: postgresql
spec:
  type: ClusterIP
  ports:
  - name: postgresql
    port: 5432
    targetPort: postgresql
  selector:
    {{- include "chart.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/component: postgresql
```

#### PostgreSQL ConfigMap Template
```yaml
# session-backend/helm/postgresql-configmap.yaml.j2
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "chart.fullname" . }}-postgresql-init
  labels:
    {{- include "chart.labels" . | nindent 4 }}
    app.kubernetes.io/component: postgresql
data:
  init.sql: |
    -- Create sessions table
    CREATE TABLE IF NOT EXISTS sessions (
        session_id VARCHAR(255) PRIMARY KEY,
        multi_agent_state JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Create session_agents table
    CREATE TABLE IF NOT EXISTS session_agents (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(255) NOT NULL,
        agent_id VARCHAR(255) NOT NULL,
        state JSONB NOT NULL,
        conversation_manager_state JSONB NOT NULL,
        internal_state JSONB NOT NULL DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
        UNIQUE(session_id, agent_id)
    );

    -- Create session_messages table
    CREATE TABLE IF NOT EXISTS session_messages (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(255) NOT NULL,
        agent_id VARCHAR(255) NOT NULL,
        message_id INTEGER NOT NULL,
        message JSONB NOT NULL,
        redact_message JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        FOREIGN KEY (session_id, agent_id) REFERENCES session_agents(session_id, agent_id) ON DELETE CASCADE,
        UNIQUE(session_id, agent_id, message_id)
    );

    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_session_agents_session_id ON session_agents(session_id);
    CREATE INDEX IF NOT EXISTS idx_session_messages_session_agent ON session_messages(session_id, agent_id);
    CREATE INDEX IF NOT EXISTS idx_session_messages_created_at ON session_messages(created_at);
    CREATE INDEX IF NOT EXISTS idx_messages_pagination ON session_messages(session_id, agent_id, message_id);

    -- Create updated_at trigger function
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    -- Create triggers for updated_at
    CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    CREATE TRIGGER update_session_agents_updated_at BEFORE UPDATE ON session_agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    CREATE TRIGGER update_session_messages_updated_at BEFORE UPDATE ON session_messages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### Updated Helm Values Template
```yaml
# session-backend/helm/values-additions.yaml.j2
# Additional values for session backend components
sessionApi:
  enabled: true
  replicaCount: 2
  image:
    repository: {{ .Values.image.repository }}-session-api
    tag: {{ .Values.image.tag }}
    pullPolicy: {{ .Values.image.pullPolicy }}
  logLevel: INFO
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 250m
      memory: 256Mi

postgresql:
  enabled: true
  auth:
    password: {{ .Values.postgresql.auth.password | default "changeme" }}
  persistence:
    enabled: true
    size: 8Gi
    # storageClass: ""
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 500m
      memory: 512Mi
```

### Generated Project Structure with PostgreSQL Sessions

When using `--session-state=postgresql`, the generated project structure includes the session backend:

```
[agent_name]/
├── README.md
├── pyproject.toml
├── agent/
│   ├── __init__.py
│   ├── agent.py
│   ├── tools.py
│   ├── prompts.py
│   └── session_repository.py    # Custom PostgreSQL repository
├── api/
│   ├── __init__.py
│   ├── app.py
│   ├── models.py
│   └── routes.py
├── session_backend/             # New: Session backend API
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── session.py
│   │   │   ├── agent.py
│   │   │   └── message.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── session.py
│   │   │   ├── agent.py
│   │   │   └── message.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── session_service.py
│   │   │   ├── agent_service.py
│   │   │   └── message_service.py
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── sessions.py
│   │       ├── agents.py
│   │       ├── messages.py
│   │       └── health.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── init.sql               # Database initialization script
├── deployment/
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── helm/                  # Extended with session backend templates
│       ├── Chart.yaml
│       ├── values.yaml        # Includes session backend values
│       ├── VALUES.md
│       └── templates/
│           ├── _helpers.tpl
│           ├── deployment.yaml
│           ├── service.yaml
│           ├── serviceaccount.yaml
│           ├── ingress.yaml
│           ├── poddisruptionbudget.yaml
│           ├── hpa.yaml
│           ├── session-api-deployment.yaml    # New
│           ├── session-api-service.yaml       # New
│           ├── postgresql-statefulset.yaml    # New
│           ├── postgresql-service.yaml        # New
│           └── postgresql-configmap.yaml      # New
└── scripts/
    ├── build.sh               # Extended to build session backend
    ├── push.sh                # Extended to push session backend image
    └── deploy.sh              # Extended to deploy session backend
```

### Docker Compose Integration

The `run` command programmatically extends the Docker Compose configuration:

```yaml
# Generated docker-compose.yml (when using PostgreSQL sessions)
version: '3.8'

services:
  agent:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - "./agent:/app/agent"
      - "./api:/app/api"
      - "~/.aws:/home/app/.aws:ro"
    environment:
      - AWS_PROFILE=${AWS_PROFILE}
      - SESSION_BACKEND_URL=http://session-api:8000  # New
    depends_on:
      session-api:
        condition: service_healthy

  ui:
    build: ${UI_TEMPLATE_DIR}
    ports:
      - "8501:8501"
    environment:
      - AGENT_URL=http://agent:8000
    depends_on:
      - agent

  session-api:                 # New service
    build: ./session_backend
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/sessions
      - LOG_LEVEL=INFO
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:                    # New service
    image: postgres:15
    environment:
      - POSTGRES_DB=sessions
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./session_backend/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:               # New volume
```

## Deployment and Operations

### Container Configuration

#### API Container (Dockerfile)
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose Configuration
```yaml
version: '3.8'

services:
  session-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/sessions
      - LOG_LEVEL=INFO
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=sessions
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### Environment Configuration

```python
class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/sessions"
    database_pool_size: int = 20
    database_max_overflow: int = 30
    database_pool_pre_ping: bool = True
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Retry configuration
    retry_attempts: int = 3
    retry_backoff_multiplier: float = 1.0
    retry_backoff_min: float = 4.0
    retry_backoff_max: float = 10.0
    
    class Config:
        env_file = ".env"
```

### Monitoring and Health Checks

#### Health Check Endpoints
- `/health` - Basic application health
- `/health/db` - Database connectivity
- `/health/ready` - Readiness probe for Kubernetes

#### Metrics Collection
- Request/response metrics via middleware
- Database connection pool metrics
- Error rate and latency metrics
- Custom business metrics (sessions created, messages stored)

This design provides a comprehensive, scalable, and maintainable solution for persistent session storage in Strands agents, with seamless integration into the existing strands-cli ecosystem.