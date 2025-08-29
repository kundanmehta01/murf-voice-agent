import asyncio
from typing import Optional

from utils.logger import logger
from config import GEMINI_API_KEY
from utils.user_api_keys import get_effective_api_key

LLM_AVAILABLE = False
_genai_cache = {}  # Cache for configured genai instances

# Map old/deprecated names to current supported ones
MODEL_ALIASES = {
    "gemini-pro": "gemini-1.5-pro",
    "gemini-1.5-flash-8b": "gemini-1.5-flash",
    "gemini-2.5-pro": "gemini-1.5-pro",
    "gemini-2.5-flash": "gemini-1.5-flash",
}

def _get_genai_client(session_id: Optional[str] = None):
    """Get configured genai client with user-provided API key if available"""
    global _genai_cache
    
    # Get the effective API key (user-provided or env)
    api_key = get_effective_api_key('gemini', session_id)
    
    if not api_key:
        return None
    
    # Check if we have a cached client for this key
    if api_key in _genai_cache:
        return _genai_cache[api_key]
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _genai_cache[api_key] = genai
        logger.info(f"Configured Gemini client for {'user-provided' if api_key != GEMINI_API_KEY else 'environment'} API key")
        return genai
    except Exception as e:
        logger.warning(f"Failed to configure Gemini client with API key: {e}")
        return None

# Initialize with environment key if available
try:
    if GEMINI_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _genai_cache[GEMINI_API_KEY] = genai
        LLM_AVAILABLE = True
        logger.info("✅ Gemini LLM configured successfully")
    else:
        logger.warning("⚠️ GEMINI_API_KEY not set; LLM will use user-provided keys only")
except Exception as e:
    logger.warning(f"❌ Failed to configure Gemini LLM: {e}")
    LLM_AVAILABLE = False


async def llm_generate(model_name: str, prompt: str, session_id: Optional[str] = None) -> Optional[str]:
    """
    Generate a single response from Gemini using user-provided API key if available.
    """
    genai_client = _get_genai_client(session_id)
    if not genai_client:
        # Fall back to default client if available
        if not LLM_AVAILABLE:
            logger.warning("No Gemini client available for LLM generation")
            return None
        import google.generativeai as genai
        genai_client = genai
    
    try:
        # Map old model names to current supported ones
        model_name = MODEL_ALIASES.get(model_name, model_name)

        llm_model = genai_client.GenerativeModel(model_name)
        result = await asyncio.to_thread(llm_model.generate_content, prompt)

        # Check for content safety issues
        if hasattr(result, 'candidates') and result.candidates:
            candidate = result.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                if candidate.finish_reason == 1:  # STOP
                    # Normal completion
                    pass
                elif candidate.finish_reason == 2:  # MAX_TOKENS
                    logger.warning("Response truncated due to max tokens")
                elif candidate.finish_reason == 3:  # SAFETY
                    logger.warning("Response blocked by safety filters")
                    return "I understand you're looking for a response, but I need to be careful about the content I generate. Could you rephrase your question?"
                elif candidate.finish_reason == 4:  # RECITATION
                    logger.warning("Response blocked due to recitation concerns")
                    return "I can't provide that specific response, but I'd be happy to help with a similar question phrased differently."
                elif candidate.finish_reason == 5:  # OTHER
                    logger.warning("Response blocked for other reasons")
                    return "I'm having trouble generating a response right now. Could you try asking in a different way?"

        # Try to get the text response
        if hasattr(result, 'text') and result.text:
            return result.text.strip()
        elif hasattr(result, 'candidates') and result.candidates:
            for candidate in result.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            return ' '.join(text_parts).strip()
        
        logger.warning("No valid text found in Gemini response")
        return "I'm having trouble generating a response right now. Please try again."
        
    except Exception as e:
        logger.warning(f"LLM error: {e}")
        return None


async def llm_generate_stream(model_name: str, prompt: str, session_id: Optional[str] = None):
    """
    Generate LLM response with streaming support using user-provided API key if available.
    Yields text chunks as they arrive from the LLM API.
    """
    genai_client = _get_genai_client(session_id)
    if not genai_client:
        # Fall back to default client if available
        if not LLM_AVAILABLE:
            logger.warning("No Gemini client available for LLM streaming")
            yield None
            return
        import google.generativeai as genai
        genai_client = genai
    
    try:
        # Map old model names to current supported ones
        model_name = MODEL_ALIASES.get(model_name, model_name)

        llm_model = genai_client.GenerativeModel(model_name)

        # Generate content with streaming enabled
        response = await asyncio.to_thread(
            llm_model.generate_content,
            prompt,
            stream=True
        )

        # Yield chunks as they arrive
        for chunk in response:
            if hasattr(chunk, "text") and chunk.text:
                yield chunk.text

    except Exception as e:
        logger.error(f"LLM streaming error: {e}")
        yield None


def is_llm_available(session_id: Optional[str] = None) -> bool:
    """Check if LLM is available with current configuration"""
    genai_client = _get_genai_client(session_id)
    return genai_client is not None or LLM_AVAILABLE
