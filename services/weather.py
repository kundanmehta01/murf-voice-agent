import asyncio
import json
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from utils.logger import logger
from config import OPENWEATHER_API_KEY

# Weather service availability
WEATHER_AVAILABLE = False

try:
    if OPENWEATHER_API_KEY:
        WEATHER_AVAILABLE = True
        logger.info("✅ Weather service configured successfully")
    else:
        logger.warning("⚠️ OPENWEATHER_API_KEY not set; Weather service disabled")
except Exception as e:
    logger.warning(f"❌ Failed to configure Weather service: {e}")
    WEATHER_AVAILABLE = False

# API Configuration
BASE_URL = "https://api.openweathermap.org/data/2.5"
GEO_URL = "https://api.openweathermap.org/geo/1.0"

# Weather condition mapping for user-friendly descriptions
WEATHER_CONDITIONS = {
    "clear sky": "☀️ Clear skies",
    "few clouds": "🌤️ Partly cloudy", 
    "scattered clouds": "⛅ Scattered clouds",
    "broken clouds": "☁️ Mostly cloudy",
    "overcast clouds": "☁️ Overcast",
    "shower rain": "🌦️ Light showers",
    "rain": "🌧️ Rainy",
    "thunderstorm": "⛈️ Thunderstorms",
    "snow": "🌨️ Snowing",
    "mist": "🌫️ Misty",
    "fog": "🌫️ Foggy",
    "drizzle": "🌦️ Drizzling"
}

def format_weather_condition(description: str) -> str:
    """Format weather condition with appropriate emoji"""
    description_lower = description.lower()
    for condition, formatted in WEATHER_CONDITIONS.items():
        if condition in description_lower:
            return formatted
    return f"🌤️ {description.title()}"

