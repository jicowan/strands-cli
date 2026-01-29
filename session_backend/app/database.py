"""Database configuration and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from sqlalchemy import text
from typing import AsyncGenerator, Optional
import logging
import asyncio
from contextlib import asynccontextmanager
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import get_settings

logger = logging.getLogger(__name__)

# Create the declarative base
Base = declarative_base()

# Global variables for engine and session maker
engine = None
async_session_maker = None


class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors."""
    pass


class TransactionError(Exception):
    """Custom exception for transaction errors."""
    pass


def create_database_engine():
    """Create the database engine with proper configuration."""
    settings = get_settings()
    
    return create_async_engine(
        settings.database_url,
        echo=settings.log_level.upper() == "DEBUG",
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=settings.database_pool_pre_ping,
        # Use NullPool for testing to avoid connection issues
        poolclass=NullPool if "test" in settings.database_url else None,
        # Connection pool settings for resilience
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_timeout=30,    # Timeout for getting connection from pool
    )


def get_database_engine():
    """Get or create the database engine."""
    global engine
    if engine is None:
        engine = create_database_engine()
    return engine


def get_session_maker():
    """Get or create the async session maker."""
    global async_session_maker
    if async_session_maker is None:
        async_session_maker = async_sessionmaker(
            bind=get_database_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return async_session_maker


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((DisconnectionError, DatabaseConnectionError))
)
async def execute_with_retry(operation, *args, **kwargs):
    """Execute database operation with retry logic."""
    try:
        return await operation(*args, **kwargs)
    except (DisconnectionError, SQLAlchemyError) as e:
        logger.warning(f"Database operation failed, will retry: {str(e)}")
        raise DatabaseConnectionError(f"Database operation failed: {str(e)}") from e


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session with proper error handling."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_transaction_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session with explicit transaction management."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        async with session.begin():
            try:
                yield session
            except Exception as e:
                logger.error(f"Transaction failed, rolling back: {str(e)}")
                await session.rollback()
                raise TransactionError(f"Transaction failed: {str(e)}") from e


async def check_database_connectivity() -> bool:
    """Check database connectivity with retry logic."""
    try:
        async def _check_connection():
            engine = get_database_engine()
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        
        result = await execute_with_retry(_check_connection)
        logger.info("Database connectivity check successful")
        return result
        
    except Exception as e:
        logger.error(f"Database connectivity check failed: {str(e)}")
        return False


async def get_database_health() -> dict:
    """Get detailed database health information."""
    try:
        engine = get_database_engine()
        
        # Check basic connectivity
        is_connected = await check_database_connectivity()
        
        # Get pool status
        pool = engine.pool
        pool_status = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow()
        }
        
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "connected": is_connected,
            "pool": pool_status,
            "database_url": engine.url.render_as_string(hide_password=True)
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


async def create_tables():
    """Create all database tables with retry logic."""
    async def _create_tables():
        engine = get_database_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    await execute_with_retry(_create_tables)
    logger.info("Database tables created successfully")


async def drop_tables():
    """Drop all database tables (for testing) with retry logic."""
    async def _drop_tables():
        engine = get_database_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    await execute_with_retry(_drop_tables)
    logger.info("Database tables dropped successfully")


async def close_database():
    """Close database connections."""
    global engine, async_session_maker
    if engine:
        await engine.dispose()
        engine = None
        async_session_maker = None
        logger.info("Database connections closed")


async def initialize_database():
    """Initialize database connection and create tables if needed."""
    try:
        # Check connectivity first
        if not await check_database_connectivity():
            raise DatabaseConnectionError("Cannot establish database connection")
        
        # Create tables
        await create_tables()
        
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise DatabaseConnectionError(f"Database initialization failed: {str(e)}") from e