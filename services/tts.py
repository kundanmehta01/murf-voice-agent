from typing import List, Optional

from utils.logger import logger
from config import MURF_API_KEY
from utils.user_api_keys import get_effective_api_key

TTS_AVAILABLE = False
_client = None
_client_cache = {}  # Cache for different API keys

def _get_murf_client(session_id: Optional[str] = None):
    """Get Murf client with user-provided API key if available"""
    global _client, _client_cache
    
    # Get the effective API key (user-provided or env)
    api_key = get_effective_api_key('murf', session_id)
    
    if not api_key:
        return None
    
    # Check if we have a cached client for this key
    if api_key in _client_cache:
        return _client_cache[api_key]
    
    try:
        import murf
        client = murf.Murf(api_key=api_key)
        _client_cache[api_key] = client
        logger.info(f"Created Murf client for {'user-provided' if get_effective_api_key('murf', session_id) != MURF_API_KEY else 'environment'} API key")
        return client
    except Exception as e:
        logger.warning(f"Failed to initialize Murf client with API key: {e}")
        return None

# Initialize with environment key if available
try:
    if MURF_API_KEY:
        import murf  # local import to avoid hard dependency if missing
        _client = murf.Murf(api_key=MURF_API_KEY)
        _client_cache[MURF_API_KEY] = _client
        TTS_AVAILABLE = True
    else:
        logger.warning("MURF_API_KEY not set; TTS will use user-provided keys only")
except Exception as e:
    logger.warning(f"Failed to initialize Murf client: {e}")
    TTS_AVAILABLE = False


def _extract_audio_url(result) -> Optional[str]:
    for attr in ("audio_file", "audio_url", "url"):
        if hasattr(result, attr):
            value = getattr(result, attr)
            if value:
                return str(value)
    return None


def tts_generate(text: str, voice_id: str = "en-US-natalie", fmt: str = "mp3", session_id: Optional[str] = None) -> Optional[str]:
    """Generate TTS audio using user-provided API key if available"""
    client = _get_murf_client(session_id)
    if not client:
        # Fall back to default client if available
        if not TTS_AVAILABLE or _client is None:
            logger.warning("No Murf client available for TTS generation")
            return None
        client = _client
    
    try:
        res = client.text_to_speech.generate(text=text, voice_id=voice_id, format=fmt)
        return _extract_audio_url(res)
    except Exception as e:
        logger.warning(f"TTS error: {e}")
        return None


def tts_get_voices(session_id: Optional[str] = None):
    """Get available voices using user-provided API key if available"""
    client = _get_murf_client(session_id)
    if not client:
        # Fall back to default client if available
        if not TTS_AVAILABLE or _client is None:
            logger.warning("No Murf client available for getting voices")
            return []
        client = _client
    
    try:
        return client.text_to_speech.get_voices()
    except Exception as e:
        logger.warning(f"Get voices error: {e}")
        return []


def is_tts_available(session_id: Optional[str] = None) -> bool:
    """Check if TTS is available with current configuration"""
    client = _get_murf_client(session_id)
    return client is not None or (TTS_AVAILABLE and _client is not None)

