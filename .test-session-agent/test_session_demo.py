#!/usr/bin/env python3
"""
Demo script to test session management with the PostgreSQL backend.

This script demonstrates:
1. Creating agents with session persistence
2. Having conversations that persist across agent instances
3. Retrieving conversation history
4. Multiple concurrent sessions

Prerequisites:
- Session backend running on localhost:8001
- Agent dependencies installed
"""

import asyncio
import time
from agent.agent import create_agent


async def demo_session_persistence():
    """Demonstrate session persistence across agent instances."""
    print("🔄 Session Persistence Demo")
    print("=" * 50)
    
    session_id = "demo-session-123"
    
    # Create first agent instance
    print(f"📝 Creating agent with session ID: {session_id}")
    agent1 = create_agent(session_id=session_id)
    
    # First conversation
    print("\n💬 First conversation:")
    response1 = agent1("Hello! My name is Alice. Please remember my name.")
    print(f"Agent: {response1}")
    
    # Simulate agent restart by creating new instance with same session
    print(f"\n🔄 Simulating agent restart - creating new agent instance with same session ID...")
    agent2 = create_agent(session_id=session_id)
    
    # Second conversation - should remember Alice
    print("\n💬 Second conversation (after 'restart'):")
    response2 = agent2("What's my name? Do you remember our previous conversation?")
    print(f"Agent: {response2}")
    
    print("\n✅ Session persistence demo completed!")


async def demo_multiple_sessions():
    """Demonstrate multiple concurrent sessions."""
    print("\n🔄 Multiple Sessions Demo")
    print("=" * 50)
    
    # Create two different sessions
    session_a = "session-alice"
    session_b = "session-bob"
    
    agent_a = create_agent(session_id=session_a)
    agent_b = create_agent(session_id=session_b)
    
    # Conversations in different sessions
    print(f"\n💬 Session A conversation:")
    response_a = agent_a("Hi, I'm Alice and I love cats.")
    print(f"Agent A: {response_a}")
    
    print(f"\n💬 Session B conversation:")
    response_b = agent_b("Hello, I'm Bob and I love dogs.")
    print(f"Agent B: {response_b}")
    
    # Cross-check - each agent should only know about their own session
    print(f"\n🔍 Cross-check - asking Agent A about Bob:")
    response_a2 = agent_a("Do you know anything about Bob or dogs?")
    print(f"Agent A: {response_a2}")
    
    print(f"\n🔍 Cross-check - asking Agent B about Alice:")
    response_b2 = agent_b("Do you know anything about Alice or cats?")
    print(f"Agent B: {response_b2}")
    
    print("\n✅ Multiple sessions demo completed!")


async def demo_conversation_continuity():
    """Demonstrate conversation continuity within a session."""
    print("\n🔄 Conversation Continuity Demo")
    print("=" * 50)
    
    session_id = "continuity-demo"
    agent = create_agent(session_id=session_id)
    
    # Multi-turn conversation
    conversations = [
        "I'm planning a trip to Japan. Can you help me?",
        "What's the best time of year to visit?",
        "What about cherry blossom season specifically?",
        "Can you summarize what we've discussed about my Japan trip?"
    ]
    
    for i, prompt in enumerate(conversations, 1):
        print(f"\n💬 Turn {i}: {prompt}")
        response = agent(prompt)
        print(f"Agent: {response}")
        time.sleep(1)  # Small delay between turns
    
    print("\n✅ Conversation continuity demo completed!")


async def main():
    """Run all session management demos."""
    print("🚀 Session Management Demo with PostgreSQL Backend")
    print("=" * 60)
    print("Make sure the session backend is running on localhost:8001")
    print("=" * 60)
    
    try:
        await demo_session_persistence()
        await demo_multiple_sessions()
        await demo_conversation_continuity()
        
        print("\n🎉 All demos completed successfully!")
        print("\nKey features demonstrated:")
        print("✅ Session persistence across agent restarts")
        print("✅ Session isolation between different users")
        print("✅ Conversation continuity within sessions")
        print("✅ PostgreSQL backend integration")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure the session backend is running: docker-compose up -d")
        print("2. Check that the backend is accessible at http://localhost:8001/health")
        print("3. Ensure all dependencies are installed: pip install -e .")


if __name__ == "__main__":
    asyncio.run(main())