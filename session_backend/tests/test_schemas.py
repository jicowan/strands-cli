"""Property-based tests for API schemas validation and serialization."""

import base64
import json
from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from hypothesis import given, strategies as st, settings, assume
from pydantic import ValidationError

from app.schemas import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionAgentCreate,
    SessionAgentUpdate,
    SessionAgentResponse,
    SessionMessageCreate,
    SessionMessageUpdate,
    SessionMessageResponse,
    ErrorResponse,
)


# Hypothesis strategies for generating test data
@st.composite
def valid_session_id(draw):
    """Generate valid session IDs."""
    # Valid characters: alphanumeric, hyphens, underscores
    chars = st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_",
        min_size=1,
        max_size=255
    )
    return draw(chars)


@st.composite
def invalid_session_id(draw):
    """Generate invalid session IDs."""
    # Choose from various invalid formats
    invalid_type = draw(st.sampled_from([
        "empty",
        "whitespace",
        "special_chars",
        "too_long"
    ]))
    
    if invalid_type == "empty":
        return ""
    elif invalid_type == "whitespace":
        return draw(st.text(alphabet=" \t\n", min_size=1, max_size=10))
    elif invalid_type == "special_chars":
        # Include invalid characters
        return draw(st.text(
            alphabet="!@#$%^&*()+=[]{}|;:,.<>?/~`",
            min_size=1,
            max_size=50
        ))
    elif invalid_type == "too_long":
        return "a" * 256  # Exceeds max length
    
    return ""


@st.composite
def json_data(draw, max_depth=3):
    """Generate JSON-serializable data structures."""
    if max_depth <= 0:
        # Base case: primitive values
        return draw(st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text()
        ))
    
    # Recursive case: containers
    return draw(st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(json_data(max_depth=max_depth-1), max_size=5),
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            json_data(max_depth=max_depth-1),
            max_size=5
        )
    ))


@st.composite
def json_dict_data(draw, max_depth=3):
    """Generate JSON-serializable dictionary data structures."""
    if max_depth <= 0:
        # Base case: primitive values
        return draw(st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(
                st.none(),
                st.booleans(),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text()
            ),
            max_size=3
        ))
    
    # Recursive case: nested dictionaries
    return draw(st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(),
            st.lists(json_data(max_depth=max_depth-1), max_size=3),
            json_dict_data(max_depth=max_depth-1)
        ),
        max_size=5
    ))


@st.composite
def binary_data(draw):
    """Generate binary data for testing serialization."""
    return draw(st.binary(min_size=0, max_size=1000))


@st.composite
def agent_state_with_binary(draw):
    """Generate agent state that may contain binary data."""
    base_state = draw(st.dictionaries(
        st.text(min_size=1, max_size=50),
        json_data(),
        max_size=10
    ))
    
    # Sometimes add binary data
    if draw(st.booleans()):
        binary_key = draw(st.text(min_size=1, max_size=20))
        binary_value = draw(binary_data())
        base_state[binary_key] = binary_value
    
    return base_state


@st.composite
def strands_message(draw):
    """Generate valid Strands message format."""
    role = draw(st.sampled_from(['user', 'assistant', 'system', 'tool', 'function']))
    content = draw(st.text(min_size=0, max_size=1000))
    
    message = {
        'role': role,
        'content': content
    }
    
    # Sometimes add additional fields
    if draw(st.booleans()):
        message['timestamp'] = draw(st.datetimes()).isoformat()
    
    if draw(st.booleans()):
        message['metadata'] = draw(st.dictionaries(
            st.text(min_size=1, max_size=20),
            json_data(max_depth=2),
            max_size=5
        ))
    
    return message


