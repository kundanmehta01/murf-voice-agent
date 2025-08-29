#!/usr/bin/env python3
"""
Simple test script to validate AssemblyAI API key
"""
import os
from dotenv import load_dotenv

load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

print(f"🔍 Testing AssemblyAI API Key...")
print(f"🔑 Key: {ASSEMBLYAI_API_KEY[:8]}...{ASSEMBLYAI_API_KEY[-4:]} (length: {len(ASSEMBLYAI_API_KEY)})")

try:
    import assemblyai as aai
    print("✅ AssemblyAI package imported successfully")
    
    # Set API key
    aai.settings.api_key = ASSEMBLYAI_API_KEY
    print("✅ API key set in settings")
    
    # Test with a simple transcriber creation
    transcriber = aai.Transcriber()
    print("✅ Transcriber created successfully")
    
    # Test streaming availability
    try:
        realtime_transcriber = aai.RealtimeTranscriber(
            sample_rate=16000,
            on_data=lambda x: print(f"📝 Received: {x}"),
            on_error=lambda x: print(f"❌ Error: {x}"),
        )
        print("✅ RealtimeTranscriber created successfully")
        
        # Try to connect (this is where API key validation usually happens)
        print("🔄 Testing connection...")
        realtime_transcriber.connect()
        print("✅ Connected to AssemblyAI streaming successfully!")
        
        # Close immediately
        realtime_transcriber.close()
        print("✅ Connection closed")
        
    except Exception as stream_error:
        print(f"❌ Streaming test failed: {stream_error}")
        
        # Check if it's an authentication error
        if "401" in str(stream_error) or "unauthorized" in str(stream_error).lower():
            print("❌ API KEY INVALID - This is likely the root cause of your issue!")
            print("💡 Check your AssemblyAI API key in the .env file")
        elif "403" in str(stream_error) or "forbidden" in str(stream_error).lower():
            print("❌ API KEY EXPIRED OR USAGE EXCEEDED")
        else:
            print(f"❌ Other streaming error: {stream_error}")

except ImportError as import_error:
    print(f"❌ Failed to import AssemblyAI: {import_error}")
except Exception as general_error:
    print(f"❌ General error: {general_error}")

print("🏁 Test completed")