def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit"""
    return (celsius * 9/5) + 32

def format_temperature(temp_celsius: float, unit: str = "celsius") -> str:
    """Format temperature with appropriate unit"""
    if unit.lower() == "fahrenheit":
        temp_f = celsius_to_fahrenheit(temp_celsius)
        return f"{temp_f:.1f}°F"
    return f"{temp_celsius:.1f}°C"

async def geocode_location(location: str) -> Optional[Dict]:
    """Get coordinates for a location using OpenWeatherMap geocoding"""
    if not WEATHER_AVAILABLE:
        return None
    
    try:
        url = f"{GEO_URL}/direct"
        params = {
            "q": location,
            "limit": 1,
            "appid": OPENWEATHER_API_KEY
        }
        
        response = await asyncio.to_thread(requests.get, url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data:
            location_data = data[0]
            return {
                "name": location_data.get("name"),
                "country": location_data.get("country"),
                "state": location_data.get("state"),
                "lat": location_data.get("lat"),
                "lon": location_data.get("lon")
            }
        return None
        
    except Exception as e:
        logger.error(f"Geocoding error for {location}: {e}")
        return None

async def get_current_weather(location: str, unit: str = "celsius") -> Optional[Dict]:
    """Get current weather for a location"""
    if not WEATHER_AVAILABLE:
        return None
    
    try:
        # First, get coordinates for the location
        geo_data = await geocode_location(location)
        if not geo_data:
            logger.warning(f"Could not find location: {location}")
            return {"error": f"Location '{location}' not found"}
        
        # Get current weather
        url = f"{BASE_URL}/weather"
        params = {
            "lat": geo_data["lat"],
            "lon": geo_data["lon"],
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"  # Always get Celsius from API
        }
        
        response = await asyncio.to_thread(requests.get, url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract and format weather data
        main = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        wind = data.get("wind", {})
        
        current_temp = main.get("temp", 0)
        feels_like = main.get("feels_like", current_temp)
        
        weather_info = {
            "location": {
                "name": geo_data["name"],
                "country": geo_data["country"],
                "state": geo_data.get("state")
            },
            "temperature": {
                "current": format_temperature(current_temp, unit),
                "feels_like": format_temperature(feels_like, unit),
                "min": format_temperature(main.get("temp_min", current_temp), unit),
                "max": format_temperature(main.get("temp_max", current_temp), unit)
            },
            "condition": {
                "main": weather.get("main", "Unknown"),
                "description": format_weather_condition(weather.get("description", "Unknown")),
                "raw_description": weather.get("description", "Unknown")
            },
            "details": {
                "humidity": f"{main.get('humidity', 0)}%",
                "pressure": f"{main.get('pressure', 0)} hPa",
                "wind_speed": f"{wind.get('speed', 0)} m/s",
                "wind_direction": wind.get("deg", 0),
                "visibility": f"{data.get('visibility', 0) / 1000:.1f} km"
            },
            "timestamp": datetime.now().isoformat(),
            "unit": unit
        }
        
        return weather_info
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Weather API request error: {e}")
        return {"error": "Weather service temporarily unavailable"}
    except Exception as e:
        logger.error(f"Weather error: {e}")
        return {"error": "Failed to get weather information"}

async def get_weather_forecast(location: str, days: int = 3, unit: str = "celsius") -> Optional[Dict]:
    """Get weather forecast for a location"""
    if not WEATHER_AVAILABLE:
        return None
    
    try:
        # First, get coordinates for the location
        geo_data = await geocode_location(location)
        if not geo_data:
            return {"error": f"Location '{location}' not found"}
        
        # Get 5-day forecast
        url = f"{BASE_URL}/forecast"
        params = {
            "lat": geo_data["lat"],
            "lon": geo_data["lon"],
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
            "cnt": min(days * 8, 40)  # 8 forecasts per day (3-hour intervals), max 40
        }
        
        response = await asyncio.to_thread(requests.get, url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Process forecast data
        forecasts = []
        daily_forecasts = {}
        
        for item in data.get("list", []):
            dt = datetime.fromtimestamp(item["dt"])
            date_key = dt.strftime("%Y-%m-%d")
            
            forecast_item = {
                "datetime": dt.isoformat(),
                "date": dt.strftime("%A, %B %d"),
                "time": dt.strftime("%H:%M"),
                "temperature": {
                    "temp": format_temperature(item["main"]["temp"], unit),
                    "feels_like": format_temperature(item["main"]["feels_like"], unit),
                    "min": format_temperature(item["main"]["temp_min"], unit),
                    "max": format_temperature(item["main"]["temp_max"], unit)
                },
                "condition": {
                    "main": item["weather"][0]["main"],
                    "description": format_weather_condition(item["weather"][0]["description"]),
                    "raw_description": item["weather"][0]["description"]
                },
                "details": {
                    "humidity": f"{item['main']['humidity']}%",
                    "wind_speed": f"{item.get('wind', {}).get('speed', 0)} m/s",
                    "precipitation": f"{item.get('rain', {}).get('3h', 0):.1f} mm"
                }
            }
            
            forecasts.append(forecast_item)
            
            # Group by day for daily summary
            if date_key not in daily_forecasts:
                daily_forecasts[date_key] = {
                    "date": dt.strftime("%A, %B %d"),
                    "forecasts": []
                }
            daily_forecasts[date_key]["forecasts"].append(forecast_item)
        
        forecast_info = {
            "location": {
                "name": geo_data["name"],
                "country": geo_data["country"],
                "state": geo_data.get("state")
            },
            "forecasts": forecasts[:min(len(forecasts), days * 8)],
            "daily_summary": dict(list(daily_forecasts.items())[:days]),
            "timestamp": datetime.now().isoformat(),
            "unit": unit
        }
        
        return forecast_info
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Forecast API request error: {e}")
        return {"error": "Weather service temporarily unavailable"}
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        return {"error": "Failed to get weather forecast"}

async def search_locations(query: str) -> List[Dict]:
    """Search for locations matching a query"""
    if not WEATHER_AVAILABLE:
        return []
    
    try:
        url = f"{GEO_URL}/direct"
        params = {
            "q": query,
            "limit": 5,
            "appid": OPENWEATHER_API_KEY
        }
        
        response = await asyncio.to_thread(requests.get, url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        locations = []
        for item in data:
            location = {
                "name": item.get("name"),
                "country": item.get("country"),
                "state": item.get("state"),
                "lat": item.get("lat"),
                "lon": item.get("lon"),
                "display_name": f"{item.get('name')}"
            }
            
            # Add state/country info to display name
            if item.get("state"):
                location["display_name"] += f", {item.get('state')}"
            if item.get("country"):
                location["display_name"] += f", {item.get('country')}"
                
            locations.append(location)
        
        return locations
        
    except Exception as e:
        logger.error(f"Location search error: {e}")
        return []

def format_weather_response(weather_data: Dict, persona_style: str = "default") -> str:
    """Format weather data for natural language response"""
    if "error" in weather_data:
        return f"Sorry, I couldn't get the weather information: {weather_data['error']}"
    
    location = weather_data["location"]
    temp = weather_data["temperature"]
    condition = weather_data["condition"]
    details = weather_data["details"]
    
    location_name = location["name"]
    if location.get("state"):
        location_name += f", {location['state']}"
    if location.get("country") and location["country"] != "US":
        location_name += f", {location['country']}"
    
    # Base weather response
    response = f"The weather in {location_name} is currently {condition['description']} with a temperature of {temp['current']}"
    
    if temp['feels_like'] != temp['current']:
        response += f", feeling like {temp['feels_like']}"
    
    response += f". The humidity is {details['humidity']} and wind speed is {details['wind_speed']}."
    
    if temp['min'] != temp['current'] or temp['max'] != temp['current']:
        response += f" Today's range is {temp['min']} to {temp['max']}."
    
    return response

def format_forecast_response(forecast_data: Dict, persona_style: str = "default") -> str:
    """Format forecast data for natural language response"""
    if "error" in forecast_data:
        return f"Sorry, I couldn't get the forecast: {forecast_data['error']}"
    
    location = forecast_data["location"]
    daily_summary = forecast_data["daily_summary"]
    
    location_name = location["name"]
    if location.get("state"):
        location_name += f", {location['state']}"
    
    response = f"Here's the forecast for {location_name}:\n\n"
    
    for date_key, day_data in list(daily_summary.items())[:3]:  # Next 3 days
        day_forecasts = day_data["forecasts"]
        if day_forecasts:
            # Get the midday forecast (around 12-15:00) or first available
            midday_forecast = next(
                (f for f in day_forecasts if 12 <= datetime.fromisoformat(f["datetime"]).hour <= 15),
                day_forecasts[0]
            )
            
            response += f"**{day_data['date']}**: {midday_forecast['condition']['description']} "
            response += f"with highs around {midday_forecast['temperature']['max']} "
            response += f"and lows around {midday_forecast['temperature']['min']}.\n"
    
    return response.strip()
