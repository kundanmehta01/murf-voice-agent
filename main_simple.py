"""
Simplified version of the voice agent for deployment testing
This version has minimal dependencies to ensure deployment succeeds
"""

import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Murf Voice Agent", description="AI Voice Agent with minimal dependencies")

@app.get("/")
async def root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Murf Voice Agent - Deployment Test</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin: 50px; }
            .container { max-width: 600px; margin: 0 auto; }
            .status { color: green; font-size: 24px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 Murf Voice Agent</h1>
            <div class="status">✅ Server is running successfully!</div>
            <p>This is a simplified version for deployment testing.</p>
            <p>Once deployment is confirmed working, we'll add back all the voice features.</p>
            <hr>
            <h3>Environment Info</h3>
            <p><strong>Python Version:</strong> Available in logs</p>
            <p><strong>Port:</strong> {port}</p>
        </div>
    </body>
    </html>
    """.format(port=os.getenv("PORT", "8000")))

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Server is running"}

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🚀 Starting simplified voice agent on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
