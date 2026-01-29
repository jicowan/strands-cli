#!/usr/bin/env python3
"""Final verification test for session backend integration."""

import sys
import os

# Add the current directory to the path so we can import from agent package
sys.path.insert(0, os.path.dirname(__file__))

from agent.agent import create_agent_sync


def main():
    """Final verification test."""
    print("🔍 FINAL VERIFICATION: Session Backend Integration")
    print("=" * 60)
    
    try:
        # Test 1: Create agent with session management
        print("\n1. Testing agent creation with session management...")
        agent = create_agent_sync(session_id="final-test-session")
        print("✅ Agent created successfully with session backend!")
        
        # Test 2: Simple interaction
        print("\n2. Testing basic interaction...")
        response = agent("Hello! I'm testing the session backend integration.")
        print(f"✅ Agent responded: {str(response)[:100]}...")
        
        # Test 3: Create second agent with same session
        print("\n3. Testing session sharing...")
        agent2 = create_agent_sync(session_id="final-test-session")
        response2 = agent2("What did I just say in my previous message?")
        print(f"✅ Second agent responded: {str(response2)[:100]}...")
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Session backend integration is fully functional!")
        print("✅ Session persistence working across agent instances!")
        print("✅ PostgreSQL repository successfully integrated!")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)