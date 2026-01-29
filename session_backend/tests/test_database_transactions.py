"""Property-based tests for database transaction atomicity and connection resilience."""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select
from typing import Dict, Any
from unittest.mock import patch, AsyncMock

from app.models import SessionModel, SessionAgentModel, SessionMessageModel
from app.database import get_transaction_session, check_database_connectivity, execute_with_retry, DatabaseConnectionError


# Test data generators (reusing from test_database_models.py)
@st.composite
def session_data(draw):
    """Generate valid session data with PostgreSQL-safe characters."""
    # Use ASCII-safe characters to avoid PostgreSQL Unicode issues
    session_id = draw(st.text(
        min_size=1, 
        max_size=100, 
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    ))
    
    safe_alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !@#$%^&*()_+-=[]{}|;:,.<>?"
    
    multi_agent_state = draw(st.one_of(
        st.none(),
        st.dictionaries(
            st.text(
                min_size=1, 
                max_size=50,
                alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
            ),
            st.one_of(
                st.text(alphabet=safe_alphabet), 
                st.integers(), 
                st.booleans(), 
                st.none()
            ),
            min_size=0,
            max_size=5
        )
    ))
    return {
        "session_id": session_id,
        "multi_agent_state": multi_agent_state
    }


@st.composite
def agent_data(draw, session_id: str):
    """Generate valid agent data for a given session."""
    agent_id = draw(st.text(
        min_size=1, 
        max_size=100, 
        alphabet=st.characters(min_codepoint=32, max_codepoint=126)
    ))
    state = draw(st.dictionaries(
        st.text(
            min_size=1, 
            max_size=50,
            alphabet=st.characters(min_codepoint=32, max_codepoint=126)
        ),
        st.one_of(
            st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126)), 
            st.integers(), 
            st.booleans()
        ),
        min_size=1,
        max_size=5
    ))
    conversation_manager_state = draw(st.dictionaries(
        st.text(
            min_size=1, 
            max_size=50,
            alphabet=st.characters(min_codepoint=32, max_codepoint=126)
        ),
        st.one_of(
            st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126)), 
            st.integers(), 
            st.booleans()
        ),
        min_size=1,
        max_size=5
    ))
    internal_state = draw(st.dictionaries(
        st.text(
            min_size=1, 
            max_size=50,
            alphabet=st.characters(min_codepoint=32, max_codepoint=126)
        ),
        st.one_of(
            st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126)), 
            st.integers(), 
            st.booleans()
        ),
        min_size=0,
        max_size=3
    ))
    
    return {
        "session_id": session_id,
        "agent_id": agent_id,
        "state": state,
        "conversation_manager_state": conversation_manager_state,
        "internal_state": internal_state
    }


