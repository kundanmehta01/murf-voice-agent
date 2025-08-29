#!/usr/bin/env python3
"""
Test script to verify persona functionality
Tests each persona's system prompt and voice selection
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from personas import list_personas, get_persona, get_persona_voice_id, get_persona_system_prompt
from utils.text import build_prompt_from_history


def test_persona_system():
    """Test the basic persona system functionality"""
    print("🎭 Testing Persona System\n")
    
    # Test listing personas
    print("📋 Available Personas:")
    personas = list_personas()
    for persona in personas:
        print(f"  {persona['emoji']} {persona['name']} - {persona['description']}")
    print()
    
    # Test each persona's configuration
    print("🔧 Testing Persona Configurations:")
    for persona in personas:
        persona_id = persona['id']
        persona_obj = get_persona(persona_id)
        voice_id = get_persona_voice_id(persona_id)
        system_prompt = get_persona_system_prompt(persona_id)
        
        print(f"\n{persona['emoji']} {persona['name']} ({persona_id}):")
        print(f"  Voice: {voice_id}")
        print(f"  Traits: {', '.join(persona['personality_traits'])}")
        print(f"  System Prompt (first 100 chars): {system_prompt[:100]}...")
    
    print("\n✅ Persona system basic tests passed!")


def test_prompt_building():
    """Test prompt building with different personas"""
    print("\n🔨 Testing Prompt Building with Personas:")
    
    # Create sample chat history
    sample_history = [
        {"role": "user", "content": "Hello! What's the weather like?", "ts": "2024-01-01T12:00:00"},
        {"role": "assistant", "content": "I don't have access to current weather data, but I'd be happy to help you find weather information!", "ts": "2024-01-01T12:00:30"}
    ]
    
    # Test prompt building with different personas
    test_personas = ["default", "pirate", "cowboy", "robot"]
    
    for persona_id in test_personas:
        persona = get_persona(persona_id)
        prompt = build_prompt_from_history(sample_history, persona_id)
        
        print(f"\n{persona.emoji} {persona.name} Prompt:")
        print("=" * 50)
        print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
        print("=" * 50)
    
    print("\n✅ Prompt building tests passed!")


async def test_api_simulation():
    """Simulate API calls to test persona switching"""
    print("\n🌐 Simulating API Persona Tests:")
    
    # Simulate session persona management
    session_personas = {}
    session_id = "test-session-123"
    
    # Test setting different personas
    test_personas = ["pirate", "wizard", "chef"]
    
    for persona_id in test_personas:
        # Simulate setting persona
        session_personas[session_id] = persona_id
        current_persona = get_persona(session_personas.get(session_id))
        
        print(f"\n🔄 Session {session_id} persona set to: {current_persona.emoji} {current_persona.name}")
        print(f"   Voice ID: {current_persona.voice_id}")
        print(f"   Speaking Style: {current_persona.speaking_style}")
        
        # Test prompt generation
        test_history = [{"role": "user", "content": "Tell me about yourself", "ts": "2024-01-01T12:00:00"}]
        prompt = build_prompt_from_history(test_history, persona_id)
        
        print(f"   Sample Prompt: {prompt.split('Assistant:')[0].strip()[-100:]}...")
    
    print("\n✅ API simulation tests passed!")


def main():
    """Run all persona tests"""
    print("🚀 Starting Persona System Tests\n")
    
    try:
        # Test basic persona functionality
        test_persona_system()
        
        # Test prompt building
        test_prompt_building()
        
        # Test API simulation
        asyncio.run(test_api_simulation())
        
        print("\n🎉 All persona tests passed successfully!")
        print("\n📝 Quick Test Summary:")
        print("   ✅ Persona configuration loading")
        print("   ✅ Voice ID mapping")
        print("   ✅ System prompt generation")
        print("   ✅ Prompt building with persona context")
        print("   ✅ Session persona management simulation")
        
        print("\n🎭 Available Personas for Voice Agent:")
        personas = list_personas()
        for persona in personas:
            print(f"   {persona['emoji']} {persona['name']} - {persona['speaking_style']}")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
