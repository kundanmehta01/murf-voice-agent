#!/usr/bin/env python3
"""
Simple AssemblyAI streaming test to verify the connection
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

async def test_streaming():
    print("🔍 Testing AssemblyAI Streaming...")
    print(f"🔑 Key: {ASSEMBLYAI_API_KEY[:8]}...{ASSEMBLYAI_API_KEY[-4:]}")
    
    try:
        import assemblyai as aai
        aai.settings.api_key = ASSEMBLYAI_API_KEY
        
        transcript_received = False
        session_opened = False
        
        def on_open(session_opened_event):
            nonlocal session_opened
            session_opened = True
            print(f"✅ Session opened: {session_opened_event}")
        
        def on_data(transcript):
            nonlocal transcript_received
            transcript_received = True
            print(f"🎤 Transcript received: {transcript}")
            
        def on_error(error):
            print(f"❌ Error: {error}")
        
        # Create transcriber with minimal config
        transcriber = aai.RealtimeTranscriber(
            on_data=on_data,
            on_error=on_error,
            on_open=on_open,
            sample_rate=16000
        )
        
        print("🔄 Connecting...")
        transcriber.connect()
        print("✅ Connected!")
        
        # Give it a moment to establish connection
        await asyncio.sleep(2)
        
        if session_opened:
            print("✅ Session successfully opened")
        else:
            print("❌ Session did not open")
        
        print("🎵 Sending test audio data...")
        
        # Send some dummy audio data (silence)
        for i in range(10):
            dummy_audio = b'\x00\x00' * 1365  # 2730 bytes of silence (same as your logs)
            transcriber.stream(dummy_audio)
            await asyncio.sleep(0.1)
        
        print("⏸️ Waiting for transcripts...")
        await asyncio.sleep(3)
        
        if transcript_received:
            print("✅ Transcript received successfully!")
        else:
            print("❌ No transcripts received (this might be normal with silence)")
        
        print("🔄 Closing connection...")
        transcriber.close()
        print("✅ Test completed")
        
        return session_opened
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_streaming())
    print(f"🏁 Test result: {'PASSED' if result else 'FAILED'}")
