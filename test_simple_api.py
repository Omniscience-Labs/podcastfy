#!/usr/bin/env python3
"""
Simple API test for Podcastfy
"""

import requests
import json

def test_api():
    url = "https://podcastfy-8x6a.onrender.com/generate"
    
    # Test with minimal payload
    payload = {
        "topic": "Artificial Intelligence",
        "tts_model": "edge"
    }
    
    print("Testing API with payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Success!")
        else:
            print("❌ Failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api() 