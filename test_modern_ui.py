#!/usr/bin/env python3
"""
Simple test script to validate the modern UI functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test key endpoints to ensure functionality is preserved"""
    
    print("🧪 Testing Modern UI Endpoints...")
    
    # Test 1: Main page loads
    try:
        response = requests.get(BASE_URL)
        assert response.status_code == 200
        assert "Modern AI Voice Agent" in response.text or "AI Voice Agent" in response.text
        print("✅ Main page loads successfully")
    except Exception as e:
        print(f"❌ Main page test failed: {e}")
    
    # Test 2: Personas endpoint
    try:
        response = requests.get(f"{BASE_URL}/personas")
        assert response.status_code == 200
        data = response.json()
        assert "personas" in data
        assert isinstance(data["personas"], list)
        print(f"✅ Personas endpoint works - {len(data['personas'])} personas loaded")
    except Exception as e:
        print(f"❌ Personas test failed: {e}")
    
    # Test 3: Static CSS loads
    try:
        response = requests.get(f"{BASE_URL}/static/style_modern.css")
        assert response.status_code == 200
        assert "app-container" in response.text
        print("✅ Modern CSS stylesheet loads successfully")
    except Exception as e:
        print(f"❌ CSS test failed: {e}")
    
    # Test 4: Test API key endpoints (should work without keys)
    try:
        test_data = {"api_key": "test"}
        response = requests.post(f"{BASE_URL}/test/assemblyai", json=test_data)
        # Should return something (even if failure due to invalid key)
        assert response.status_code == 200
        print("✅ API test endpoints are accessible")
    except Exception as e:
        print(f"❌ API test failed: {e}")
    
    print("\n🎉 Modern UI validation complete!")

if __name__ == "__main__":
    test_endpoints()
