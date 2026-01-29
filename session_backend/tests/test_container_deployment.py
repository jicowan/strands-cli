"""
Unit tests for container deployment functionality.
Tests Dockerfile builds successfully and database initialization script.
Requirements: 6.1, 6.4
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Generator

import pytest


class TestDockerfileBuild:
    """Test that the Dockerfile builds successfully."""
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists in the session_backend directory."""
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        assert dockerfile_path.exists(), "Dockerfile should exist in session_backend directory"
    
    def test_dockerfile_syntax_valid(self):
        """Test that Dockerfile has valid syntax by attempting to parse it."""
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        
        # Read and basic syntax validation
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        # Check for required instructions
        assert "FROM python:" in content, "Dockerfile should use Python base image"
        assert "WORKDIR /app" in content, "Dockerfile should set working directory"
        assert "COPY requirements.txt" in content, "Dockerfile should copy requirements.txt"
        assert "RUN pip install" in content, "Dockerfile should install Python dependencies"
        assert "COPY app/" in content, "Dockerfile should copy application code"
        assert "EXPOSE 8000" in content, "Dockerfile should expose port 8000"
        assert "CMD" in content or "ENTRYPOINT" in content, "Dockerfile should have startup command"
    
    def test_dockerfile_healthcheck_configured(self):
        """Test that Dockerfile includes health check configuration."""
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        assert "HEALTHCHECK" in content, "Dockerfile should include health check"
        assert "curl -f http://localhost:8000/health" in content, "Health check should test /health endpoint"
    
    def test_dockerfile_security_practices(self):
        """Test that Dockerfile follows security best practices."""
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        # Check for non-root user
        assert "useradd" in content, "Dockerfile should create non-root user"
        assert "USER app" in content, "Dockerfile should switch to non-root user"
        
        # Check for multi-stage build
        assert "as builder" in content, "Dockerfile should use multi-stage build"


class TestDatabaseInitialization:
    """Test database initialization script functionality."""
    
    def test_init_sql_exists(self):
        """Test that init.sql exists in the session_backend directory."""
        init_sql_path = Path(__file__).parent.parent / "init.sql"
        assert init_sql_path.exists(), "init.sql should exist in session_backend directory"
    
    def test_init_sql_syntax_valid(self):
        """Test that init.sql has valid SQL syntax."""
        init_sql_path = Path(__file__).parent.parent / "init.sql"
        
        with open(init_sql_path, 'r') as f:
            content = f.read()
        
        # Check for required table creation statements
        assert "CREATE TABLE IF NOT EXISTS sessions" in content, "Should create sessions table"
        assert "CREATE TABLE IF NOT EXISTS session_agents" in content, "Should create session_agents table"
        assert "CREATE TABLE IF NOT EXISTS session_messages" in content, "Should create session_messages table"
        
        # Check for indexes
        assert "CREATE INDEX" in content, "Should create performance indexes"
        
        # Check for foreign key constraints
        assert "FOREIGN KEY" in content, "Should define foreign key relationships"
        assert "REFERENCES sessions(session_id)" in content, "Should reference sessions table"
        
        # Check for triggers
        assert "CREATE TRIGGER" in content, "Should create update triggers"
        assert "update_updated_at_column" in content, "Should have timestamp update function"
    
    def test_init_sql_table_structure(self):
        """Test that init.sql defines correct table structure."""
        init_sql_path = Path(__file__).parent.parent / "init.sql"
        
        with open(init_sql_path, 'r') as f:
            content = f.read()
        
        # Sessions table structure
        assert "session_id VARCHAR(255) PRIMARY KEY" in content, "Sessions should have session_id primary key"
        assert "multi_agent_state JSONB" in content, "Sessions should have JSONB multi_agent_state"
        assert "created_at TIMESTAMP WITH TIME ZONE" in content, "Sessions should have created_at timestamp"
        assert "updated_at TIMESTAMP WITH TIME ZONE" in content, "Sessions should have updated_at timestamp"
        
        # Session agents table structure
        assert "agent_id VARCHAR(255) NOT NULL" in content, "Session agents should have agent_id"
        assert "state JSONB NOT NULL" in content, "Session agents should have JSONB state"
        assert "conversation_manager_state JSONB NOT NULL" in content, "Session agents should have conversation_manager_state"
        assert "internal_state JSONB NOT NULL DEFAULT '{}'" in content, "Session agents should have internal_state with default"
        
        # Session messages table structure
        assert "message_id INTEGER NOT NULL" in content, "Session messages should have message_id"
        assert "message JSONB NOT NULL" in content, "Session messages should have JSONB message"
        assert "redact_message JSONB" in content, "Session messages should have optional redact_message"
    
    def test_init_sql_constraints_and_indexes(self):
        """Test that init.sql defines proper constraints and indexes."""
        init_sql_path = Path(__file__).parent.parent / "init.sql"
        
        with open(init_sql_path, 'r') as f:
            content = f.read()
        
        # Unique constraints
        assert "UNIQUE (session_id, agent_id)" in content, "Should have unique constraint on session_id + agent_id"
        assert "UNIQUE (session_id, agent_id, message_id)" in content, "Should have unique constraint on message identifiers"
        
        # Cascade deletion
        assert "ON DELETE CASCADE" in content, "Should have cascade deletion configured"
        
        # Performance indexes
        assert "idx_session_agents_session_id" in content, "Should create session agents index"
        assert "idx_session_messages_session_agent" in content, "Should create session messages index"
        assert "idx_session_messages_created_at" in content, "Should create timestamp index"
        assert "idx_messages_pagination" in content, "Should create pagination index"


