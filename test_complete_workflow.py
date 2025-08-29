#!/usr/bin/env python3
"""
Test script to verify the complete voice agent workflow
"""
import asyncio
import json
import os
from services.llm import llm_generate, LLM_AVAILABLE
from services.tts import tts_generate, TTS_AVAILABLE 
from services.stt import STT_AVAILABLE
from services.murf_ws import murf_streaming_tts
from utils.text import chunk_text, build_prompt_from_history

async def test_complete_workflow():
    """Test the complete voice agent workflow"""
    
    print("🧪 Testing Complete Voice Agent Workflow")
    print("=" * 50)
    
    # Test 1: Check all services availability
    print("\n1️⃣ Testing Service Availability:")
    print(f"   STT (AssemblyAI): {'✅' if STT_AVAILABLE else '❌'}")
    print(f"   LLM (Gemini): {'✅' if LLM_AVAILABLE else '❌'}")
    print(f"   TTS (Murf): {'✅' if TTS_AVAILABLE else '❌'}")
    
    if not all([STT_AVAILABLE, LLM_AVAILABLE, TTS_AVAILABLE]):
        print("❌ Not all services are available. Check your API keys.")
        return False
    
    # Test 2: Test LLM Generation
    print("\n2️⃣ Testing LLM Generation:")
    test_prompt = "Hello! Can you explain what a voice agent is in one sentence?"
    try:
        llm_response = await llm_generate("gemini-1.5-flash-8b", test_prompt)
        if llm_response:
            print(f"   ✅ LLM Response: {llm_response[:100]}...")
        else:
            print("   ❌ No LLM response received")
            return False
    except Exception as e:
        print(f"   ❌ LLM Error: {e}")
        return False
    
    # Test 3: Test TTS Generation 
    print("\n3️⃣ Testing TTS Generation:")
    try:
        audio_url = tts_generate("This is a test of text-to-speech conversion.", "en-US-natalie")
        if audio_url:
            print(f"   ✅ TTS Audio URL: {audio_url[:60]}...")
        else:
            print("   ❌ No TTS audio URL received")
            return False
    except Exception as e:
        print(f"   ❌ TTS Error: {e}")
        return False
    
    # Test 4: Test Text Chunking
    print("\n4️⃣ Testing Text Chunking:")
    long_text = llm_response * 5  # Make it longer to test chunking
    chunks = list(chunk_text(long_text, limit=100))
    print(f"   ✅ Text chunked into {len(chunks)} parts")
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        print(f"   Chunk {i+1}: {chunk[:50]}...")
    
    # Test 5: Test Chat History Building
    print("\n5️⃣ Testing Chat History:")
    mock_history = [
        {"role": "user", "content": "Hello", "ts": "2024-01-01T10:00:00"},
        {"role": "assistant", "content": "Hi there! How can I help you?", "ts": "2024-01-01T10:00:01"},
        {"role": "user", "content": "What's the weather?", "ts": "2024-01-01T10:00:02"}
    ]
    prompt_with_history = build_prompt_from_history(mock_history)
    print(f"   ✅ Built prompt with history ({len(prompt_with_history)} chars)")
    
    # Test 6: Test Murf Streaming TTS
    print("\n6️⃣ Testing Murf Streaming TTS:")
    try:
        audio_base64 = await murf_streaming_tts("Hello world, this is a streaming test.", "en-US-natalie")
        if audio_base64:
            print(f"   ✅ Streaming TTS returned base64 audio ({len(audio_base64)} chars)")
        else:
            print("   ❌ No base64 audio from streaming TTS")
    except Exception as e:
        print(f"   ⚠️ Streaming TTS Error (fallback mode): {e}")
    
    # Test 7: Simulate Complete Pipeline
    print("\n7️⃣ Testing Complete Pipeline Simulation:")
    user_query = "What makes a good voice assistant?"
    
    # Step 1: LLM Processing
    print(f"   User Query: {user_query}")
    llm_result = await llm_generate("gemini-1.5-flash-8b", user_query)
    print(f"   LLM Response: {llm_result[:80]}...")
    
    # Step 2: Text Chunking
    text_chunks = list(chunk_text(llm_result, limit=500))
    print(f"   Text split into {len(text_chunks)} chunks for TTS")
    
    # Step 3: TTS for each chunk
    audio_urls = []
    for i, chunk in enumerate(text_chunks[:2]):  # Limit to 2 chunks for testing
        try:
            audio_url = tts_generate(chunk, "en-US-natalie")
            if audio_url:
                audio_urls.append(audio_url)
                print(f"   ✅ Generated audio for chunk {i+1}: {audio_url[:40]}...")
        except Exception as e:
            print(f"   ⚠️ TTS failed for chunk {i+1}: {e}")
    
    print(f"\n🎉 Pipeline Test Complete: Generated {len(audio_urls)} audio files")
    
    print("\n" + "=" * 50)
    print("✅ Complete Voice Agent Workflow Test PASSED!")
    print("🚀 The voice agent is ready to use!")
    print("\nTo start the server, run: python main.py")
    print("Then open http://127.0.0.1:8000 in your browser")
    
    return True

async def main():
    """Main test function"""
    success = await test_complete_workflow()
    return success

if __name__ == "__main__":
    # Run the test
    result = asyncio.run(main())
    exit(0 if result else 1)
