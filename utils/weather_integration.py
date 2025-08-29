import re
import asyncio
from typing import Dict, List, Optional, Tuple
from services.weather import (
    get_current_weather,
    get_weather_forecast,
    format_weather_response,
    format_forecast_response,
    WEATHER_AVAILABLE
)
from utils.logger import logger

# Weather-related keywords and patterns for detection
WEATHER_KEYWORDS = [
    # Current weather
    'weather', 'temperature', 'temp', 'hot', 'cold', 'sunny', 'rainy', 'cloudy',
    'humid', 'dry', 'windy', 'stormy', 'snow', 'snowing', 'rain', 'raining',
    'clear', 'overcast', 'foggy', 'misty',
    
    # Forecast
    'forecast', 'tomorrow', 'today', 'weekend', 'next week', 'this week',
    'later', 'tonight', 'morning', 'afternoon', 'evening',
    
    # Location indicators
    'in', 'at', 'for', 'near', 'around', 'outside',
    
    # Questions
    "what's", "how's", "is it", "will it", "should i", "do i need"
]

FORECAST_KEYWORDS = [
    'forecast', 'tomorrow', 'next week', 'this week', 'weekend', 
    'later', 'tonight', 'will it', 'going to', 'expect'
]

def detect_weather_query(text: str) -> Dict[str, any]:
    """
    Detect if a query is weather-related and extract relevant information
    Returns: {
        'is_weather_query': bool,
        'query_type': str,  # 'current', 'forecast', 'general'
        'location': str,    # extracted location or None
        'time_frame': str   # for forecasts
    }
    """
    text_lower = text.lower().strip()
    
    # Check for weather keywords
    weather_score = 0
    for keyword in WEATHER_KEYWORDS:
        if keyword in text_lower:
            weather_score += 1
    
    # If no weather keywords found, not a weather query
    if weather_score == 0:
        return {
            'is_weather_query': False,
            'query_type': 'none',
            'location': None,
            'time_frame': None
        }
    
    # Determine query type
    query_type = 'current'
    time_frame = None
    
    for keyword in FORECAST_KEYWORDS:
        if keyword in text_lower:
            query_type = 'forecast'
            time_frame = keyword
            break
    
    # Extract location using simple patterns
    location = extract_location(text_lower)
    
    return {
        'is_weather_query': True,
        'query_type': query_type,
        'location': location,
        'time_frame': time_frame,
        'confidence': min(weather_score / 3.0, 1.0)  # Normalize confidence score
    }