class TestInputValidationAndErrorReporting:
    """Property 11: Input Validation and Error Reporting
    
    **Validates: Requirements 1.5, 4.7, 9.2**
    
    For any invalid request payload, the API should reject it and return 
    a descriptive error message explaining the validation failure.
    """
    
    @given(invalid_session_id())
    @settings(max_examples=100)
    def test_session_create_invalid_session_id_rejected(self, invalid_id):
        """Test that invalid session IDs are rejected with descriptive errors."""
        # Feature: session-backend-api, Property 11: Input Validation and Error Reporting
        
        with pytest.raises(ValidationError) as exc_info:
            SessionCreate(session_id=invalid_id, multi_agent_state=None)
        
        # Verify error message is descriptive
        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        
        # Should have field information
        session_id_errors = [e for e in error_details if 'session_id' in str(e.get('loc', []))]
        assert len(session_id_errors) > 0
        
        # Error message should be descriptive
        error_msg = session_id_errors[0]['msg']
        assert isinstance(error_msg, str)
        assert len(error_msg) > 0
    
    @given(st.text(min_size=1, max_size=255))
    @settings(max_examples=100)
    def test_session_agent_create_invalid_state_rejected(self, agent_id):
        """Test that invalid agent state data is rejected."""
        # Feature: session-backend-api, Property 11: Input Validation and Error Reporting
        
        assume(agent_id.strip() != "")  # Ensure valid agent_id
        
        # Test with non-dict state
        with pytest.raises(ValidationError) as exc_info:
            SessionAgentCreate(
                agent_id=agent_id,
                state="not_a_dict",  # Invalid: should be dict
                conversation_manager_state={},
                internal_state={}
            )
        
        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        
        # Should mention state validation
        state_errors = [e for e in error_details if 'state' in str(e.get('loc', []))]
        assert len(state_errors) > 0
    
    @given(st.integers(), json_data())
    @settings(max_examples=100)
    def test_session_message_create_invalid_message_rejected(self, message_id, invalid_message):
        """Test that invalid message formats are rejected."""
        # Feature: session-backend-api, Property 11: Input Validation and Error Reporting
        
        assume(message_id >= 0)  # Ensure valid message_id
        
        # Test with message missing required fields
        if not isinstance(invalid_message, dict) or 'role' not in invalid_message or 'content' not in invalid_message:
            with pytest.raises(ValidationError) as exc_info:
                SessionMessageCreate(
                    message_id=message_id,
                    message=invalid_message
                )
            
            error_details = exc_info.value.errors()
            assert len(error_details) > 0
            
            # Should have descriptive error about message format
            message_errors = [e for e in error_details if 'message' in str(e.get('loc', []))]
            assert len(message_errors) > 0
    
    @given(st.integers(max_value=-1))
    @settings(max_examples=50)
    def test_negative_message_id_rejected(self, negative_id):
        """Test that negative message IDs are rejected."""
        # Feature: session-backend-api, Property 11: Input Validation and Error Reporting
        
        valid_message = {'role': 'user', 'content': 'test'}
        
        with pytest.raises(ValidationError) as exc_info:
            SessionMessageCreate(
                message_id=negative_id,
                message=valid_message
            )
        
        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        
        # Should mention message_id constraint
        id_errors = [e for e in error_details if 'message_id' in str(e.get('loc', []))]
        assert len(id_errors) > 0


