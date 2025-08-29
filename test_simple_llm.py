#!/usr/bin/env python3
"""
Simple test script to check if Gemini LLM is working
"""

import asyncio
from services.llm import llm_generate, LLM_AVAILABLE

async def test_simple_llm():
    print(f"LLM Available: {LLM_AVAILABLE}")
    
    if not LLM_AVAILABLE:
        print("❌ LLM not available - check your GEMINI_API_KEY")
        return
    
    # Test with a very simple, safe prompt
    test_prompts = [
        "Hello, how are you?",
        "What is 2 + 2?",
        "Tell me about the weather in general terms.",
        "What is your name?",
    ]
    
    for prompt in test_prompts:
        print(f"\n🤖 Testing prompt: '{prompt}'")
        try:
            response = await llm_generate("gemini-1.5-flash", prompt)
            if response:
                print(f"✅ Response: {response[:100]}{'...' if len(response) > 100 else ''}")
            else:
                print("❌ No response received")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_llm())
