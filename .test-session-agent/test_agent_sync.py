#!/usr/bin/env python3
"""Test script for the session-enabled agent (synchronous version)."""

import sys
import os

# Add the current directory to the path so we can import from agent package
sys.path.insert(0, os.path.dirname(__file__))

from agent.agent import create_agent_sync


def main():
    """Test the agent with session management (sync version)."""
    try:
        print("Creating agent with session management (sync)...")
        agent = create_agent_sync(session_id="test-sync-session")
        print("✓ Agent created successfully!")
        
        print("\nTesting agent interaction...")
        response = agent("Hello! Can you tell me what you are?")
        print(f"Agent response: {response}")
        
        print("\nTesting session persistence...")
        response2 = agent("What did I just ask you?")
        print(f"Agent response: {response2}")
        
        print("\n✓ All tests passed!")
        return 0
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)