def extract_location(text: str) -> Optional[str]:
    """
    Extract location from weather query using simple pattern matching
    """
    # Common patterns for location extraction
    patterns = [
        r'(?:weather|temperature|temp|forecast)?\s*(?:in|at|for|near|around)\s+([a-zA-Z\s,]+?)(?:\s|$|\?|\.)',
        r'(?:weather|temperature|temp|forecast)?\s*(?:in|at|for|near|around)\s+([a-zA-Z\s,]+)',
        r'([a-zA-Z\s,]+?)\s+(?:weather|temperature|temp|forecast)',
        r"(?:what's|how's)\s+(?:the\s+)?(?:weather|temperature|temp).*?(?:in|at|for|near|around)\s+([a-zA-Z\s,]+?)(?:\s|$|\?|\.)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            # Clean up common words
            location = re.sub(r'\b(the|like|today|tomorrow|now|currently)\b', '', location, flags=re.IGNORECASE)
            location = location.strip(' ,')
            if len(location) > 1:
                return location
    
    return None

async def handle_weather_query(query_info: Dict, persona_id: str = "default") -> Optional[str]:
    """
    Handle a detected weather query and return formatted response
    """
    if not query_info['is_weather_query'] or not WEATHER_AVAILABLE:
        return None
    
    location = query_info['location']
    query_type = query_info['query_type']
    
    # Default to a common location if none specified
    if not location:
        location = "New York"  # You could make this configurable
    
    try:
        if query_type == 'forecast':
            # Get forecast data
            forecast_data = await get_weather_forecast(location, days=3)
            if forecast_data and 'error' not in forecast_data:
                return format_forecast_response(forecast_data, persona_id)
            elif forecast_data and 'error' in forecast_data:
                return f"Sorry, I couldn't get the forecast for {location}: {forecast_data['error']}"
        else:
            # Get current weather data
            weather_data = await get_current_weather(location)
            if weather_data and 'error' not in weather_data:
                return format_weather_response(weather_data, persona_id)
            elif weather_data and 'error' in weather_data:
                return f"Sorry, I couldn't get the weather for {location}: {weather_data['error']}"
    
    except Exception as e:
        logger.error(f"Error handling weather query: {e}")
        return f"Sorry, I encountered an error getting the weather information."
    
    return None

def format_persona_weather_response(weather_response: str, persona_id: str) -> str:
    """
    Format weather response according to persona style
    """
    if not weather_response or persona_id == "default":
        return weather_response
    
    # Persona-specific weather response formatting
    persona_styles = {
        "pirate": {
            "prefixes": ["Arr, matey!", "Shiver me timbers!", "Ahoy there!"],
            "replacements": {
                "The weather": "The weather on the seven seas",
                "temperature": "the warmth of the sun",
                "wind": "the sea breeze",
                "rain": "the ocean's tears",
                "sunny": "blessed by Neptune",
                "cloudy": "the sky be lookin' moody"
            },
            "suffixes": ["Arr!", "Set sail when ye be ready!", "Fair winds to ye!"]
        },
        "cowboy": {
            "prefixes": ["Well, partner,", "Howdy there,", "I reckon"],
            "replacements": {
                "The weather": "The weather out here in these parts",
                "temperature": "how warm it's gettin'",
                "wind": "the prairie wind",
                "sunny": "bright as a new penny",
                "hot": "hotter than a brandin' iron"
            },
            "suffixes": ["Y'all take care now!", "Happy trails!", "Giddy up!"]
        },
        "robot": {
            "prefixes": ["ANALYZING WEATHER DATA...", "WEATHER REPORT INITIATED.", "ATMOSPHERIC CONDITIONS:"],
            "replacements": {
                "The weather": "Current atmospheric conditions",
                "temperature": "thermal readings indicate",
                "humidity": "moisture levels in the atmosphere",
                "sunny": "optimal solar radiation detected"
            },
            "suffixes": ["END WEATHER REPORT.", "WEATHER DATA TRANSMISSION COMPLETE.", "SYSTEM READY."]
        },
        "wizard": {
            "prefixes": ["By my mystical powers,", "The ancient winds tell me", "Through my crystal ball I see"],
            "replacements": {
                "The weather": "The mystical forces of nature",
                "temperature": "the magical warmth",
                "wind": "the enchanted breezes",
                "rain": "the tears of sky spirits",
                "sunny": "blessed by the sun god"
            },
            "suffixes": ["May the elements be with you!", "The prophecy is complete!", "So it is written!"]
        },
        "scientist": {
            "prefixes": ["According to my meteorological analysis,", "Based on atmospheric data,", "My research indicates"],
            "replacements": {
                "The weather": "Current meteorological conditions",
                "temperature": "thermal measurements show",
                "humidity": "relative humidity levels",
                "wind": "atmospheric pressure systems"
            },
            "suffixes": ["Fascinating weather patterns!", "Science is amazing!", "Data analysis complete!"]
        }
    }
    
    if persona_id not in persona_styles:
        return weather_response
    
    style = persona_styles[persona_id]
    
    # Apply replacements
    formatted_response = weather_response
    for old, new in style["replacements"].items():
        formatted_response = formatted_response.replace(old, new)
    
    # Add prefix and suffix
    import random
    prefix = random.choice(style["prefixes"])
    suffix = random.choice(style["suffixes"])
    
    return f"{prefix} {formatted_response} {suffix}"

def enhance_prompt_with_weather_context(prompt: str, user_query: str) -> str:
    """
    Enhance the LLM prompt with weather detection context
    """
    query_info = detect_weather_query(user_query)
    
    if not query_info['is_weather_query']:
        return prompt
    
    # Add weather context to the prompt
    weather_context = f"""
    
[WEATHER QUERY DETECTED]
The user is asking about weather. You have access to real-time weather information.
Query Type: {query_info['query_type']}
Location: {query_info['location'] or 'not specified (use a default)'}
Time Frame: {query_info['time_frame'] or 'current'}

When responding to weather queries:
1. Stay in character according to your persona
2. Provide helpful and accurate weather information
3. Include relevant details like temperature, conditions, and any safety advice
4. If location is not specified, you can ask for clarification or use a default location
5. Make your weather reports engaging and personality-appropriate

Example responses by persona:
- Pirate: "Arr, matey! The seas be calm with sunny skies at 75°F in yer port!"
- Cowboy: "Well, partner, it's lookin' mighty fine out there - 72°F and clear skies!"
- Robot: "WEATHER DATA: Temperature 23°C, atmospheric conditions optimal for human activity."
- Wizard: "The mystical winds reveal fair weather - 75°F with enchanted sunshine!"
"""
    
    return prompt + weather_context
