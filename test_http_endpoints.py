#!/usr/bin/env python3
"""
Test HTTP endpoints to verify voice agent functionality
"""

import asyncio
import httpx
import json

async def test_endpoints():
    """Test the main HTTP endpoints"""
    base_url = "http://127.0.0.1:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test basic health
        try:
            print("🔍 Testing basic connectivity...")
            response = await client.get(f"{base_url}/voices")
            print(f"✅ Voices endpoint: {response.status_code}")
        except Exception as e:
            print(f"❌ Server not running: {e}")
            return
        
        # Test LLM endpoint
        try:
            print("\n🤖 Testing LLM endpoint...")
            llm_data = {
                "prompt": "Hello, how are you?",
                "model": "gemini-1.5-flash"
            }
            response = await client.post(f"{base_url}/llm/query", json=llm_data)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ LLM Response: {result.get('llm_text', 'No text')[:100]}...")
            else:
                print(f"❌ LLM Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ LLM Test Failed: {e}")
        
        # Test TTS endpoint
        try:
            print("\n🔊 Testing TTS endpoint...")
            tts_data = {
                "text": "Hello, this is a test",
                "voice_id": "en-US-natalie"
            }
            response = await client.post(f"{base_url}/generate-tts", json=tts_data)
            if response.status_code == 200:
                result = response.json()
                if result.get('audio_url'):
                    print(f"✅ TTS Response: Audio URL generated")
                else:
                    print(f"⚠️ TTS Response: {result.get('message', 'No audio URL')}")
            else:
                print(f"❌ TTS Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ TTS Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
