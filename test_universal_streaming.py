#!/usr/bin/env python3
"""
Test the new AssemblyAI Universal Streaming API
Based on: https://www.assemblyai.com/docs/speech-to-text/universal-streaming
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

async def test_universal_streaming():
    print("🔍 Testing AssemblyAI Universal Streaming...")
    print(f"🔑 Key: {ASSEMBLYAI_API_KEY[:8]}...{ASSEMBLYAI_API_KEY[-4:]}")
    
    try:
        import assemblyai as aai
        
        # Configure the client
        aai.settings.api_key = ASSEMBLYAI_API_KEY
        
        print("🔧 Configuring Universal Streaming...")
        
        # Create transcription config for Universal Streaming
        config = aai.TranscriptionConfig(
            model='best'  # Use the best model available 
        )
        
        # Create a RealtimeTranscriber with the Universal model
        transcriber = aai.RealtimeTranscriber(
            config=config,
            sample_rate=16000,
            on_data=lambda transcript: print(f"🎤 Received: {transcript}"),
            on_error=lambda error: print(f"❌ Error: {error}"),
            on_open=lambda session: print(f"✅ Session opened: {session}"),
            on_close=lambda code, reason: print(f"🔴 Session closed: {code} - {reason}")
        )
        
        print("🔄 Connecting...")
        transcriber.connect()
        print("✅ Connected!")
        
        # Wait to see if session opens
        await asyncio.sleep(3)
        
        print("🎵 Sending test audio...")
        # Send some test audio data
        for i in range(5):
            dummy_audio = b'\x00\x00' * 1365  # 2730 bytes
            transcriber.stream(dummy_audio)
            await asyncio.sleep(0.2)
        
        print("⏸️ Waiting...")
        await asyncio.sleep(2)
        
        print("🔄 Closing...")
        transcriber.close()
        print("✅ Test completed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_universal_streaming())
    print(f"🏁 Result: {'SUCCESS' if result else 'FAILED'}")
