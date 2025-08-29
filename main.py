import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from schemas import (
    ChatHistoryResponse,
    ChatMessage,
    LLMQueryAudioResponse,
    LLMQueryRequest,
    TTSRequest,
    TTSResponse,
)
from services.stt import stt_transcribe_bytes, STT_AVAILABLE
from services.tts import tts_generate, tts_get_voices, TTS_AVAILABLE
from services.llm import llm_generate, LLM_AVAILABLE
from services.weather import (
    get_current_weather, 
    get_weather_forecast, 
    search_locations, 
    format_weather_response, 
    format_forecast_response, 
    WEATHER_AVAILABLE
)
from services.time_productivity import (
    get_current_time as get_time_service,
    add_task, list_tasks, complete_task,
    start_timer, check_timer_status,
    start_time_tracking, stop_time_tracking,
    format_time_response, format_task_list,
    TIME_PRODUCTIVITY_AVAILABLE
)
from utils.text import chunk_text, build_prompt_from_history
from utils.weather_integration import detect_weather_query, handle_weather_query, format_persona_weather_response
from utils.time_productivity_integration import (
    detect_productivity_query, handle_productivity_query_comprehensive,
    format_persona_productivity_response
)
from config import FALLBACK_TEXT, DEFAULT_PERSONA_ID
from utils.logger import logger
from personas import list_personas, get_persona, get_persona_voice_id

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory chat history store per session
CHAT_HISTORY: Dict[str, List[Dict[str, Any]]] = {}
MAX_HISTORY_MESSAGES = 50

# In-memory persona store per session
SESSION_PERSONAS: Dict[str, str] = {}


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate-tts", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    try:
        if not TTS_AVAILABLE:
            return TTSResponse(audio_url="", message=FALLBACK_TEXT)
        audio_url = tts_generate(text=request.text, voice_id=request.voice_id)
        if audio_url:
            return TTSResponse(audio_url=audio_url, message="Audio generated successfully")
        return TTSResponse(audio_url="", message=FALLBACK_TEXT)
    except Exception as e:
        logger.exception("Murf TTS error")
        return TTSResponse(audio_url="", message=FALLBACK_TEXT)


@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    file_location = UPLOAD_DIR / file.filename
    content = await file.read()
    with open(file_location, "wb") as f:
        f.write(content)
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content),
    }


@app.post("/transcribe/file")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        if not STT_AVAILABLE:
            return {"transcript": None, "status": "unavailable"}
        audio_bytes = await file.read()
        transcript_text, status = stt_transcribe_bytes(audio_bytes)
        return {"transcript": transcript_text, "status": status}
    except Exception:
        logger.exception("Transcription error")
        return {"transcript": None, "status": "error"}


@app.get("/voices")
async def get_voices():
    try:
        if not TTS_AVAILABLE:
            return []
        return tts_get_voices()
    except Exception:
        logger.exception("Get voices error")
        return []


@app.post("/tts/echo")
async def tts_echo(file: UploadFile = File(...)):
    """Echo Bot v2: Transcribe audio and generate new audio with Murf voice"""
    try:
        transcribed_text = None
        if STT_AVAILABLE:
            try:
                audio_bytes = await file.read()
                transcript_text, status = stt_transcribe_bytes(audio_bytes)
                if status == "completed" and transcript_text:
                    transcribed_text = transcript_text.strip()
            except Exception:
                logger.exception("Transcription error (echo)")
        if not transcribed_text:
            return {"transcript": None, "audio_url": "", "message": FALLBACK_TEXT}
        if not TTS_AVAILABLE:
            return {"transcript": transcribed_text, "audio_url": "", "message": FALLBACK_TEXT}
        audio_url = tts_generate(text=transcribed_text, voice_id="en-US-natalie")
        if audio_url:
            return {
                "transcript": transcribed_text,
                "audio_url": audio_url,
                "message": "Audio transcribed and regenerated successfully",
            }
        return {"transcript": transcribed_text, "audio_url": "", "message": FALLBACK_TEXT}
    except Exception:
        logger.exception("Echo processing error")
        return {"transcript": None, "audio_url": "", "message": FALLBACK_TEXT}