class TestAgentStateSerialization:
    """Property 6: Agent State Serialization Round-trip
    
    **Validates: Requirements 2.5**
    
    For any agent state containing binary data, storing then retrieving 
    the agent should preserve all data through base64 encoding.
    """
    
    @given(valid_session_id(), agent_state_with_binary(), agent_state_with_binary())
    @settings(max_examples=100)
    def test_agent_state_binary_data_round_trip(self, agent_id, state_data, conv_state_data):
        """Test that binary data in agent state survives serialization round-trip."""
        # Feature: session-backend-api, Property 6: Agent State Serialization Round-trip
        
        assume(agent_id.strip() != "")
        
        # Create agent with binary data
        agent_create = SessionAgentCreate(
            agent_id=agent_id,
            state=state_data,
            conversation_manager_state=conv_state_data,
            internal_state={}
        )
        
        # Serialize to JSON (simulating API request/response)
        json_data = agent_create.model_dump_json()
        
        # Deserialize back
        parsed_data = json.loads(json_data)
        recreated_agent = SessionAgentCreate(**parsed_data)
        
        # Verify data integrity
        assert recreated_agent.agent_id == agent_id
        
        # Check that binary data was properly encoded/decoded
        self._verify_binary_data_preserved(state_data, recreated_agent.state)
        self._verify_binary_data_preserved(conv_state_data, recreated_agent.conversation_manager_state)
    
    def _verify_binary_data_preserved(self, original: Any, processed: Any):
        """Verify that binary data was properly preserved through encoding."""
        if isinstance(original, bytes):
            # Should be encoded as base64 dict
            assert isinstance(processed, dict)
            assert processed.get('_type') == 'binary'
            assert '_data' in processed
            
            # Verify we can decode it back
            decoded = base64.b64decode(processed['_data'])
            assert decoded == original
            
        elif isinstance(original, dict):
            assert isinstance(processed, dict)
            for key, value in original.items():
                assert key in processed
                self._verify_binary_data_preserved(value, processed[key])
                
        elif isinstance(original, list):
            assert isinstance(processed, list)
            assert len(processed) == len(original)
            for orig_item, proc_item in zip(original, processed):
                self._verify_binary_data_preserved(orig_item, proc_item)
                
        else:
            # Non-binary data should be unchanged
            assert processed == original
    
    @given(valid_session_id(), agent_state_with_binary())
    @settings(max_examples=100)
    def test_agent_response_binary_data_decoding(self, agent_id, state_data):
        """Test that SessionAgentResponse properly decodes binary data."""
        # Feature: session-backend-api, Property 6: Agent State Serialization Round-trip
        
        assume(agent_id.strip() != "")
        
        # Create response data with encoded binary
        now = datetime.now(timezone.utc)
        
        # First encode the binary data
        encoded_state = SessionAgentCreate._process_binary_data(state_data)
        
        # Create response object
        response = SessionAgentResponse(
            agent_id=agent_id,
            state=encoded_state,
            conversation_manager_state={},
            internal_state={},
            created_at=now,
            updated_at=now
        )
        
        # Verify binary data was decoded back to original form
        self._verify_binary_data_decoded(state_data, response.state)
    
    def _verify_binary_data_decoded(self, original: Any, decoded: Any):
        """Verify that binary data was properly decoded from base64."""
        if isinstance(original, bytes):
            # Should be decoded back to bytes
            assert isinstance(decoded, bytes)
            assert decoded == original
            
        elif isinstance(original, dict):
            assert isinstance(decoded, dict)
            for key, value in original.items():
                assert key in decoded
                self._verify_binary_data_decoded(value, decoded[key])
                
        elif isinstance(original, list):
            assert isinstance(decoded, list)
            assert len(decoded) == len(original)
            for orig_item, dec_item in zip(original, decoded):
                self._verify_binary_data_decoded(orig_item, dec_item)
                
        else:
            # Non-binary data should be unchanged
            assert decoded == original


class TestValidDataAcceptance:
    """Test that valid data is properly accepted and processed."""
    
    @given(valid_session_id(), st.one_of(st.none(), json_dict_data()))
    @settings(max_examples=100)
    def test_valid_session_create_accepted(self, session_id, multi_agent_state):
        """Test that valid session data is accepted."""
        assume(session_id.strip() != "")
        
        # Should not raise any validation errors
        session = SessionCreate(
            session_id=session_id,
            multi_agent_state=multi_agent_state
        )
        
        assert session.session_id == session_id.strip()
        assert session.multi_agent_state == multi_agent_state
    
    @given(valid_session_id(), json_dict_data(), json_dict_data())
    @settings(max_examples=100)
    def test_valid_agent_create_accepted(self, agent_id, state_data, conv_state_data):
        """Test that valid agent data is accepted."""
        assume(agent_id.strip() != "")
        
        # Should not raise any validation errors
        agent = SessionAgentCreate(
            agent_id=agent_id,
            state=state_data,
            conversation_manager_state=conv_state_data
        )
        
        assert agent.agent_id == agent_id.strip()
        assert isinstance(agent.state, dict)
        assert isinstance(agent.conversation_manager_state, dict)
        assert isinstance(agent.internal_state, dict)
    
    @given(st.integers(min_value=0), strands_message())
    @settings(max_examples=100)
    def test_valid_message_create_accepted(self, message_id, message_data):
        """Test that valid message data is accepted."""
        # Should not raise any validation errors
        message = SessionMessageCreate(
            message_id=message_id,
            message=message_data
        )
        
        assert message.message_id == message_id
        assert message.message == message_data
        assert 'role' in message.message
        assert 'content' in message.message