"""
User API Key Management System

This module provides functionality to manage user-provided API keys
and prioritize them over the keys from .env files.
"""

import os
import json
from typing import Dict, Optional
from utils.logger import logger

# In-memory storage for user API keys per session
# In production, this should be stored in a database or secure cache
USER_API_KEYS: Dict[str, Dict[str, str]] = {}

# Global API keys from user configuration (not session-specific)
GLOBAL_USER_API_KEYS: Dict[str, str] = {}

def set_user_api_key(service: str, api_key: str, session_id: Optional[str] = None) -> None:
    """Set API key for a specific service and session."""
    if session_id:
        if session_id not in USER_API_KEYS:
            USER_API_KEYS[session_id] = {}
        USER_API_KEYS[session_id][service] = api_key
        logger.info(f"Set user API key for {service} in session {session_id}")
    else:
        GLOBAL_USER_API_KEYS[service] = api_key
        logger.info(f"Set global user API key for {service}")

def get_user_api_key(service: str, session_id: Optional[str] = None) -> Optional[str]:
    """Get API key for a specific service and session."""
    # First check session-specific keys
    if session_id and session_id in USER_API_KEYS:
        session_key = USER_API_KEYS[session_id].get(service)
        if session_key:
            return session_key
    
    # Then check global user keys
    global_key = GLOBAL_USER_API_KEYS.get(service)
    if global_key:
        return global_key
    
    return None

def get_effective_api_key(service: str, session_id: Optional[str] = None) -> Optional[str]:
    """
    Get the effective API key for a service, prioritizing user-provided keys over .env keys.
    
    Priority order:
    1. Session-specific user-provided key
    2. Global user-provided key  
    3. Environment variable (.env file)
    """
    from config import ASSEMBLYAI_API_KEY, MURF_API_KEY, GEMINI_API_KEY, OPENWEATHER_API_KEY
    
    # Check user-provided keys first
    user_key = get_user_api_key(service, session_id)
    if user_key:
        logger.debug(f"Using user-provided API key for {service}")
        return user_key
    
    # Fall back to environment variables
    env_keys = {
        'assemblyai': ASSEMBLYAI_API_KEY,
        'murf': MURF_API_KEY,
        'gemini': GEMINI_API_KEY,
        'openweather': OPENWEATHER_API_KEY
    }
    
    env_key = env_keys.get(service)
    if env_key:
        logger.debug(f"Using environment API key for {service}")
        return env_key
    
    logger.warning(f"No API key found for service: {service}")
    return None

def clear_user_api_keys(session_id: Optional[str] = None) -> None:
    """Clear API keys for a session or all global keys."""
    if session_id:
        if session_id in USER_API_KEYS:
            del USER_API_KEYS[session_id]
            logger.info(f"Cleared user API keys for session {session_id}")
    else:
        GLOBAL_USER_API_KEYS.clear()
        logger.info("Cleared all global user API keys")

def get_all_user_api_keys(session_id: Optional[str] = None) -> Dict[str, str]:
    """Get all API keys for a session."""
    if session_id and session_id in USER_API_KEYS:
        return USER_API_KEYS[session_id].copy()
    return GLOBAL_USER_API_KEYS.copy()

def set_global_user_api_keys(keys: Dict[str, str]) -> None:
    """Set multiple global API keys at once."""
    for service, key in keys.items():
        if key and key.strip():
            GLOBAL_USER_API_KEYS[service] = key.strip()
            logger.info(f"Set global user API key for {service}")

def validate_api_key_format(service: str, api_key: str) -> bool:
    """Basic validation of API key format."""
    if not api_key or not api_key.strip():
        return False
    
    api_key = api_key.strip()
    
    # Basic format validation
    if service == 'assemblyai':
        return len(api_key) >= 32 and api_key.isalnum()
    elif service == 'murf':
        return len(api_key) >= 30 and 'ap2_' in api_key
    elif service == 'gemini':
        return len(api_key) >= 35 and 'AIza' in api_key
    elif service == 'openweather':
        return len(api_key) >= 30 and api_key.isalnum()
    
    return True

def get_api_key_status(service: str, session_id: Optional[str] = None) -> Dict[str, any]:
    """Get status information about API key for a service."""
    effective_key = get_effective_api_key(service, session_id)
    user_key = get_user_api_key(service, session_id)
    
    if not effective_key:
        return {
            'available': False,
            'source': 'none',
            'message': f'No API key configured for {service}'
        }
    
    source = 'user' if user_key else 'environment'
    
    return {
        'available': True,
        'source': source,
        'message': f'{service.title()} API key available from {source}',
        'key_preview': f"{effective_key[:8]}...{effective_key[-4:]}" if len(effective_key) > 12 else "***"
    }

def export_user_api_keys() -> str:
    """Export user API keys to JSON string (for backup/restore)."""
    try:
        data = {
            'global_keys': GLOBAL_USER_API_KEYS,
            'session_keys': USER_API_KEYS
        }
        return json.dumps(data, indent=2)
    except Exception as e:
        logger.error(f"Failed to export user API keys: {e}")
        return "{}"

def import_user_api_keys(json_data: str) -> bool:
    """Import user API keys from JSON string."""
    try:
        data = json.loads(json_data)
        
        if 'global_keys' in data:
            GLOBAL_USER_API_KEYS.update(data['global_keys'])
        
        if 'session_keys' in data:
            USER_API_KEYS.update(data['session_keys'])
        
        logger.info("Successfully imported user API keys")
        return True
    except Exception as e:
        logger.error(f"Failed to import user API keys: {e}")
        return False
