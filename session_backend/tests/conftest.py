"""Shared test fixtures for session backend tests."""

import pytest
import pytest_asyncio
import asyncio
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from fastapi.testclient import TestClient

from app.database import Base, get_db_session
from app.config import get_settings
from app.main import app
# Import all models to ensure they're registered with Base.metadata
from app.models import SessionModel, SessionAgentModel, SessionMessageModel


# Test database URL - use containerized PostgreSQL as per steering guidelines
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://postgres:password@localhost:5432/sessions"
)


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Use NullPool for testing to avoid connection issues
    )
    
    # Tables are created by init.sql - just verify they exist
    max_retries = 10
    for i in range(max_retries):
        try:
            async with engine.begin() as conn:
                from sqlalchemy import text
                result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
                tables = [row[0] for row in result.fetchall()]
                expected_tables = {'sessions', 'session_agents', 'session_messages'}
                if expected_tables.issubset(set(tables)):
                    break
                else:
                    # Tables not ready yet, wait a bit
                    await asyncio.sleep(1)
        except Exception:
            # Connection not ready yet, wait a bit
            await asyncio.sleep(1)
    else:
        raise RuntimeError(f"Required tables not found after {max_retries} retries")
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session_maker(test_engine):
    """Create a test session maker."""
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def test_db_session(test_session_maker) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with proper cleanup."""
    async with test_session_maker() as session:
        try:
            yield session
        finally:
            # Clean up after each test - use DELETE instead of TRUNCATE
            await session.rollback()  # Rollback any pending transaction
            try:
                from sqlalchemy import text
                # Delete in order to respect foreign key constraints
                await session.execute(text("DELETE FROM session_messages"))
                await session.execute(text("DELETE FROM session_agents"))
                await session.execute(text("DELETE FROM sessions"))
                await session.commit()
            except Exception:
                # If delete fails, just rollback
                await session.rollback()


@pytest.fixture
def test_client(test_session_maker):
    """Create a test client with database override and per-test cleanup."""
    async def override_get_db_session():
        async with test_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    # Clean database before each test using direct psql command
    # This bypasses any session/transaction issues
    def clean_database_direct():
        """Clean database using direct psql command."""
        import subprocess
        
        try:
            # Use docker exec to run psql directly on the container
            subprocess.run([
                "docker", "exec", "session_backend-postgres-1", 
                "psql", "-U", "postgres", "-d", "sessions", 
                "-c", "DELETE FROM session_messages; DELETE FROM session_agents; DELETE FROM sessions;"
            ], capture_output=True, check=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Database cleanup failed: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
    
    # Clean database before test
    clean_database_direct()
    
    with TestClient(app) as client:
        yield client
    
    # Clean up after test
    clean_database_direct()
    app.dependency_overrides.clear()


@pytest.fixture
def override_settings():
    """Override settings for tests."""
    def _get_test_settings():
        from app.config import Settings
        return Settings(
            database_url=TEST_DATABASE_URL,
            log_level="DEBUG",
            api_port=8001,  # Different port for tests
        )
    
    return _get_test_settings