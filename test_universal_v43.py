#!/usr/bin/env python3
"""
Test AssemblyAI v0.43.1+ Universal Streaming
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

async def test_v43_streaming():
    print("🔍 Testing AssemblyAI v0.43.1+ Universal Streaming...")
    print(f"🔑 Key: {ASSEMBLYAI_API_KEY[:8]}...{ASSEMBLYAI_API_KEY[-4:]}")
    
    try:
        import assemblyai as aai
        
        # Check the version
        print(f"📦 AssemblyAI version: {aai.__version__}")
        
        # Configure the client  
        aai.settings.api_key = ASSEMBLYAI_API_KEY
        
        session_opened = False
        transcript_received = False
        
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
        
        def on_close(code, reason):
            print(f"🔴 Session closed: {code} - {reason}")
        
        print("🔧 Creating RealtimeTranscriber...")
        
        # Create RealtimeTranscriber with v0.43.1+ syntax
        transcriber = aai.RealtimeTranscriber(
            sample_rate=16000,
            on_data=on_data,
            on_error=on_error,
            on_open=on_open,
            on_close=on_close
        )
        
        print("🔄 Connecting...")
        transcriber.connect()
        print("✅ Connected!")
        
        # Wait for session to open
        await asyncio.sleep(3)
        
        if session_opened:
            print("✅ Session successfully opened!")
        else:
            print("❌ Session did not open properly")
            
        print("🎵 Sending test audio...")
        # Send some test audio data
        for i in range(10):
            dummy_audio = b'\x00\x00' * 1365  # 2730 bytes of silence
            transcriber.stream(dummy_audio)
            await asyncio.sleep(0.1)
        
        print("⏸️ Waiting for transcripts...")
        await asyncio.sleep(3)
        
        if transcript_received:
            print("✅ Transcripts received successfully!")
        else:
            print("⚠️ No transcripts received (this might be normal with silence)")
        
        print("🔄 Closing connection...")
        transcriber.close()
        print("✅ Test completed!")
        
        return session_opened
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_v43_streaming())
    print(f"🏁 Result: {'SUCCESS' if result else 'FAILED'}")
