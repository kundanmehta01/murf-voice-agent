#!/usr/bin/env python3
"""
Add diagnostic endpoints to main.py to help debug Render vs Local differences
"""

# Add these endpoints to your main.py file:

@app.get("/debug/environment")
async def debug_environment():
    """Debug endpoint to check environment variables and versions"""
    import sys
    import os
    import platform
    
    try:
        import assemblyai as aai
        aai_version = aai.__version__
    except ImportError:
        aai_version = "NOT_INSTALLED"
    
    try:
        import murf
        murf_version = murf.__version__
    except ImportError:
        murf_version = "NOT_INSTALLED"
    
    try:
        import google.generativeai as genai
        genai_version = "AVAILABLE"
    except ImportError:
        genai_version = "NOT_INSTALLED"
    
    # Get environment variables (mask sensitive parts)
    def mask_key(key):
        if key and len(key) > 8:
            return f"{key[:4]}...{key[-4:]}"
        return "NOT_SET" if not key else "SET_BUT_SHORT"
    
    return {
        "success": True,
        "environment": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.architecture(),
            "machine": platform.machine(),
            "processor": platform.processor()
        },
        "package_versions": {
            "assemblyai": aai_version,
            "murf": murf_version,
            "google_generativeai": genai_version
        },
        "api_keys_status": {
            "ASSEMBLYAI_API_KEY": mask_key(os.getenv("ASSEMBLYAI_API_KEY")),
            "MURF_API_KEY": mask_key(os.getenv("MURF_API_KEY")), 
            "GEMINI_API_KEY": mask_key(os.getenv("GEMINI_API_KEY")),
            "OPENWEATHER_API_KEY": mask_key(os.getenv("OPENWEATHER_API_KEY"))
        },
        "render_specific": {
            "PORT": os.getenv("PORT"),
            "RENDER": os.getenv("RENDER"),
            "PYTHON_VERSION": os.getenv("PYTHON_VERSION")
        }
    }


@app.get("/debug/assemblyai-test")
async def debug_assemblyai():
    """Test AssemblyAI connection from server"""
    import os
    
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    
    if not api_key:
        return {
            "success": False,
            "error": "No API key found",
            "api_key_status": "NOT_SET"
        }
    
    try:
        import assemblyai as aai
        aai.settings.api_key = api_key
        
        # Test basic connection
        transcriber = aai.Transcriber()
        
        # Try to create a RealtimeTranscriber to test streaming
        test_errors = []
        session_opened = False
        
        def on_open(session):
            nonlocal session_opened
            session_opened = True
        
        def on_error(error):
            test_errors.append(str(error))
        
        def on_data(transcript):
            pass
        
        try:
            rt = aai.RealtimeTranscriber(
                sample_rate=16000,
                on_data=on_data,
                on_error=on_error,
                on_open=on_open
            )
            
            # Try to connect
            rt.connect()
            
            # Wait a bit
            import asyncio
            await asyncio.sleep(2)
            
            # Close
            rt.close()
            
            return {
                "success": True,
                "assemblyai_version": aai.__version__,
                "api_key": f"{api_key[:4]}...{api_key[-4:]}",
                "session_opened": session_opened,
                "errors": test_errors,
                "message": "AssemblyAI test completed"
            }
            
        except Exception as streaming_error:
            return {
                "success": False,
                "assemblyai_version": aai.__version__,
                "api_key": f"{api_key[:4]}...{api_key[-4:]}",
                "streaming_error": str(streaming_error),
                "errors": test_errors,
                "message": "Streaming test failed"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "api_key": f"{api_key[:4]}...{api_key[-4:]}",
            "message": "AssemblyAI import or setup failed"
        }
