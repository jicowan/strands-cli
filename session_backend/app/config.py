"""Configuration management for the Session Backend API."""

import os
from typing import Optional
from pydantic import validator
from pydantic_settings import BaseSettings
import logging


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database configuration
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/sessions"
    database_pool_size: int = 20
    database_max_overflow: int = 30
    database_pool_pre_ping: bool = True
    database_echo: bool = False
    
    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    api_title: str = "Session Backend API"
    api_description: str = "FastAPI backend for Strands session persistence"
    api_version: str = "0.1.0"
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = None
    
    # Retry configuration
    retry_attempts: int = 3
    retry_backoff_multiplier: float = 1.0
    retry_backoff_min: float = 4.0
    retry_backoff_max: float = 10.0
    
    # Health check configuration
    health_check_timeout: float = 5.0
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False
        
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level is a valid logging level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()
    
    @validator('database_url')
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError('database_url must be a PostgreSQL connection string')
        return v
    
    @validator('api_port')
    def validate_api_port(cls, v):
        """Validate API port is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError('api_port must be between 1 and 65535')
        return v
    
    @validator('database_pool_size')
    def validate_pool_size(cls, v):
        """Validate database pool size is positive."""
        if v <= 0:
            raise ValueError('database_pool_size must be positive')
        return v
    
    @validator('retry_attempts')
    def validate_retry_attempts(cls, v):
        """Validate retry attempts is non-negative."""
        if v < 0:
            raise ValueError('retry_attempts must be non-negative')
        return v


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def validate_configuration() -> None:
    """Validate configuration on startup and report errors clearly."""
    try:
        # Test settings instantiation
        test_settings = Settings()
        
        # Additional validation checks
        if test_settings.database_pool_size > 100:
            logging.warning("Database pool size is very large (%d), consider reducing it", 
                          test_settings.database_pool_size)
        
        if test_settings.retry_attempts > 10:
            logging.warning("Retry attempts is very high (%d), consider reducing it", 
                          test_settings.retry_attempts)
            
        logging.info("Configuration validation successful")
        
    except Exception as e:
        logging.error("Configuration validation failed: %s", str(e))
        raise ValueError(f"Invalid configuration: {str(e)}") from e