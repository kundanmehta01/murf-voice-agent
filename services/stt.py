from typing import Optional, Tuple, Callable, Awaitable
import asyncio
from utils.logger import logger
from config import ASSEMBLYAI_API_KEY
from utils.user_api_keys import get_effective_api_key

STT_AVAILABLE = False
_transcriber = None
_transcriber_cache = {}  # Cache for different API keys

def _get_transcriber(session_id: Optional[str] = None):
    """Get AssemblyAI transcriber with user-provided API key if available"""
    global _transcriber, _transcriber_cache
    
    # Get the effective API key (user-provided or env)
    api_key = get_effective_api_key('assemblyai', session_id)
    
    if not api_key:
        return None
    
    # Check if we have a cached transcriber for this key
    if api_key in _transcriber_cache:
        return _transcriber_cache[api_key]
    
    try:
        import assemblyai as aai
        # Create a new settings context for this API key
        aai.settings.api_key = api_key
        transcriber = aai.Transcriber()
        _transcriber_cache[api_key] = transcriber
        logger.info(f"Created AssemblyAI transcriber for {'user-provided' if api_key != ASSEMBLYAI_API_KEY else 'environment'} API key")
        return transcriber
    except Exception as e:
        logger.warning(f"Failed to initialize AssemblyAI transcriber with API key: {e}")
        return None

# ---------- Non-streaming (file upload style) ----------
try:
    if ASSEMBLYAI_API_KEY:
        import assemblyai as aai
        aai.settings.api_key = ASSEMBLYAI_API_KEY
        _transcriber = aai.Transcriber()
        _transcriber_cache[ASSEMBLYAI_API_KEY] = _transcriber
        STT_AVAILABLE = True
    else:
        logger.warning("ASSEMBLYAI_API_KEY not set; STT will use user-provided keys only")
except Exception as e:
    logger.warning(f"Failed to initialize AssemblyAI transcriber: {e}")
    STT_AVAILABLE = False


def stt_transcribe_bytes(audio_bytes: bytes, session_id: Optional[str] = None) -> Tuple[Optional[str], str]:
    """Return (text, status) using non-streaming API (file upload style)."""
    transcriber = _get_transcriber(session_id)
    if not transcriber:
        # Fall back to default transcriber if available
        if not STT_AVAILABLE or _transcriber is None:
            logger.warning("No AssemblyAI transcriber available for transcription")
            return None, "unavailable"
        transcriber = _transcriber
    
    try:
        # Transcriber.transcribe is sync; run in a thread to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        transcript = loop.run_until_complete(asyncio.to_thread(transcriber.transcribe, audio_bytes)) if loop.is_running() else transcriber.transcribe(audio_bytes)
        text = getattr(transcript, "text", None)
        status = getattr(transcript, "status", "unknown")
        return text, status
    except Exception as e:
        logger.warning(f"STT error: {e}")
        return None, "error"


def is_stt_available(session_id: Optional[str] = None) -> bool:
    """Check if STT is available with current configuration"""
    transcriber = _get_transcriber(session_id)
    return transcriber is not None or (STT_AVAILABLE and _transcriber is not None)


# ---------- Streaming implementation using AssemblyAI ----------
_V3_OK = False
_STREAMING_IMPORTS = None

# Try multiple import paths for different AssemblyAI versions
try:
    # Try newer AssemblyAI SDK structure
    from assemblyai.streaming import (
        RealtimeService,
        RealtimeTranscriber,
        StreamingEvents,
        StreamingError,
    )
    _V3_OK = True
    _STREAMING_IMPORTS = 'new'
    logger.info("Using newer AssemblyAI streaming API")
except ImportError:
    try:
        # Try legacy v3 import path
        from assemblyai.streaming.v3 import (  # type: ignore
            BeginEvent,
            StreamingClient,
            StreamingClientOptions,
            StreamingParameters,
            StreamingSessionParameters,
            StreamingError,
            StreamingEvents,
            TurnEvent,
            TerminationEvent,
        )
        _V3_OK = True
        _STREAMING_IMPORTS = 'v3'
        logger.info("Using AssemblyAI v3 streaming API")
    except ImportError:
        try:
            # Try basic streaming import
            import assemblyai as aai
            if hasattr(aai, 'RealtimeTranscriber'):
                _V3_OK = True
                _STREAMING_IMPORTS = 'basic'
                logger.info("Using basic AssemblyAI streaming API")
            else:
                raise ImportError("No streaming support found")
        except Exception as e:
            logger.warning(f"All AssemblyAI streaming import attempts failed: {e}")
            _V3_OK = False
            _STREAMING_IMPORTS = None


