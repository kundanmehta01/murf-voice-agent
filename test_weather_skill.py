#!/usr/bin/env python3
"""
Test suite for Day 25 Weather Skill implementation
Tests weather service, API endpoints, and integration with agent system
"""

import asyncio
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock

# Import the modules to test
from services.weather import (
    detect_weather_condition, 
    format_temperature,
    format_weather_response,
    format_forecast_response,
    WEATHER_AVAILABLE
)
from utils.weather_integration import detect_weather_query, extract_location


class TestWeatherDetection:
    """Test weather query detection functionality"""
    
    def test_detect_weather_query_positive(self):
        """Test detection of weather queries"""
        test_cases = [
            "What's the weather like in New York?",
            "How's the temperature today?",
            "Will it rain tomorrow?",
            "Weather forecast for this weekend",
            "Is it sunny outside?",
            "Current weather in London"
        ]
        
        for query in test_cases:
            result = detect_weather_query(query)
            assert result['is_weather_query'] == True, f"Failed to detect weather query: {query}"
            assert result['confidence'] > 0, f"Confidence should be > 0 for: {query}"
    
    def test_detect_weather_query_negative(self):
        """Test non-weather queries are not detected as weather"""
        test_cases = [
            "Hello, how are you?",
            "What's 2 + 2?",
            "Tell me a joke",
            "Who is the president?",
            "Play some music",
            "Set a timer for 5 minutes"
        ]
        
        for query in test_cases:
            result = detect_weather_query(query)
            assert result['is_weather_query'] == False, f"False positive for: {query}"
    
    def test_extract_location(self):
        """Test location extraction from weather queries"""
        test_cases = [
            ("Weather in New York", "New York"),
            ("What's the temperature in London?", "London"),
            ("How's the weather for Paris today?", "Paris"),
            ("Is it raining in Seattle", "Seattle"),
            ("Temperature near Los Angeles", "Los Angeles")
        ]
        
        for query, expected_location in test_cases:
            extracted = extract_location(query.lower())
            assert extracted is not None, f"Failed to extract location from: {query}"
            assert expected_location.lower() in extracted.lower(), f"Expected {expected_location}, got {extracted}"
    
    def test_forecast_vs_current_detection(self):
        """Test detection of forecast vs current weather queries"""
        current_queries = [
            "Current weather in Boston",
            "How's the weather now?",
            "Temperature today in Miami"
        ]
        
        forecast_queries = [
            "Weather forecast for tomorrow",
            "Will it rain this weekend?",
            "Next week weather in Chicago"
        ]
        
        for query in current_queries:
            result = detect_weather_query(query)
            assert result['query_type'] == 'current', f"Should detect current weather for: {query}"
        
        for query in forecast_queries:
            result = detect_weather_query(query)
            assert result['query_type'] == 'forecast', f"Should detect forecast for: {query}"


class TestWeatherFormatting:
    """Test weather data formatting functions"""
    
    def test_format_temperature(self):
        """Test temperature formatting"""
        from services.weather import format_temperature
        
        # Test Celsius (default)
        assert format_temperature(25.0) == "25.0°C"
        assert format_temperature(0.0) == "0.0°C"
        assert format_temperature(-5.5) == "-5.5°C"
        
        # Test Fahrenheit
        assert format_temperature(25.0, "fahrenheit") == "77.0°F"
        assert format_temperature(0.0, "fahrenheit") == "32.0°F"
    
    def test_weather_condition_formatting(self):
        """Test weather condition emoji mapping"""
        from services.weather import format_weather_condition
        
        test_cases = [
            ("clear sky", "☀️ Clear skies"),
            ("few clouds", "🌤️ Partly cloudy"),
            ("rain", "🌧️ Rainy"),
            ("snow", "🌨️ Snowing"),
            ("thunderstorm", "⛈️ Thunderstorms")
        ]
        
        for input_desc, expected in test_cases:
            result = format_weather_condition(input_desc)
            assert result == expected, f"Expected {expected}, got {result}"
    
    def test_weather_response_formatting(self):
        """Test weather response formatting for natural language"""
        sample_weather_data = {
            "location": {
                "name": "New York",
                "state": "NY",
                "country": "US"
            },
            "temperature": {
                "current": "22.0°C",
                "feels_like": "24.0°C",
                "min": "18.0°C",
                "max": "25.0°C"
            },
            "condition": {
                "description": "☀️ Clear skies",
                "raw_description": "clear sky"
            },
            "details": {
                "humidity": "60%",
                "wind_speed": "3.2 m/s"
            }
        }
        
        response = format_weather_response(sample_weather_data)
        
        # Check that response contains key information
        assert "New York" in response
        assert "22.0°C" in response
        assert "Clear skies" in response or "clear sky" in response
        assert "60%" in response
        assert "3.2 m/s" in response


