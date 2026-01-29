"""Property-based tests for configuration management.

Feature: session-backend-api, Property 14: Environment Configuration Flexibility
Validates: Requirements 8.1, 8.4
"""

import os
import pytest
from hypothesis import given, strategies as st, settings
from pydantic import ValidationError

from app.config import Settings, validate_configuration


class TestConfigurationManagement:
    """Property-based tests for configuration management."""
    
    @given(
        database_url=st.one_of(
            st.just("postgresql://user:pass@localhost:5432/db"),
            st.just("postgresql+asyncpg://user:pass@localhost:5432/db")
        ),
        log_level=st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
        api_port=st.integers(min_value=1, max_value=65535),
        database_pool_size=st.integers(min_value=1, max_value=100),
        retry_attempts=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=100)
    def test_environment_configuration_flexibility(self, database_url, log_level, 
                                                  api_port, database_pool_size, retry_attempts):
        """
        Property 14: Environment Configuration Flexibility
        For any valid environment variable configuration, changing the configuration 
        should result in corresponding behavior changes in the API.
        
        **Validates: Requirements 8.1, 8.4**
        """
        # Set environment variables
        env_vars = {
            'DATABASE_URL': database_url,
            'LOG_LEVEL': log_level,
            'API_PORT': str(api_port),
            'DATABASE_POOL_SIZE': str(database_pool_size),
            'RETRY_ATTEMPTS': str(retry_attempts)
        }
        
        # Store original environment
        original_env = {}
        for key in env_vars:
            original_env[key] = os.environ.get(key)
        
        try:
            # Set new environment variables
            for key, value in env_vars.items():
                os.environ[key] = value
            
            # Create settings instance
            settings = Settings()
            
            # Verify configuration changes are reflected
            assert settings.database_url == database_url
            assert settings.log_level == log_level
            assert settings.api_port == api_port
            assert settings.database_pool_size == database_pool_size
            assert settings.retry_attempts == retry_attempts
            
        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    
    @given(
        database_url=st.text(min_size=1, max_size=100).filter(lambda x: '\x00' not in x),
        log_level=st.text(min_size=1, max_size=20).filter(lambda x: '\x00' not in x),
        api_port=st.integers(),
        database_pool_size=st.integers(),
        retry_attempts=st.integers()
    )
    @settings(max_examples=100)
    def test_configuration_validation_robustness(self, database_url, log_level, 
                                                api_port, database_pool_size, retry_attempts):
        """
        Test that configuration validation handles arbitrary inputs gracefully.
        Invalid configurations should raise ValidationError with descriptive messages.
        """
        # Filter out valid configurations to focus on invalid ones
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        valid_db_prefixes = ['postgresql://', 'postgresql+asyncpg://']
        
        is_valid_config = (
            any(database_url.startswith(prefix) for prefix in valid_db_prefixes) and
            log_level.upper() in valid_log_levels and
            1 <= api_port <= 65535 and
            database_pool_size > 0 and
            retry_attempts >= 0
        )
        
        # Set environment variables
        env_vars = {
            'DATABASE_URL': database_url,
            'LOG_LEVEL': log_level,
            'API_PORT': str(api_port),
            'DATABASE_POOL_SIZE': str(database_pool_size),
            'RETRY_ATTEMPTS': str(retry_attempts)
        }
        
        # Store original environment
        original_env = {}
        for key in env_vars:
            original_env[key] = os.environ.get(key)
        
        try:
            # Set new environment variables
            for key, value in env_vars.items():
                os.environ[key] = value
            
            if is_valid_config:
                # Valid configuration should work
                settings = Settings()
                assert settings.database_url == database_url
                assert settings.log_level == log_level.upper()
                assert settings.api_port == api_port
                assert settings.database_pool_size == database_pool_size
                assert settings.retry_attempts == retry_attempts
            else:
                # Invalid configuration should raise ValidationError
                with pytest.raises(ValidationError):
                    Settings()
                    
        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    
    @given(
        invalid_database_url=st.one_of(
            st.just(""),
            st.just("invalid://url"),
            st.just("mysql://user:pass@localhost:5432/db"),
            st.just("http://not-a-database")
        ),
        invalid_log_level=st.one_of(
            st.just("INVALID"),
            st.just("trace"),
            st.just(""),
            st.just("123")
        ),
        invalid_port=st.one_of(
            st.integers(max_value=0),
            st.integers(min_value=65536),
            st.just(-1),
            st.just(100000)
        ),
        invalid_pool_size=st.one_of(
            st.integers(max_value=0),
            st.just(-1),
            st.just(-100)
        )
    )
    @settings(max_examples=100)
    def test_configuration_validation_and_error_reporting(self, invalid_database_url, 
                                                         invalid_log_level, invalid_port, 
                                                         invalid_pool_size):
        """
        Property 15: Configuration Validation and Error Reporting
        For any invalid configuration, the API should fail to start and provide 
        clear error messages describing the configuration problems.
        
        **Validates: Requirements 8.3, 9.4**
        """
        # Test invalid database URL
        original_db_url = os.environ.get('DATABASE_URL')
        try:
            os.environ['DATABASE_URL'] = invalid_database_url
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            # Verify error message is descriptive
            error_message = str(exc_info.value)
            assert "database_url" in error_message.lower()
            
        finally:
            if original_db_url is None:
                os.environ.pop('DATABASE_URL', None)
            else:
                os.environ['DATABASE_URL'] = original_db_url
        
        # Test invalid log level
        original_log_level = os.environ.get('LOG_LEVEL')
        try:
            os.environ['LOG_LEVEL'] = invalid_log_level
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            # Verify error message is descriptive
            error_message = str(exc_info.value)
            assert "log_level" in error_message.lower()
            
        finally:
            if original_log_level is None:
                os.environ.pop('LOG_LEVEL', None)
            else:
                os.environ['LOG_LEVEL'] = original_log_level
        
        # Test invalid port
        original_port = os.environ.get('API_PORT')
        try:
            os.environ['API_PORT'] = str(invalid_port)
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            # Verify error message is descriptive
            error_message = str(exc_info.value)
            assert "api_port" in error_message.lower()
            
        finally:
            if original_port is None:
                os.environ.pop('API_PORT', None)
            else:
                os.environ['API_PORT'] = original_port
        
        # Test invalid pool size
        original_pool_size = os.environ.get('DATABASE_POOL_SIZE')
        try:
            os.environ['DATABASE_POOL_SIZE'] = str(invalid_pool_size)
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            # Verify error message is descriptive
            error_message = str(exc_info.value)
            assert "database_pool_size" in error_message.lower()
            
        finally:
            if original_pool_size is None:
                os.environ.pop('DATABASE_POOL_SIZE', None)
            else:
                os.environ['DATABASE_POOL_SIZE'] = original_pool_size
    
    def test_validate_configuration_function(self):
        """Test the validate_configuration function with various scenarios."""
        # Test with valid configuration
        original_env = {}
        valid_env = {
            'DATABASE_URL': 'postgresql://user:pass@localhost:5432/db',
            'LOG_LEVEL': 'INFO',
            'API_PORT': '8000'
        }
        
        # Store original values
        for key in valid_env:
            original_env[key] = os.environ.get(key)
        
        try:
            # Set valid environment
            for key, value in valid_env.items():
                os.environ[key] = value
            
            # Should not raise exception
            validate_configuration()
            
            # Test with invalid configuration
            os.environ['DATABASE_URL'] = 'invalid-url'
            
            with pytest.raises(ValueError) as exc_info:
                validate_configuration()
            
            # Verify error message mentions configuration
            assert "configuration" in str(exc_info.value).lower()
            
        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value