class AssemblyAIStreamingWrapper:
    """Wrapper for AssemblyAI streaming client that handles multiple API versions"""
    def __init__(self, sample_rate=16000, on_transcript=None, loop=None, session_id=None):
        self.on_transcript_callback = on_transcript
        self.is_connected = False
        self.loop = loop or asyncio.get_event_loop()
        self.client = None
        
        # Get API key (user-provided or environment)
        api_key = get_effective_api_key('assemblyai', session_id) or ASSEMBLYAI_API_KEY
        
        if not api_key:
            raise ValueError("No AssemblyAI API key available")
        
        try:
            if _STREAMING_IMPORTS == 'v3':
                # Use v3 API
                self.client = StreamingClient(
                    StreamingClientOptions(
                        api_key=api_key,
                        api_host="streaming.assemblyai.com"
                    )
                )
                self._setup_v3_event_handlers()
                # Connect with v3 parameters
                self.client.connect(StreamingParameters(
                    sample_rate=sample_rate,
                    format_turns=True,
                    disable_partial_transcripts=False
                ))
            elif _STREAMING_IMPORTS == 'new' or _STREAMING_IMPORTS == 'basic':
                # Use newer/basic API
                import assemblyai as aai
                aai.settings.api_key = api_key
                self.client = aai.RealtimeTranscriber(
                    sample_rate=sample_rate,
                    on_data=self._on_transcript_received,
                    on_error=self._on_error_received
                )
                # Connect method may differ
                if hasattr(self.client, 'connect'):
                    self.client.connect()
                else:
                    # Newer API might auto-connect or use different method
                    pass
            else:
                raise ValueError(f"Unsupported streaming API: {_STREAMING_IMPORTS}")
            
            self.is_connected = True
            logger.info(f"AssemblyAI streaming client connected using {_STREAMING_IMPORTS} API")
            
        except Exception as e:
            logger.error(f"Failed to connect AssemblyAI streaming: {e}")
            raise
    
    def _setup_v3_event_handlers(self):
        """Set up event handlers for v3 API"""
        wrapper = self
        
        def on_begin(self_arg, event):
            logger.info(f"V3 Session started: {getattr(event, 'id', 'unknown')}")
        
        def on_turn(self_arg, event):
            if hasattr(event, 'transcript') and event.transcript:
                if wrapper.on_transcript_callback and wrapper.loop:
                    try:
                        future = asyncio.run_coroutine_threadsafe(
                            wrapper.on_transcript_callback(event.transcript, getattr(event, 'end_of_turn', False)),
                            wrapper.loop
                        )
                    except Exception as e:
                        logger.error(f"Failed to schedule transcript callback: {e}")
        
        def on_terminated(self_arg, event):
            duration = getattr(event, 'audio_duration_seconds', 0)
            logger.info(f"V3 Session terminated: {duration} seconds processed")
        
        def on_error(self_arg, error):
            logger.warning(f"V3 Streaming error: {error}")
        
        # Register handlers
        if hasattr(self.client, 'on'):
            self.client.on(StreamingEvents.Begin, on_begin)
            self.client.on(StreamingEvents.Turn, on_turn)
            self.client.on(StreamingEvents.Termination, on_terminated)
            self.client.on(StreamingEvents.Error, on_error)
    
    def _on_transcript_received(self, transcript_data):
        """Handle transcript data from newer API"""
        if self.on_transcript_callback and self.loop:
            try:
                # Extract text from transcript data
                text = None
                end_of_turn = False
                
                if hasattr(transcript_data, 'text'):
                    text = transcript_data.text
                    end_of_turn = getattr(transcript_data, 'message_type', '') == 'FinalTranscript'
                elif isinstance(transcript_data, dict):
                    text = transcript_data.get('text')
                    end_of_turn = transcript_data.get('message_type') == 'FinalTranscript'
                elif isinstance(transcript_data, str):
                    text = transcript_data
                    end_of_turn = True  # Assume final for string responses
                
                if text:
                    future = asyncio.run_coroutine_threadsafe(
                        self.on_transcript_callback(text, end_of_turn),
                        self.loop
                    )
            except Exception as e:
                logger.error(f"Failed to process transcript: {e}")
    
    def _on_error_received(self, error):
        """Handle errors from newer API"""
        logger.warning(f"Streaming error: {error}")
    
    async def send_audio(self, audio_chunk: bytes):
        """Send audio data to AssemblyAI"""
        if self.is_connected:
            try:
                # Debug: log audio chunk size
                if len(audio_chunk) > 0:
                    logger.debug(f"Streaming {len(audio_chunk)} bytes to AssemblyAI")
                self.client.stream(audio_chunk)
            except Exception as e:
                logger.warning(f"Failed to send audio: {e}")
    
    async def close(self):
        """Close the streaming session"""
        if self.is_connected:
            try:
                self.client.disconnect(terminate=True)
                self.is_connected = False
            except Exception as e:
                logger.warning(f"Error closing session: {e}")


async def stream_transcribe(
    on_transcript: Callable[[str, bool], Awaitable[None]],
    loop: Optional[asyncio.AbstractEventLoop] = None
) -> Optional[object]:
    """Create a streaming transcription session with AssemblyAI"""
    if not STT_AVAILABLE or not _V3_OK:
        logger.warning("STT not available or v3 SDK not imported")
        return None
    
    try:
        # Create wrapper with callback and event loop
        wrapper = AssemblyAIStreamingWrapper(
            sample_rate=16000,
            on_transcript=on_transcript,
            loop=loop
        )
        return wrapper
    except Exception as e:
        logger.error(f"Failed to create streaming session: {e}")
        return None

