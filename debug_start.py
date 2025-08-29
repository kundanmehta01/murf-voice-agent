#!/usr/bin/env python3
"""
Debug startup script to help identify why the server isn't responding
"""

import asyncio
import sys
import os
import uvicorn
from pathlib import Path

def check_environment():
    """Check the current environment setup"""
    print("🔍 ENVIRONMENT CHECK:")
    print(f"   Python version: {sys.version}")
    print(f"   Current directory: {os.getcwd()}")
    print(f"   Python path: {sys.executable}")
    
    # Check if main.py exists
    main_path = Path("main.py")
    if main_path.exists():
        print(f"   ✅ main.py found: {main_path.absolute()}")
    else:
        print(f"   ❌ main.py not found in {os.getcwd()}")
        return False
    
    return True

def check_imports():
    """Check if all required imports work"""
    print("\n📦 IMPORT CHECK:")
    
    try:
        from services.llm import LLM_AVAILABLE
        from services.tts import TTS_AVAILABLE  
        from services.stt import STT_AVAILABLE
        print(f"   ✅ Services: LLM={LLM_AVAILABLE}, TTS={TTS_AVAILABLE}, STT={STT_AVAILABLE}")
    except Exception as e:
        print(f"   ❌ Service import error: {e}")
        return False
    
    try:
        import uvicorn
        import fastapi
        print(f"   ✅ FastAPI: {fastapi.__version__}")
        print(f"   ✅ Uvicorn: {uvicorn.__version__}")
    except Exception as e:
        print(f"   ❌ Web framework import error: {e}")
        return False
    
    return True

def check_files():
    """Check if required files exist"""
    print("\n📁 FILE CHECK:")
    
    required_files = [
        "main.py",
        "config.py", 
        ".env",
        "templates/index.html",
        "static/style.css"
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (missing)")
            all_exist = False
    
    return all_exist

async def test_basic_server():
    """Test if we can start the basic FastAPI app"""
    print("\n🚀 TESTING SERVER STARTUP:")
    
    try:
        # Import the FastAPI app
        from main import app
        print("   ✅ FastAPI app imported successfully")
        
        # Create uvicorn config
        config = uvicorn.Config(
            app=app,
            host="127.0.0.1", 
            port=8000,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        print("   🌐 Starting server on http://127.0.0.1:8000")
        print("   📝 Server logs will appear below...")
        print("   ⏹️ Press Ctrl+C to stop")
        print("\n" + "="*50 + "\n")
        
        # Start the server
        await server.serve()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server startup error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main diagnostic and startup function"""
    print("🎤 VOICE AGENT DEBUG STARTUP")
    print("="*40)
    
    # Run all checks
    if not check_environment():
        print("\n❌ Environment check failed")
        return
    
    if not check_imports():
        print("\n❌ Import check failed") 
        return
    
    if not check_files():
        print("\n⚠️ Some files are missing, but proceeding...")
    
    print("\n✅ All checks passed! Starting server...\n")
    
    # Start the server with detailed logging
    await test_basic_server()

if __name__ == "__main__":
    asyncio.run(main())
