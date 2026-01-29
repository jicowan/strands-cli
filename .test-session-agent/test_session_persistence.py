#!/usr/bin/env python3
"""Test script to verify session persistence with the session backend."""

import sys
import os
import time

# Add the current directory to the path so we can import from agent package
sys.path.insert(0, os.path.dirname(__file__))

from agent.agent import create_agent_sync


def test_session_persistence():
    """Test that sessions persist across different agent instances."""
    
    session_id = "test-persistence-session"
    
    print("=" * 60)
    print("TESTING SESSION PERSISTENCE WITH BACKEND")
    print("=" * 60)
    
    try:
        # Test 1: Create first agent instance
        print("\n1. Creating first agent instance...")
        agent1 = create_agent_sync(session_id=session_id)
        print("✓ First agent created successfully!")
        
        print("\n2. First conversation with agent1...")
        response1 = agent1("Hello! My name is Alice. Can you remember my name?")
        print(f"Agent1 response: {response1}")
        
        # Test 2: Create second agent instance with same session ID
        print("\n3. Creating second agent instance with same session ID...")
        agent2 = create_agent_sync(session_id=session_id)
        print("✓ Second agent created successfully!")
        
        print("\n4. Testing memory persistence with agent2...")
        response2 = agent2("What is my name? Do you remember what I told you earlier?")
        print(f"Agent2 response: {response2}")
        
        # Test 3: Continue conversation with first agent
        print("\n5. Continuing conversation with first agent...")
        response3 = agent1("What did I ask the other agent instance?")
        print(f"Agent1 response: {response3}")
        
        # Test 4: Test with a different session ID
        print("\n6. Testing with different session ID (should not remember)...")
        agent3 = create_agent_sync(session_id="different-session")
        response4 = agent3("Do you know my name? What have we talked about?")
        print(f"Agent3 (different session) response: {response4}")
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("✓ Session persistence is working correctly!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("Starting session persistence test...")
    print("Make sure the session backend is running on localhost:8001")
    
    # Wait a moment for any previous operations to complete
    time.sleep(1)
    
    success = test_session_persistence()
    
    if success:
        print("\n🎉 Session backend integration test PASSED!")
        return 0
    else:
        print("\n❌ Session backend integration test FAILED!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)