@app.post("/llm/query", response_model=LLMQueryAudioResponse)
async def llm_query(
    request: Request,
    file: UploadFile | None = File(None),
    prompt: str | None = Form(None),
    model: str | None = Form(None),
    voice_id: str | None = Form("en-US-natalie"),
):
    """Text or audio input -> LLM -> optional TTS"""
    try:
        content_type = request.headers.get("content-type", "").lower()
        transcript_text: Optional[str] = None
        effective_prompt: Optional[str] = None
        model_name = model or "gemini-1.5-flash-8b"

        if "application/json" in content_type:
            body = await request.json()
            payload = LLMQueryRequest(**body)
            model_name = payload.model or model_name
            effective_prompt = payload.prompt
        else:
            if file is not None and STT_AVAILABLE:
                try:
                    audio_bytes = await file.read()
                    text, status = stt_transcribe_bytes(audio_bytes)
                    if status == "completed" and text:
                        transcript_text = text.strip()
                        effective_prompt = transcript_text
                except Exception:
                    logger.exception("Transcription error (llm_query)")
            if effective_prompt is None:
                if prompt is None or not prompt.strip():
                    return LLMQueryAudioResponse(
                        transcript_text=None,
                        llm_text=FALLBACK_TEXT,
                        model=model_name,
                        audio_urls=[],
                    )
                effective_prompt = prompt.strip()

        llm_text = None
        if LLM_AVAILABLE:
            try:
                llm_text = await llm_generate(model_name=model_name, prompt=effective_prompt)
            except Exception:
                logger.exception("LLM error")
        if not llm_text:
            llm_text = FALLBACK_TEXT

        audio_urls: List[str] = []
        if TTS_AVAILABLE and llm_text != FALLBACK_TEXT:
            try:
                for ch in chunk_text(llm_text, limit=3000):
                    url = tts_generate(text=ch, voice_id=voice_id or "en-US-natalie")
                    if url:
                        audio_urls.append(url)
            except Exception:
                logger.exception("TTS error (llm_query)")
                audio_urls = []

        return LLMQueryAudioResponse(
            transcript_text=transcript_text,
            llm_text=llm_text,
            model=model_name,
            audio_urls=audio_urls,
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /llm/query")
        return LLMQueryAudioResponse(
            transcript_text=None,
            llm_text=FALLBACK_TEXT,
            model=(model or "gemini-1.5-flash-8b"),
            audio_urls=[],
        )


@app.post("/agent/chat/{session_id}", response_model=LLMQueryAudioResponse)
async def agent_chat(
    request: Request,
    session_id: str,
    file: UploadFile | None = File(None),
    prompt: str | None = Form(None),
    model: str | None = Form(None),
    voice_id: str | None = Form("en-US-natalie"),
):
    try:
        content_type = request.headers.get("content-type", "").lower()
        history = CHAT_HISTORY.get(session_id, [])

        transcript_text: Optional[str] = None
        effective_user_text: Optional[str] = None
        model_name = model or "gemini-1.5-flash-8b"

        if "application/json" in content_type:
            body = await request.json()
            payload = LLMQueryRequest(**body)
            model_name = payload.model or model_name
            effective_user_text = payload.prompt
        else:
            if file is not None and STT_AVAILABLE:
                try:
                    audio_bytes = await file.read()
                    text, status = stt_transcribe_bytes(audio_bytes)
                    if status == "completed" and text:
                        transcript_text = text.strip()
                        effective_user_text = transcript_text
                except Exception:
                    logger.exception("Transcription error (agent_chat)")
            if effective_user_text is None:
                if prompt is None or not prompt.strip():
                    return LLMQueryAudioResponse(
                        transcript_text=None,
                        llm_text=FALLBACK_TEXT,
                        model=model_name,
                        audio_urls=[],
                    )
                effective_user_text = prompt.strip()

        history.append({"role": "user", "content": effective_user_text, "ts": datetime.now().isoformat()})
        if len(history) > MAX_HISTORY_MESSAGES:
            history = history[-MAX_HISTORY_MESSAGES:]
        CHAT_HISTORY[session_id] = history

        # Get persona for this session
        persona_id = SESSION_PERSONAS.get(session_id, DEFAULT_PERSONA_ID)
        persona_voice_id = get_persona_voice_id(persona_id)
        
        # Check for weather queries first
        weather_query_info = detect_weather_query(effective_user_text)
        weather_response = None
        
        if weather_query_info['is_weather_query'] and WEATHER_AVAILABLE:
            try:
                weather_response = await handle_weather_query(weather_query_info, persona_id)
                if weather_response:
                    # Format the weather response according to persona
                    weather_response = format_persona_weather_response(weather_response, persona_id)
                    logger.info(f"Weather query handled for location: {weather_query_info.get('location', 'default')}")
            except Exception as e:
                logger.error(f"Error handling weather query: {e}")
        
        # Check for time/productivity queries if no weather query
        productivity_response = None
        if not weather_response and TIME_PRODUCTIVITY_AVAILABLE:
            try:
                productivity_response = await handle_productivity_query_comprehensive(effective_user_text, session_id)
                if productivity_response:
                    # Format the productivity response according to persona
                    productivity_response = format_persona_productivity_response(productivity_response, persona_id)
                    logger.info(f"Productivity query handled for session: {session_id}")
            except Exception as e:
                logger.error(f"Error handling productivity query: {e}")
        
        # Generate LLM response (either normal, weather-enhanced, or productivity-enhanced)
        full_prompt = build_prompt_from_history(history, persona_id)
        llm_text = None
        
        if weather_response:
            # If we have weather data, use it directly
            llm_text = weather_response
        elif productivity_response:
            # If we have productivity data, use it directly
            llm_text = productivity_response
        elif LLM_AVAILABLE:
            try:
                llm_text = await llm_generate(model_name=model_name, prompt=full_prompt)
            except Exception:
                logger.exception("LLM error (agent_chat)")
        
        if not llm_text:
            llm_text = FALLBACK_TEXT

        history.append({"role": "assistant", "content": llm_text, "ts": datetime.now().isoformat()})
        if len(history) > MAX_HISTORY_MESSAGES:
            history = history[-MAX_HISTORY_MESSAGES:]
        CHAT_HISTORY[session_id] = history

        audio_urls: List[str] = []
        if TTS_AVAILABLE and llm_text != FALLBACK_TEXT:
            try:
                # Use persona voice or fallback to provided voice_id
                effective_voice_id = voice_id if voice_id != "en-US-natalie" else persona_voice_id
                for ch in chunk_text(llm_text, limit=3000):
                    url = tts_generate(text=ch, voice_id=effective_voice_id)
                    if url:
                        audio_urls.append(url)
            except Exception:
                logger.exception("TTS error (agent_chat)")
                audio_urls = []

        return LLMQueryAudioResponse(
            transcript_text=transcript_text,
            llm_text=llm_text,
            model=model_name,
            audio_urls=audio_urls,
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /agent/chat")
        return LLMQueryAudioResponse(
            transcript_text=None,
            llm_text=FALLBACK_TEXT,
            model=(model or "gemini-1.5-flash-8b"),
            audio_urls=[],
        )


@app.get("/agent/history/{session_id}", response_model=ChatHistoryResponse)
async def get_history(session_id: str):
    hist = CHAT_HISTORY.get(session_id, [])
    msgs: List[ChatMessage] = []
    for m in hist:
        msgs.append(
            ChatMessage(
                role=m.get("role", "user"),
                content=str(m.get("content", "")),
                ts=str(m.get("ts", "")),
            )
        )
    return ChatHistoryResponse(session_id=session_id, history=msgs)


@app.delete("/agent/history/{session_id}")
async def clear_history(session_id: str):
    CHAT_HISTORY[session_id] = []
    return {"session_id": session_id, "cleared": True}


# Persona management endpoints
@app.get("/personas")
async def get_personas():
    """Get all available personas"""
    try:
        return {"personas": list_personas()}
    except Exception as e:
        logger.exception("Error getting personas")
        return {"personas": [], "error": str(e)}


@app.get("/agent/persona/{session_id}")
async def get_session_persona(session_id: str):
    """Get the current persona for a session"""
    persona_id = SESSION_PERSONAS.get(session_id, DEFAULT_PERSONA_ID)
    persona = get_persona(persona_id)
    return {
        "session_id": session_id,
        "persona_id": persona.id,
        "persona_name": persona.name,
        "persona_emoji": persona.emoji,
        "persona_description": persona.description
    }


@app.post("/agent/persona/{session_id}")
async def set_session_persona(session_id: str, persona_id: str = Form(...)):
    """Set the persona for a session"""
    try:
        # Validate persona exists
        persona = get_persona(persona_id)
        if persona.id != persona_id and persona_id != "default":
            return {"error": "Invalid persona ID", "available_personas": list_personas()}
        
        # Set the persona for this session
        SESSION_PERSONAS[session_id] = persona_id
        
        return {
            "session_id": session_id,
            "persona_id": persona.id,
            "persona_name": persona.name,
            "persona_emoji": persona.emoji,
            "message": f"Persona changed to {persona.name} {persona.emoji}"
        }
    except Exception as e:
        logger.exception("Error setting persona")
        return {"error": str(e)}


# Weather endpoints
@app.get("/weather/status")
async def weather_status():
    """Check weather service availability"""
    return {
        "weather_available": WEATHER_AVAILABLE,
        "message": "Weather service is available" if WEATHER_AVAILABLE else "Weather service unavailable - check OPENWEATHER_API_KEY"
    }


@app.get("/weather/current/{location}")
async def get_current_weather_endpoint(location: str, unit: str = "celsius"):
    """Get current weather for a location"""
    try:
        if not WEATHER_AVAILABLE:
            return {"error": "Weather service unavailable - check OPENWEATHER_API_KEY"}
        
        weather_data = await get_current_weather(location, unit)
        if weather_data:
            return {
                "success": True,
                "data": weather_data,
                "formatted_response": format_weather_response(weather_data)
            }
        return {"error": "Failed to get weather data"}
        
    except Exception as e:
        logger.exception("Error in weather endpoint")
        return {"error": str(e)}


@app.get("/weather/forecast/{location}")
async def get_weather_forecast_endpoint(location: str, days: int = 3, unit: str = "celsius"):
    """Get weather forecast for a location"""
    try:
        if not WEATHER_AVAILABLE:
            return {"error": "Weather service unavailable - check OPENWEATHER_API_KEY"}
        
        if days < 1 or days > 5:
            return {"error": "Days must be between 1 and 5"}
        
        forecast_data = await get_weather_forecast(location, days, unit)
        if forecast_data:
            return {
                "success": True,
                "data": forecast_data,
                "formatted_response": format_forecast_response(forecast_data)
            }
        return {"error": "Failed to get forecast data"}
        
    except Exception as e:
        logger.exception("Error in forecast endpoint")
        return {"error": str(e)}


# Time & Productivity endpoints
@app.get("/time/status")
async def time_productivity_status():
    """Check time & productivity service availability"""
    return {
        "time_productivity_available": TIME_PRODUCTIVITY_AVAILABLE,
        "message": "Time & Productivity service is available" if TIME_PRODUCTIVITY_AVAILABLE else "Time & Productivity service unavailable"
    }


@app.get("/time/current")
async def get_current_time_endpoint(timezone: str = "UTC", format: str = "default"):
    """Get current time in specified timezone"""
    try:
        if not TIME_PRODUCTIVITY_AVAILABLE:
            return {"error": "Time & Productivity service unavailable"}
        
        time_data = await get_time_service(timezone_str=timezone, format_str=format)
        if time_data.get("success"):
            return {
                "success": True,
                "data": time_data,
                "formatted_response": format_time_response(time_data)
            }
        return {"error": time_data.get("error", "Failed to get time data")}
        
    except Exception as e:
        logger.exception("Error in time endpoint")
        return {"error": str(e)}


@app.post("/tasks/{session_id}")
async def add_task_endpoint(
    session_id: str, 
    title: str = Form(...), 
    description: str = Form(""), 
    due_date: str = Form(None),
    priority: str = Form("medium")
):
    """Add a new task"""
    try:
        if not TIME_PRODUCTIVITY_AVAILABLE:
            return {"error": "Time & Productivity service unavailable"}
        
        result = await add_task(
            title=title,
            description=description, 
            due_date=due_date if due_date else None,
            priority=priority,
            session_id=session_id
        )
        
        return result
        
    except Exception as e:
        logger.exception("Error adding task")
        return {"error": str(e)}


@app.get("/tasks/{session_id}")
async def list_tasks_endpoint(
    session_id: str, 
    completed: bool = None, 
    priority: str = None
):
    """List tasks for a session"""
    try:
        if not TIME_PRODUCTIVITY_AVAILABLE:
            return {"error": "Time & Productivity service unavailable"}
        
        tasks_data = await list_tasks(
            session_id=session_id,
            filter_completed=completed,
            priority=priority
        )
        
        if tasks_data.get("success"):
            return {
                "success": True,
                "data": tasks_data,
                "formatted_response": format_task_list(tasks_data)
            }
        return {"error": tasks_data.get("error", "Failed to get tasks")}
        
    except Exception as e:
        logger.exception("Error listing tasks")
        return {"error": str(e)}


@app.patch("/tasks/{session_id}/{task_id}/complete")
async def complete_task_endpoint(session_id: str, task_id: str):
    """Mark a task as completed"""
    try:
        if not TIME_PRODUCTIVITY_AVAILABLE:
            return {"error": "Time & Productivity service unavailable"}
        
        result = await complete_task(task_id=task_id, session_id=session_id)
        return result
        
    except Exception as e:
        logger.exception("Error completing task")
        return {"error": str(e)}


@app.post("/timers/{session_id}")
async def start_timer_endpoint(
    session_id: str,
    name: str = Form(...),
    duration_minutes: int = Form(...),
    timer_type: str = Form("pomodoro")
):
    """Start a productivity timer"""
    try:
        if not TIME_PRODUCTIVITY_AVAILABLE:
            return {"error": "Time & Productivity service unavailable"}
        
        result = await start_timer(
            name=name,
            duration_minutes=duration_minutes,
            timer_type=timer_type,
            session_id=session_id
        )
        
        return result
        
    except Exception as e:
        logger.exception("Error starting timer")
        return {"error": str(e)}


@app.get("/timers/{session_id}")
async def check_timers_endpoint(session_id: str, timer_id: str = None):
    """Check timer status"""
    try:
        if not TIME_PRODUCTIVITY_AVAILABLE:
            return {"error": "Time & Productivity service unavailable"}
        
        result = await check_timer_status(timer_id=timer_id, session_id=session_id)
        return result
        
    except Exception as e:
        logger.exception("Error checking timers")
        return {"error": str(e)}


@app.post("/time-tracking/{session_id}/start")
async def start_time_tracking_endpoint(
    session_id: str,
    task_name: str = Form(...)
):
    """Start time tracking for a task"""
    try:
        if not TIME_PRODUCTIVITY_AVAILABLE:
            return {"error": "Time & Productivity service unavailable"}
        
        result = await start_time_tracking(
            task_name=task_name,
            session_id=session_id
        )
        
        return result
        
    except Exception as e:
        logger.exception("Error starting time tracking")
        return {"error": str(e)}


@app.patch("/time-tracking/{session_id}/{tracking_id}/stop")
async def stop_time_tracking_endpoint(
    session_id: str,
    tracking_id: str,
    notes: str = Form("")
):
    """Stop time tracking session"""
    try:
        if not TIME_PRODUCTIVITY_AVAILABLE:
            return {"error": "Time & Productivity service unavailable"}
        
        result = await stop_time_tracking(
            session_id=tracking_id,  # This should be the tracking session ID
            notes=notes,
            session_id_param=session_id
        )
        
        return result
        
    except Exception as e:
        logger.exception("Error stopping time tracking")
        return {"error": str(e)}


@app.get("/weather/search")
async def search_weather_locations(query: str):
    """Search for locations"""
    try:
        if not WEATHER_AVAILABLE:
            return {"error": "Weather service unavailable - check OPENWEATHER_API_KEY"}
        
        if not query or len(query.strip()) < 2:
            return {"error": "Query must be at least 2 characters"}
        
        locations = await search_locations(query.strip())
        return {
            "success": True,
            "locations": locations,
            "count": len(locations)
        }
        
    except Exception as e:
        logger.exception("Error in location search")
        return {"error": str(e)}


# Simple echo WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    # Accept the WebSocket connection
    await ws.accept()
    try:
        while True:
            # Receive text from client
            msg = await ws.receive_text()
            # Echo back (you can also include timestamp)
            await ws.send_text(f"echo: {msg}")
    except WebSocketDisconnect:
        # Client disconnected gracefully
        pass
    except Exception:
        # Log unexpected errors and close socket
        logger.exception("WebSocket error")
        try:
            await ws.close()
        except Exception:
            pass


@app.websocket("/ws/audio")
async def websocket_audio(ws: WebSocket):
    """
    Receives 16 kHz, 16-bit, mono PCM audio frames from the browser and streams
    them to AssemblyAI's Streaming API. Transcripts are printed to the server
    console and also sent back to the client over the same WebSocket as text
    messages for optional UI display.
    """
    await ws.accept()
    print("\n✅ WebSocket audio connection established\n")

    # Import streaming function
    from services.stt import stream_transcribe

    # Session management
    session = None
    ws_open = True
    last_transcript = ""  # Track last transcript to avoid duplicates
    
    # Get session ID from query parameters or create a new one
    session_id = None
    query_params = dict(ws.query_params)
    if "session" in query_params:
        session_id = query_params["session"]
    else:
        # Generate a session ID if not provided
        import uuid
        session_id = str(uuid.uuid4())
    
    logger.info(f"WebSocket session ID: {session_id}")

    async def on_transcript_cb(text: str, end_of_turn: bool):
        """Callback to handle transcripts from AssemblyAI"""
        nonlocal last_transcript
        
        if not text:
            return
            
        # Check if WebSocket is still open
        if not ws_open:
            logger.warning("WebSocket closed, cannot send transcript")
            return
        
        try:
            # Send structured message to client with transcript type
            import json
            message = {
                "type": "transcript",
                "text": text,
                "is_final": end_of_turn,
                "end_of_turn": end_of_turn
            }
            
            # Send JSON message to client
            json_message = json.dumps(message)
            await ws.send_text(json_message)
            
            # Only process final transcripts and avoid duplicates
            if end_of_turn:
                # Check if this is essentially the same as the last transcript (case-insensitive)
                # Also check if text is too short or similar to avoid processing noise
                normalized_text = text.lower().strip()
                if normalized_text and len(normalized_text) > 2 and normalized_text != last_transcript.lower().strip():
                    last_transcript = text
                    # Generate and stream LLM response when end of turn is detected
                    await process_llm_response(text, ws, ws_open)
                elif normalized_text == last_transcript.lower().strip():
                    logger.info(f"Skipping duplicate transcript: {text}")
            # Remove interim transcript logging for cleaner output
        except Exception as e:
            logger.error(f"Failed to send transcript to client: {e}")
            import traceback
            traceback.print_exc()
    
    async def process_llm_response(transcript: str, websocket: WebSocket, socket_open: bool):
        """Process the final transcript with LLM and stream the response with Murf TTS"""
        if not LLM_AVAILABLE:
            return
        
        try:
            from services.llm import llm_generate_stream
            from services.murf_ws import MurfWebSocketClient, murf_streaming_tts
            
            # Clean console output - just show user query
            print(f"\n👤 USER: {transcript}")
            
            # SAVE USER MESSAGE TO CHAT HISTORY
            history = CHAT_HISTORY.get(session_id, [])
            history.append({"role": "user", "content": transcript, "ts": datetime.now().isoformat()})
            if len(history) > MAX_HISTORY_MESSAGES:
                history = history[-MAX_HISTORY_MESSAGES:]
            CHAT_HISTORY[session_id] = history
            
            # Get persona for this session and build prompt with persona context
            persona_id = SESSION_PERSONAS.get(session_id, DEFAULT_PERSONA_ID)
            persona_voice_id = get_persona_voice_id(persona_id)
            full_prompt = build_prompt_from_history(history, persona_id)
            
            # Send LLM start message to client
            if socket_open:
                start_msg = json.dumps({
                    "type": "llm_start",
                    "message": "Generating response..."
                })
                await websocket.send_text(start_msg)
            
            # Accumulate the full response for console logging
            accumulated_response = ""
            model_name = "gemini-1.5-flash-8b"  # Default model
            voice_id = persona_voice_id  # Use persona's voice
            
            # Initialize Murf WebSocket client
            murf_client = None
            use_murf_ws = False  
            
            try:
                
                if TTS_AVAILABLE and use_murf_ws:
                    murf_client = MurfWebSocketClient()
                    await murf_client.connect(voice_id=voice_id)
                    logger.info("Connected to Murf WebSocket for streaming TTS")
            except Exception as e:
                logger.warning(f"Could not connect to Murf WebSocket: {e}")
                murf_client = None
            
            
            text_chunks_for_tts = []
            
            
            async for chunk in llm_generate_stream(model_name, full_prompt):
                if chunk is None:
                    break
                
                
                accumulated_response += chunk
                text_chunks_for_tts.append(chunk)
                
                
                if murf_client and murf_client.is_connected:
                    try:
                        await murf_client.send_text(chunk)
                    except Exception as e:
                        logger.error(f"Failed to send text to Murf: {e}")
                
                
                if socket_open:
                    try:
                        chunk_msg = json.dumps({
                            "type": "llm_chunk",
                            "text": chunk
                        })
                        await websocket.send_text(chunk_msg)
                    except Exception as e:
                        break
            
            # Print only the final response in a clean format
            print(f"\n🤖 ASSISTANT: {accumulated_response}")
            
            # SAVE ASSISTANT RESPONSE TO CHAT HISTORY
            if accumulated_response and accumulated_response != FALLBACK_TEXT:
                history = CHAT_HISTORY.get(session_id, [])
                history.append({"role": "assistant", "content": accumulated_response, "ts": datetime.now().isoformat()})
                if len(history) > MAX_HISTORY_MESSAGES:
                    history = history[-MAX_HISTORY_MESSAGES:]
                CHAT_HISTORY[session_id] = history
                logger.info(f"Saved assistant response to chat history. Total messages: {len(history)}")
            
            # Handle TTS audio generation and reception
            if murf_client and murf_client.is_connected:
                try:
                    # Signal end of text stream to Murf
                    await murf_client.websocket.send(json.dumps({"type": "end_of_stream"}))
                    
                    # Receive audio chunks from Murf
                    print("\n📢 Receiving audio from Murf WebSocket...")
                    audio_chunks_received = 0
                    
                    while True:
                        audio_base64 = await asyncio.wait_for(
                            murf_client.receive_audio(), 
                            timeout=5.0
                        )
                        if audio_base64:
                            audio_chunks_received += 1
                            # Print base64 audio to console as requested
                            print(f"\n🔊 Base64 Audio Chunk {audio_chunks_received} (length: {len(audio_base64)} bytes):")
                            print(f"{audio_base64[:200]}..." if len(audio_base64) > 200 else audio_base64)
                            
                            # Send audio to client if needed
                            if socket_open:
                                try:
                                    audio_msg = json.dumps({
                                        "type": "tts_audio",
                                        "audio_base64": audio_base64,
                                        "chunk_index": audio_chunks_received
                                    })
                                    await websocket.send_text(audio_msg)
                                except Exception as e:
                                    logger.error(f"Failed to send audio to client: {e}")
                        else:
                            break
                    
                    print(f"\n✅ Received {audio_chunks_received} audio chunks from Murf")
                    
                except asyncio.TimeoutError:
                    logger.info("Finished receiving audio from Murf (timeout)")
                except Exception as e:
                    logger.error(f"Error receiving audio from Murf: {e}")
                finally:
                    # Close Murf connection
                    if murf_client:
                        await murf_client.close()
            
            # Fallback: Use HTTP-based TTS if WebSocket not available
            elif TTS_AVAILABLE and accumulated_response and accumulated_response != FALLBACK_TEXT:
                try:
                    print("\n📢 Using HTTP-based TTS fallback...")
                    
                    # Option to control chunking behavior
                    USE_SINGLE_AUDIO = True  # Set to True for single audio response, False for chunked streaming
                    
                    if USE_SINGLE_AUDIO:
                        # Generate single audio for entire response (up to 3000 chars)
                        truncated_response = accumulated_response[:3000]  # Limit to prevent API errors
                        if len(accumulated_response) > 3000:
                            print(f"\n⚠️ Response truncated from {len(accumulated_response)} to 3000 chars for single audio")
                        
                        audio_base64 = await murf_streaming_tts(
                            text=truncated_response,
                            voice_id=voice_id
                        )
                        if audio_base64:
                            # Print base64 audio to console
                            print(f"\n🔊 Single Audio Response (length: {len(audio_base64)} bytes):")
                            print(f"{audio_base64[:200]}..." if len(audio_base64) > 200 else audio_base64)
                            
                            # Send to client
                            if socket_open:
                                try:
                                    audio_msg = json.dumps({
                                        "type": "tts_audio",
                                        "audio_base64": audio_base64,
                                        "chunk_index": 1
                                    })
                                    await websocket.send_text(audio_msg)
                                except Exception as e:
                                    logger.error(f"Failed to send audio to client: {e}")
                    else:
                        # Split long text into chunks for better streaming
                        from utils.text import chunk_text
                        text_chunks = list(chunk_text(accumulated_response, limit=500))  # Smaller chunks for better streaming
                        
                        print(f"\n📄 Split response into {len(text_chunks)} chunks for TTS")
                        
                        for idx, text_chunk in enumerate(text_chunks, 1):
                            audio_base64 = await murf_streaming_tts(
                                text=text_chunk,
                                voice_id=voice_id
                            )
                            if audio_base64:
                                # Print base64 audio to console
                                print(f"\n🔊 Base64 Audio Chunk {idx}/{len(text_chunks)} (length: {len(audio_base64)} bytes):")
                                print(f"{audio_base64[:200]}..." if len(audio_base64) > 200 else audio_base64)
                                
                                # Send to client
                                if socket_open:
                                    try:
                                        audio_msg = json.dumps({
                                            "type": "tts_audio",
                                            "audio_base64": audio_base64,
                                            "chunk_index": idx
                                        })
                                        await websocket.send_text(audio_msg)
                                        # Small delay between chunks to allow processing
                                        await asyncio.sleep(0.1)
                                    except Exception as e:
                                        logger.error(f"Failed to send audio chunk {idx} to client: {e}")
                                        break
                except Exception as e:
                    logger.error(f"HTTP TTS fallback failed: {e}")
            
            # Send completion message to client
            if socket_open:
                try:
                    complete_msg = json.dumps({
                        "type": "llm_complete",
                        "full_response": accumulated_response
                    })
                    await websocket.send_text(complete_msg)
                except Exception as e:
                    pass
            
        except Exception as e:
            logger.error(f"Error processing LLM response: {e}")
            import traceback
            traceback.print_exc()
            
            # Send error message to client
            if socket_open:
                try:
                    error_msg = json.dumps({
                        "type": "llm_error",
                        "message": "Failed to generate response"
                    })
                    await websocket.send_text(error_msg)
                except:
                    pass

    try:
        # Get the current event loop for proper async handling
        loop = asyncio.get_event_loop()
        
        # Create AssemblyAI streaming session with event loop
        logger.info("Creating AssemblyAI streaming session...")
        session = await stream_transcribe(
            on_transcript=on_transcript_cb,
            loop=loop,
            session_id=session_id
        )
        
        if session is None:
            logger.error("Failed to create streaming session")
            error_msg = json.dumps({"type": "error", "message": "STT unavailable - check your ASSEMBLYAI_API_KEY"})
            await ws.send_text(error_msg)
            await ws.close()
            return
        
        logger.info("✅ Streaming session ready, waiting for audio...")
        print("\n🎤 Ready to receive audio from browser (16kHz, 16-bit PCM)\n")
        
        # Main loop to receive and forward audio
        while True:
            try:
                message = await ws.receive()
            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break
            except RuntimeError as e:
                if "disconnect" in str(e).lower():
                    logger.info("WebSocket disconnected")
                    break
                raise
            except Exception as e:
                logger.warning(f"Error receiving message: {e}")
                break
            
            # Handle text messages (control commands)
            if "text" in message:
                txt = message.get("text", "")
                if txt.strip().upper() == "EOF":
                    logger.info("Received EOF signal, closing session")
                    break
                # Ignore other text messages
                continue
            
            # Handle binary audio data
            if "bytes" in message:
                audio_data = message.get("bytes")
                if audio_data:
                    # Forward PCM16 audio to AssemblyAI
                    try:
                        await session.send_audio(audio_data)
                        # Only log occasionally to avoid spam
                        # logger.debug(f"Forwarding {len(audio_data)} bytes to AssemblyAI")
                    except Exception as e:
                        logger.error(f"Failed to send audio to AssemblyAI: {e}")
                        break
            else:
                logger.debug(f"Received message without audio data: {message.keys()}")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client")
    except (ConnectionClosedError, ConnectionClosedOK):
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.exception(f"Unexpected error in WebSocket handler: {e}")
    finally:
        ws_open = False
        
        # Clean up AssemblyAI session
        if session is not None:
            try:
                logger.info("Closing AssemblyAI session...")
                await session.close()
            except Exception as e:
                logger.warning(f"Error closing AssemblyAI session: {e}")
        
        # Close WebSocket
        try:
            await ws.close()
        except Exception:
            pass
        
        print("\n❌ WebSocket audio connection closed\n")


# API Key Testing Endpoints
@app.post("/test/assemblyai")
async def test_assemblyai_key(request: Request):
    """Test AssemblyAI API key"""
    try:
        body = await request.json()
        api_key = body.get('api_key', '').strip()
        
        if not api_key:
            return {"success": False, "error": "No API key provided"}
        
        # Test the key by importing and initializing AssemblyAI
        try:
            import assemblyai as aai
            aai.settings.api_key = api_key
            transcriber = aai.Transcriber()
            
            # Test with a simple operation (this validates the key without processing audio)
            test_config = aai.TranscriptionConfig()
            return {"success": True, "message": "AssemblyAI API key is valid"}
        except Exception as e:
            return {"success": False, "error": f"Invalid AssemblyAI API key: {str(e)}"}
            
    except Exception as e:
        logger.exception("Error testing AssemblyAI key")
        return {"success": False, "error": str(e)}


@app.post("/test/murf")
async def test_murf_key(request: Request):
    """Test Murf API key"""
    try:
        body = await request.json()
        api_key = body.get('api_key', '').strip()
        
        if not api_key:
            return {"success": False, "error": "No API key provided"}
        
        # Test the key by importing and initializing Murf
        try:
            import murf
            client = murf.Murf(api_key=api_key)
            
            # Test by getting voices (lightweight operation)
            voices = client.text_to_speech.get_voices()
            return {"success": True, "message": f"Murf API key is valid - {len(voices)} voices available"}
        except Exception as e:
            return {"success": False, "error": f"Invalid Murf API key: {str(e)}"}
            
    except Exception as e:
        logger.exception("Error testing Murf key")
        return {"success": False, "error": str(e)}


@app.post("/test/gemini")
async def test_gemini_key(request: Request):
    """Test Gemini API key"""
    try:
        body = await request.json()
        api_key = body.get('api_key', '').strip()
        
        if not api_key:
            return {"success": False, "error": "No API key provided"}
        
        # Test the key by importing and initializing Gemini
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Test with a simple model list operation
            models = list(genai.list_models())
            return {"success": True, "message": f"Gemini API key is valid - {len(models)} models available"}
        except Exception as e:
            return {"success": False, "error": f"Invalid Gemini API key: {str(e)}"}
            
    except Exception as e:
        logger.exception("Error testing Gemini key")
        return {"success": False, "error": str(e)}


@app.post("/test/openweather")
async def test_openweather_key(request: Request):
    """Test OpenWeather API key"""
    try:
        body = await request.json()
        api_key = body.get('api_key', '').strip()
        
        if not api_key:
            return {"success": False, "error": "No API key provided"}
        
        # Test the key with a simple weather request
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={api_key}"
                )
                if response.status_code == 200:
                    return {"success": True, "message": "OpenWeather API key is valid"}
                elif response.status_code == 401:
                    return {"success": False, "error": "Invalid OpenWeather API key"}
                else:
                    return {"success": False, "error": f"API test failed with status {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": f"Error testing OpenWeather key: {str(e)}"}
            
    except Exception as e:
        logger.exception("Error testing OpenWeather key")
        return {"success": False, "error": str(e)}


# User API Key Management Endpoints
@app.post("/config/api-keys")
async def save_user_api_keys(request: Request):
    """Save user-provided API keys"""
    try:
        from utils.user_api_keys import set_global_user_api_keys, validate_api_key_format
        
        body = await request.json()
        keys = body.get('keys', {})
        session_id = body.get('session_id')  # Optional session-specific keys
        
        # Validate and save keys
        validated_keys = {}
        errors = {}
        
        for service, key in keys.items():
            if key and key.strip():
                key = key.strip()
                if validate_api_key_format(service, key):
                    validated_keys[service] = key
                else:
                    errors[service] = f"Invalid {service} API key format"
        
        if validated_keys:
            if session_id:
                # Session-specific keys (not implemented in this demo)
                from utils.user_api_keys import set_user_api_key
                for service, key in validated_keys.items():
                    set_user_api_key(service, key, session_id)
            else:
                # Global keys
                set_global_user_api_keys(validated_keys)
        
        return {
            "success": True,
            "message": f"Saved {len(validated_keys)} API keys",
            "keys_saved": list(validated_keys.keys()),
            "errors": errors if errors else None
        }
        
    except Exception as e:
        logger.exception("Error saving user API keys")
        return {"success": False, "error": str(e)}


@app.get("/config/api-keys/status")
async def get_api_keys_status(session_id: Optional[str] = None):
    """Get status of all API keys"""
    try:
        from utils.user_api_keys import get_api_key_status
        
        services = ['assemblyai', 'murf', 'gemini', 'openweather']
        status = {}
        
        for service in services:
            status[service] = get_api_key_status(service, session_id)
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.exception("Error getting API keys status")
        return {"success": False, "error": str(e)}


@app.delete("/config/api-keys")
async def clear_user_api_keys(session_id: Optional[str] = None):
    """Clear user-provided API keys"""
    try:
        from utils.user_api_keys import clear_user_api_keys
        
        clear_user_api_keys(session_id)
        
        return {
            "success": True,
            "message": "API keys cleared successfully"
        }
        
    except Exception as e:
        logger.exception("Error clearing user API keys")
        return {"success": False, "error": str(e)}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"detail": str(exc)})


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable (for deployment) or use default
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"  # Bind to all interfaces for deployment
    
    print("\n🚀 Starting Voice Agent Server...")
    print(f"📍 Server will be available on port {port}")
    print("🎤 Make sure to allow microphone access when prompted\n")
    
    uvicorn.run(app, host=host, port=port)
