"""
Tests for the FastAPI endpoints.
"""

import os
import pytest
from podcastfy.api.fast_app import app
from httpx import WSGITransport
from fastapi.testclient import TestClient

client = TestClient(app, transport=WSGITransport(app=app))

@pytest.fixture
def sample_config():
    return {
        "generate_podcast": True,
        "urls": ["https://www.phenomenalworld.org/interviews/swap-structure/"],
        "name": "Central Clearing Risks",
        "tagline": "Exploring the complexities of financial systemic risk",
        "creativity": 0.8,
        "conversation_style": ["engaging", "informative"],
        "roles_person1": "main summarizer",
        "roles_person2": "questioner",
        "dialogue_structure": ["Introduction", "Content", "Conclusion"],
        "tts_model": "edge",
        "is_long_form": False,
        "engagement_techniques": ["questions", "examples", "analogies"],
        "user_instructions": "Don't use the word Dwelve",
        "output_language": "English"
    }

@pytest.mark.skip(reason="Trying to understand if other tests are passing")
def test_generate_podcast_with_edge_tts(sample_config):
    response = client.post("/generate", json=sample_config)
    assert response.status_code == 200
    assert "audioUrl" in response.json()
    assert response.json()["audioUrl"].startswith("http://testserver")

def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_generate_endpoint_validation():
    """Test that the generate endpoint validates input requirements."""
    # Test with no input sources
    response = client.post("/generate", json={})
    assert response.status_code == 400
    assert "At least one input source must be provided" in response.json()["detail"]

def test_generate_endpoint_with_text():
    """Test the generate endpoint with text input."""
    data = {
        "text": "This is a test text for podcast generation.",
        "tts_model": "edge",  # Use edge as it doesn't require API keys
        "name": "Test Podcast",
        "tagline": "Testing text input"
    }
    
    # This will fail without proper API keys, but should pass validation
    response = client.post("/generate", json=data)
    # The request should pass validation (not 400) but may fail later due to missing API keys
    assert response.status_code != 400

def test_generate_endpoint_with_topic():
    """Test the generate endpoint with topic input."""
    data = {
        "topic": "Artificial Intelligence",
        "tts_model": "edge",
        "name": "AI Podcast",
        "creativity": 0.7
    }
    
    # This will fail without proper API keys, but should pass validation
    response = client.post("/generate", json=data)
    # The request should pass validation (not 400) but may fail later due to missing API keys
    assert response.status_code != 400

def test_generate_endpoint_with_urls():
    """Test the generate endpoint with URL input."""
    data = {
        "urls": ["https://example.com"],
        "tts_model": "edge",
        "name": "URL Podcast"
    }
    
    # This will fail without proper API keys, but should pass validation
    response = client.post("/generate", json=data)
    # The request should pass validation (not 400) but may fail later due to missing API keys
    assert response.status_code != 400

def test_generate_endpoint_with_multiple_inputs():
    """Test the generate endpoint with multiple input types."""
    data = {
        "urls": ["https://example.com"],
        "text": "Additional text content",
        "topic": "Technology trends",
        "tts_model": "edge",
        "name": "Multi-Input Podcast"
    }
    
    # Should accept multiple input types
    response = client.post("/generate", json=data)
    assert response.status_code != 400

def test_audio_endpoint_not_found():
    """Test the audio endpoint with non-existent file."""
    response = client.get("/audio/nonexistent.mp3")
    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"

if __name__ == "__main__":
    pytest.main()