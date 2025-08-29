#!/usr/bin/env python3
"""
🎤 Complete Voice Agent - Day 23 Implementation
==================================================

This script demonstrates the complete working conversational voice agent with:
- Real-time speech transcription (AssemblyAI)
- LLM processing (Google Gemini)  
- Text-to-speech generation (Murf)
- WebSocket audio streaming
- Chat history persistence
- Complete web interface

Author: Day 23 Voice Agent Implementation
"""

import asyncio
import uvicorn
import webbrowser
import time
from services.llm import LLM_AVAILABLE
from services.tts import TTS_AVAILABLE
from services.stt import STT_AVAILABLE, _V3_OK

def show_banner():
    """Display the voice agent banner"""
    banner = """
🎤========================================================🎤
                   COMPLETE VOICE AGENT
                     Day 23 Implementation
🎤========================================================🎤

✅ FULLY INTEGRATED FEATURES:
   
   🎙️  Real-time Speech-to-Text (AssemblyAI Streaming)
   🧠 LLM Processing (Google Gemini with streaming)
   🔊 Text-to-Speech (Murf AI with audio streaming)
   💬 Chat History Persistence  
   🌐 WebSocket Audio Streaming
   📱 Modern Web Interface with VU meters
   ⚡ Auto-streaming conversations
   
🎤========================================================🎤

🚀 COMPLETE WORKFLOW:
   1. User speaks into microphone
   2. Audio is streamed to AssemblyAI via WebSocket
   3. Real-time transcription with turn detection
   4. Transcript sent to Gemini LLM for processing
   5. LLM response streamed in real-time
   6. Response converted to speech via Murf
   7. Audio streamed back to client
   8. Chat history automatically saved

🎤========================================================🎤
    """
    print(banner)

def check_services():
    """Check service availability"""
    print("🔍 CHECKING SERVICES:")
    print(f"   STT (AssemblyAI): {'✅ Ready' if STT_AVAILABLE else '❌ Not Available'}")
    print(f"   STT Streaming: {'✅ Ready' if _V3_OK else '❌ Not Available'}")
    print(f"   LLM (Gemini): {'✅ Ready' if LLM_AVAILABLE else '❌ Not Available'}")
    print(f"   TTS (Murf): {'✅ Ready' if TTS_AVAILABLE else '❌ Not Available'}")
    
    if not all([STT_AVAILABLE, LLM_AVAILABLE, TTS_AVAILABLE, _V3_OK]):
        print("\n❌ SETUP ISSUE: Some services are not available.")
        print("   Please check your API keys in the .env file.")
        return False
    
    print("\n✅ ALL SERVICES READY!")
    return True

def show_features():
    """Show key features"""
    features = """
📋 KEY FEATURES IMPLEMENTED:

🎙️ SPEECH INPUT:
   - Real-time microphone capture
   - 16kHz PCM audio streaming
   - WebSocket connection to AssemblyAI
   - Turn detection and end-of-speech recognition

🧠 AI PROCESSING:
   - Google Gemini LLM integration
   - Streaming responses for real-time feel
   - Context-aware conversation handling
   - Chat history integration

🔊 VOICE OUTPUT:
   - Murf AI text-to-speech
   - High-quality voice synthesis
   - Audio streaming for immediate playback
   - Base64 audio streaming support

💬 CONVERSATION FEATURES:
   - Session-based chat history
   - Persistent conversation memory
   - Real-time transcript display
   - Turn-based conversation flow

🌐 WEB INTERFACE:
   - Modern responsive design
   - VU meter visualization
   - Real-time status updates
   - Auto-stream mode for hands-free operation

⚡ TECHNICAL HIGHLIGHTS:
   - WebSocket-based audio streaming
   - Async/await throughout
   - Error handling and fallbacks
   - Production-ready FastAPI backend
    """
    print(features)

def show_usage():
    """Show usage instructions"""
    usage = """
🎯 HOW TO USE:

1. 📱 Open http://127.0.0.1:8000 in your browser
2. 🎤 Allow microphone access when prompted
3. 🟢 Click "Start Talking" to begin recording
4. 🗣️ Speak your question or message
5. ⏸️ Click "Listening... Tap to stop" to end recording
6. ⚙️ The agent will:
   - Transcribe your speech in real-time
   - Process with AI (Gemini)
   - Convert response to speech (Murf)
   - Stream audio back to you
7. 💬 Chat history is automatically saved
8. ⚡ Enable "Auto-Stream" for hands-free conversation

🔧 ADVANCED FEATURES:
   - Real-time transcription with interim results
   - Turn detection for natural conversation
   - Audio chunk streaming for immediate playback
   - Session persistence across browser refreshes
   - Error handling with graceful fallbacks
    """
    print(usage)

async def main():
    """Main startup function"""
    show_banner()
    
    if not check_services():
        print("\n❌ Cannot start - services not ready")
        return
    
    show_features()
    show_usage()
    
    print("\n🚀 STARTING VOICE AGENT SERVER...")
    print("📍 Server will be available at: http://127.0.0.1:8000")
    print("🎤 Make sure to allow microphone access!")
    print("⏹️ Press Ctrl+C to stop the server\n")
    
    # Small delay to let user read
    await asyncio.sleep(2)
    
    # Try to open browser automatically
    try:
        print("🌐 Opening browser automatically...")
        webbrowser.open("http://127.0.0.1:8000")
    except:
        print("⚠️ Could not auto-open browser. Please manually open http://127.0.0.1:8000")
    
    # Start the server
    try:
        config = uvicorn.Config(
            "main:app",
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