class TestPersonaWeatherIntegration:
    """Test persona-specific weather responses"""
    
    def test_persona_weather_formatting(self):
        """Test weather response formatting for different personas"""
        from utils.weather_integration import format_persona_weather_response
        
        base_response = "The weather in New York is currently sunny with a temperature of 75°F."
        
        # Test pirate formatting
        pirate_response = format_persona_weather_response(base_response, "pirate")
        # Should contain pirate elements (we test if it's different from base)
        assert pirate_response != base_response
        assert len(pirate_response) > len(base_response)  # Should be longer with pirate flair
        
        # Test cowboy formatting
        cowboy_response = format_persona_weather_response(base_response, "cowboy")
        assert cowboy_response != base_response
        assert cowboy_response != pirate_response  # Should be different from pirate
        
        # Test default (should be unchanged)
        default_response = format_persona_weather_response(base_response, "default")
        assert default_response == base_response


@pytest.mark.asyncio
class TestWeatherAPIIntegration:
    """Test weather API integration (mocked)"""
    
    @patch('services.weather.requests.get')
    async def test_geocode_location_success(self, mock_get):
        """Test successful location geocoding"""
        from services.weather import geocode_location
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = [{
            "name": "New York",
            "state": "NY", 
            "country": "US",
            "lat": 40.7128,
            "lon": -74.0060
        }]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test the function
        result = await geocode_location("New York")
        
        assert result is not None
        assert result["name"] == "New York"
        assert result["lat"] == 40.7128
        assert result["lon"] == -74.0060
    
    @patch('services.weather.requests.get')
    async def test_geocode_location_not_found(self, mock_get):
        """Test location geocoding when location not found"""
        from services.weather import geocode_location
        
        # Mock empty API response
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = await geocode_location("NonExistentCity")
        assert result is None


class TestEndToEndIntegration:
    """Test end-to-end weather skill integration"""
    
    def test_weather_skill_configuration(self):
        """Test that weather skill is properly configured"""
        # Test configuration import
        try:
            from config import OPENWEATHER_API_KEY
            # If we get here, the import worked (key might be None but that's ok for testing)
            assert True
        except ImportError:
            pytest.fail("OPENWEATHER_API_KEY not configured in config.py")
    
    def test_weather_service_availability_flag(self):
        """Test weather service availability detection"""
        # Test that WEATHER_AVAILABLE is properly set based on API key
        from services.weather import WEATHER_AVAILABLE
        from config import OPENWEATHER_API_KEY
        
        if OPENWEATHER_API_KEY:
            # If API key is set, service should be available
            assert WEATHER_AVAILABLE == True
        else:
            # If no API key, service should be unavailable
            assert WEATHER_AVAILABLE == False
    
    def test_main_app_weather_imports(self):
        """Test that main app imports weather components correctly"""
        try:
            from main import WEATHER_AVAILABLE
            # If we get here, the import worked
            assert True
        except ImportError:
            pytest.fail("Weather imports not properly configured in main.py")


def run_weather_tests():
    """Run all weather skill tests"""
    print("🧪 Running Day 25 Weather Skill Tests...")
    print("=" * 50)
    
    # Run synchronous tests
    test_detection = TestWeatherDetection()
    test_formatting = TestWeatherFormatting()
    test_persona = TestPersonaWeatherIntegration()
    test_integration = TestEndToEndIntegration()
    
    tests_passed = 0
    tests_total = 0
    
    # Test weather detection
    try:
        test_detection.test_detect_weather_query_positive()
        print("✅ Weather query detection (positive cases)")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Weather query detection (positive): {e}")
    tests_total += 1
    
    try:
        test_detection.test_detect_weather_query_negative()
        print("✅ Weather query detection (negative cases)")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Weather query detection (negative): {e}")
    tests_total += 1
    
    try:
        test_detection.test_extract_location()
        print("✅ Location extraction")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Location extraction: {e}")
    tests_total += 1
    
    try:
        test_detection.test_forecast_vs_current_detection()
        print("✅ Forecast vs current detection")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Forecast vs current detection: {e}")
    tests_total += 1
    
    # Test formatting
    try:
        test_formatting.test_format_temperature()
        print("✅ Temperature formatting")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Temperature formatting: {e}")
    tests_total += 1
    
    try:
        test_formatting.test_weather_condition_formatting()
        print("✅ Weather condition formatting")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Weather condition formatting: {e}")
    tests_total += 1
    
    # Test persona integration
    try:
        test_persona.test_persona_weather_formatting()
        print("✅ Persona weather formatting")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Persona weather formatting: {e}")
    tests_total += 1
    
    # Test configuration
    try:
        test_integration.test_weather_skill_configuration()
        print("✅ Weather skill configuration")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Weather skill configuration: {e}")
    tests_total += 1
    
    try:
        test_integration.test_weather_service_availability_flag()
        print("✅ Weather service availability flag")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Weather service availability: {e}")
    tests_total += 1
    
    try:
        test_integration.test_main_app_weather_imports()
        print("✅ Main app weather imports")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Main app weather imports: {e}")
    tests_total += 1
    
    print("=" * 50)
    print(f"📊 Test Results: {tests_passed}/{tests_total} passed")
    
    if tests_passed == tests_total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️ {tests_total - tests_passed} test(s) failed")
    
    return tests_passed == tests_total


if __name__ == "__main__":
    success = run_weather_tests()
    exit(0 if success else 1)