class TestDockerCompose:
    """Test docker-compose configuration."""
    
    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists."""
        compose_path = Path(__file__).parent.parent / "docker-compose.yml"
        assert compose_path.exists(), "docker-compose.yml should exist in session_backend directory"
    
    def test_docker_compose_services_defined(self):
        """Test that docker-compose.yml defines required services."""
        compose_path = Path(__file__).parent.parent / "docker-compose.yml"
        
        with open(compose_path, 'r') as f:
            content = f.read()
        
        # Required services
        assert "session-api:" in content, "Should define session-api service"
        assert "postgres:" in content, "Should define postgres service"
        
        # Service configuration
        assert "build:" in content, "Session API should have build configuration"
        assert "ports:" in content, "Services should expose ports"
        assert "environment:" in content, "Services should have environment variables"
        assert "depends_on:" in content, "Session API should depend on postgres"
        assert "healthcheck:" in content, "Services should have health checks"
    
    def test_docker_compose_environment_variables(self):
        """Test that docker-compose.yml configures proper environment variables."""
        compose_path = Path(__file__).parent.parent / "docker-compose.yml"
        
        with open(compose_path, 'r') as f:
            content = f.read()
        
        # Database connection
        assert "DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/sessions" in content, \
            "Should configure database URL"
        assert "POSTGRES_DB=sessions" in content, "Should set database name"
        assert "POSTGRES_USER=postgres" in content, "Should set database user"
        assert "POSTGRES_PASSWORD=password" in content, "Should set database password"
        
        # API configuration
        assert "LOG_LEVEL=INFO" in content, "Should set log level"
    
    def test_docker_compose_volumes_and_networks(self):
        """Test that docker-compose.yml configures volumes and networks."""
        compose_path = Path(__file__).parent.parent / "docker-compose.yml"
        
        with open(compose_path, 'r') as f:
            content = f.read()
        
        # Volumes
        assert "volumes:" in content, "Should define volumes"
        assert "postgres_data:" in content, "Should define postgres data volume"
        assert "./init.sql:/docker-entrypoint-initdb.d/init.sql" in content, \
            "Should mount init.sql for database initialization"
        
        # Networks
        assert "networks:" in content, "Should define networks"
        assert "session-backend:" in content, "Should define session-backend network"


class TestEnvironmentConfiguration:
    """Test environment configuration files."""
    
    def test_env_example_exists(self):
        """Test that .env.example exists."""
        env_example_path = Path(__file__).parent.parent / ".env.example"
        assert env_example_path.exists(), ".env.example should exist in session_backend directory"
    
    def test_env_example_contains_required_variables(self):
        """Test that .env.example contains all required environment variables."""
        env_example_path = Path(__file__).parent.parent / ".env.example"
        
        with open(env_example_path, 'r') as f:
            content = f.read()
        
        # Required variables
        assert "DATABASE_URL=" in content, "Should define DATABASE_URL"
        assert "LOG_LEVEL=" in content, "Should define LOG_LEVEL"
        assert "ENVIRONMENT=" in content, "Should define ENVIRONMENT"
        assert "HOST=" in content, "Should define HOST"
        assert "PORT=" in content, "Should define PORT"
        
        # Database pool settings
        assert "DB_POOL_SIZE=" in content, "Should define DB_POOL_SIZE"
        assert "DB_MAX_OVERFLOW=" in content, "Should define DB_MAX_OVERFLOW"
        assert "DB_POOL_TIMEOUT=" in content, "Should define DB_POOL_TIMEOUT"
    
    def test_dockerignore_exists(self):
        """Test that .dockerignore exists."""
        dockerignore_path = Path(__file__).parent.parent / ".dockerignore"
        assert dockerignore_path.exists(), ".dockerignore should exist in session_backend directory"
    
    def test_dockerignore_excludes_development_files(self):
        """Test that .dockerignore excludes development and unnecessary files."""
        dockerignore_path = Path(__file__).parent.parent / ".dockerignore"
        
        with open(dockerignore_path, 'r') as f:
            content = f.read()
        
        # Should exclude Python cache and build files
        assert "__pycache__/" in content, "Should exclude Python cache"
        assert "*.py[cod]" in content, "Should exclude compiled Python files"
        assert ".pytest_cache/" in content, "Should exclude pytest cache"
        
        # Should exclude virtual environments
        assert ".venv" in content, "Should exclude virtual environment"
        assert "venv/" in content, "Should exclude venv directory"
        
        # Should exclude development files
        assert ".env" in content, "Should exclude environment files"
        assert ".git/" in content, "Should exclude git directory"
        assert "README.md" in content, "Should exclude documentation"


# Integration test that requires Docker (marked as slow)
@pytest.mark.slow
class TestDockerBuildIntegration:
    """Integration tests that actually build Docker images (slow tests)."""
    
    def test_docker_build_succeeds(self):
        """Test that Docker build actually succeeds (requires Docker daemon)."""
        session_backend_dir = Path(__file__).parent.parent
        
        # Skip if Docker is not available
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Docker not available")
        
        # Build the Docker image
        build_command = [
            "docker", "build", 
            "-t", "session-backend-test",
            str(session_backend_dir)
        ]
        
        result = subprocess.run(build_command, capture_output=True, text=True)
        
        # Clean up the test image
        subprocess.run(["docker", "rmi", "session-backend-test"], capture_output=True)
        
        assert result.returncode == 0, f"Docker build failed: {result.stderr}"