@pytest.mark.asyncio
class TestTransactionAtomicity:
    """Property-based tests for transaction atomicity.
    
    **Feature: session-backend-api, Property 13: Transaction Atomicity**
    """

    @given(transaction_data=st.data())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_transaction_rollback_on_failure(self, transaction_data, test_db_session):
        """
        Property 13: Transaction Atomicity
        For any multi-step database operation, either all steps should succeed 
        or all should be rolled back, maintaining data consistency.
        **Validates: Requirements 5.6, 9.3**
        """
        # Generate session and agent data
        session_data_gen = transaction_data.draw(session_data())
        agent_data_dict = transaction_data.draw(agent_data(session_data_gen["session_id"]))
        
        # Count initial records
        initial_session_count = (await test_db_session.execute(select(SessionModel))).scalars().all()
        initial_agent_count = (await test_db_session.execute(select(SessionAgentModel))).scalars().all()
        
        try:
            async with get_transaction_session() as tx_session:
                # Step 1: Create session (should succeed)
                session = SessionModel(**session_data_gen)
                tx_session.add(session)
                await tx_session.flush()
                
                # Step 2: Create agent (should succeed)
                agent = SessionAgentModel(**agent_data_dict)
                tx_session.add(agent)
                await tx_session.flush()
                
                # Step 3: Force a failure by trying to create duplicate session
                duplicate_session = SessionModel(**session_data_gen)  # Same session_id
                tx_session.add(duplicate_session)
                
                # This should fail and rollback the entire transaction
                await tx_session.commit()
                
        except Exception:
            # Expected to fail due to duplicate session_id
            pass
        
        # Verify that no records were committed (transaction was rolled back)
        final_session_count = (await test_db_session.execute(select(SessionModel))).scalars().all()
        final_agent_count = (await test_db_session.execute(select(SessionAgentModel))).scalars().all()
        
        assert len(final_session_count) == len(initial_session_count)
        assert len(final_agent_count) == len(initial_agent_count)

    @given(transaction_data=st.data())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_successful_transaction_commits_all_changes(self, transaction_data, test_db_session):
        """
        Property 13: Transaction Atomicity
        For any multi-step database operation that succeeds, all steps should be committed.
        **Validates: Requirements 5.6, 9.3**
        """
        import uuid
        import time
        
        # Generate unique session and agent data
        session_data_gen = transaction_data.draw(session_data())
        agent_data_dict = transaction_data.draw(agent_data(session_data_gen["session_id"]))
        
        # Ensure uniqueness to avoid conflicts using UUID and timestamp
        unique_id = f"test_tx_{uuid.uuid4().hex[:8]}_{int(time.time() * 1000000)}"
        session_data_gen["session_id"] = unique_id
        agent_data_dict["session_id"] = unique_id
        
        # Count initial records
        initial_session_count = len((await test_db_session.execute(select(SessionModel))).scalars().all())
        initial_agent_count = len((await test_db_session.execute(select(SessionAgentModel))).scalars().all())
        
        # Execute successful transaction
        async with get_transaction_session() as tx_session:
            # Step 1: Create session
            session = SessionModel(**session_data_gen)
            tx_session.add(session)
            await tx_session.flush()
            
            # Step 2: Create agent
            agent = SessionAgentModel(**agent_data_dict)
            tx_session.add(agent)
            await tx_session.flush()
            
            # Transaction should commit successfully
        
        # Verify that all records were committed
        final_session_count = len((await test_db_session.execute(select(SessionModel))).scalars().all())
        final_agent_count = len((await test_db_session.execute(select(SessionAgentModel))).scalars().all())
        
        assert final_session_count == initial_session_count + 1
        assert final_agent_count == initial_agent_count + 1
        
        # Verify the specific records exist
        created_session = (await test_db_session.execute(
            select(SessionModel).where(SessionModel.session_id == session_data_gen["session_id"])
        )).scalar_one_or_none()
        assert created_session is not None
        
        created_agent = (await test_db_session.execute(
            select(SessionAgentModel).where(
                SessionAgentModel.session_id == session_data_gen["session_id"],
                SessionAgentModel.agent_id == agent_data_dict["agent_id"]
            )
        )).scalar_one_or_none()
        assert created_agent is not None


@pytest.mark.asyncio
class TestDatabaseConnectionResilience:
    """Property-based tests for database connection resilience.
    
    **Feature: session-backend-api, Property 17: Database Connection Resilience**
    """

    @given(retry_data=st.data())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_retry_logic_with_temporary_failures(self, retry_data):
        """
        Property 17: Database Connection Resilience
        For any temporary database connection failure, the API should implement 
        retry logic with exponential backoff before giving up.
        **Validates: Requirements 9.1**
        """
        # Generate number of failures before success
        failure_count = retry_data.draw(st.integers(min_value=1, max_value=2))
        
        call_count = 0
        
        async def mock_operation():
            nonlocal call_count
            call_count += 1
            
            if call_count <= failure_count:
                # Simulate temporary connection failure
                raise DatabaseConnectionError(f"Temporary failure {call_count}")
            else:
                # Success on final attempt
                return "success"
        
        # Test that retry logic eventually succeeds
        result = await execute_with_retry(mock_operation)
        
        assert result == "success"
        assert call_count == failure_count + 1  # Failed attempts + 1 success

    @pytest.mark.asyncio
    async def test_retry_logic_gives_up_after_max_attempts(self):
        """
        Property 17: Database Connection Resilience
        For any persistent database connection failure, the retry logic should 
        give up after the maximum number of attempts.
        **Validates: Requirements 9.1**
        """
        from tenacity import RetryError
        
        call_count = 0
        
        async def always_failing_operation():
            nonlocal call_count
            call_count += 1
            raise DatabaseConnectionError(f"Persistent failure {call_count}")
        
        # Test that retry logic eventually gives up
        with pytest.raises(RetryError):  # tenacity wraps the exception in RetryError
            await execute_with_retry(always_failing_operation)
        
        # Should have tried 3 times (default retry attempts)
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_database_connectivity_check_handles_failures(self):
        """
        Property 17: Database Connection Resilience
        For any database connectivity check, failures should be handled gracefully 
        and return appropriate status.
        **Validates: Requirements 9.1**
        """
        # Test with mocked database failure
        with patch('app.database.get_database_engine') as mock_engine:
            mock_engine.side_effect = Exception("Database unavailable")
            
            result = await check_database_connectivity()
            assert result is False
        
        # Test normal connectivity (should work with test database)
        result = await check_database_connectivity()
        assert result is True