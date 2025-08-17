"""
Podcastfy Operator Integration
=============================

This module provides integration between Podcastfy and Operator,
allowing Podcastfy to be used both as a standalone tool and as a tool within Operator.
"""

import requests
import json
from typing import Optional, List, Dict, Any
import os
from dataclasses import dataclass


@dataclass
class PodcastResult:
    """Result from podcast generation"""
    success: bool
    audio_url: Optional[str] = None
    transcript_url: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


class PodcastfyOperatorTool:
    """
    Podcastfy tool for Operator integration
    
    This class provides a clean interface for using Podcastfy within Operator
    while also supporting standalone usage.
    """
    
    def __init__(self, base_url: str = "https://varnica-dev-podcastfy.onrender.com"):
        """
        Initialize the Podcastfy tool
        
        Args:
            base_url: Base URL for the Podcastfy API
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Use FastAPI endpoints by default, Flask only for localhost
        self.is_flask = "localhost" in base_url or "127.0.0.1" in base_url
        self.health_endpoint = "/api/health" if self.is_flask else "/health"
        self.generate_endpoint = "/api/generate" if self.is_flask else "/generate"
        
    def generate_podcast(
        self,
        urls: Optional[List[str]] = None,
        text: Optional[str] = None,
        topic: Optional[str] = None,
        tts_model: str = "edge",
        conversation_style: str = "casual",
        longform: bool = False,
        **kwargs
    ) -> PodcastResult:
        """
        Generate a podcast from various content sources
        
        Args:
            urls: List of URLs to extract content from
            text: Direct text content to convert to podcast
            topic: Topic to generate podcast content about
            tts_model: TTS model to use (edge, openai, elevenlabs, gemini)
            conversation_style: Style of conversation (casual, formal, educational, interview)
            longform: Whether to generate long-form content
            **kwargs: Additional parameters
            
        Returns:
            PodcastResult: Result of the podcast generation
        """
        
        # Validate input
        if not any([urls, text, topic]):
            return PodcastResult(
                success=False,
                error="At least one content source (urls, text, or topic) must be provided"
            )
        
        # Prepare request payload
        payload = {
            "tts_model": tts_model,
            "conversation_style": conversation_style,
            "longform": longform,
            **kwargs
        }
        
        if urls:
            payload["urls"] = urls
        if text:
            payload["text"] = text
        if topic:
            payload["topic"] = topic
            
        try:
            if self.is_flask:
                # Flask backend expects form data
                form_data = {
                    'data': json.dumps(payload)
                }
                response = self.session.post(
                    f"{self.base_url}{self.generate_endpoint}",
                    data=form_data,
                    timeout=300
                )
            else:
                # FastAPI backend expects JSON
                response = self.session.post(
                    f"{self.base_url}{self.generate_endpoint}",
                    json=payload,
                    timeout=300
                )
            
            if response.status_code == 200:
                data = response.json()
                return PodcastResult(
                    success=data.get("success", False),
                    audio_url=data.get("audio_url"),
                    transcript_url=data.get("transcript_url"),
                    message=data.get("message")
                )
            else:
                return PodcastResult(
                    success=False,
                    error=f"API request failed with status {response.status_code}: {response.text}"
                )
                
        except requests.exceptions.Timeout:
            return PodcastResult(
                success=False,
                error="Request timed out. Podcast generation may take longer than expected."
            )
        except requests.exceptions.RequestException as e:
            return PodcastResult(
                success=False,
                error=f"Request failed: {str(e)}"
            )
        except Exception as e:
            return PodcastResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Podcastfy service
        
        Returns:
            Dict containing health status
        """
        try:
            # FastAPI version uses /health instead of /api/health
            response = self.session.get(f"{self.base_url}{self.health_endpoint}", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "unhealthy", "error": f"Status code: {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Operator Tool Interface
class OperatorPodcastfyTool:
    """
    Operator-specific interface for Podcastfy
    
    This class provides the interface that Operator expects for tool integration.
    """
    
    def __init__(self):
        self.tool = PodcastfyOperatorTool()
        self.name = "podcastfy"
        self.description = "Generate AI-powered podcasts from various content sources"
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the podcast generation tool
        
        This is the main entry point that Operator will call.
        
        Returns:
            Dict containing the result of the operation
        """
        result = self.tool.generate_podcast(**kwargs)
        
        return {
            "success": result.success,
            "data": {
                "audio_url": result.audio_url,
                "transcript_url": result.transcript_url,
                "message": result.message
            } if result.success else None,
            "error": result.error
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the tool schema for Operator
        
        Returns:
            Dict containing the tool schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of URLs to extract content from"
                    },
                    "text": {
                        "type": "string",
                        "description": "Direct text content to convert to podcast"
                    },
                    "topic": {
                        "type": "string",
                        "description": "Topic to generate podcast content about"
                    },
                    "tts_model": {
                        "type": "string",
                        "enum": ["edge", "openai", "elevenlabs", "gemini"],
                        "default": "edge",
                        "description": "Text-to-speech model to use"
                    },
                    "conversation_style": {
                        "type": "string",
                        "enum": ["casual", "formal", "educational", "interview"],
                        "default": "casual",
                        "description": "Style of the podcast conversation"
                    },
                    "longform": {
                        "type": "boolean",
                        "default": False,
                        "description": "Generate long-form content"
                    }
                }
            }
        }


# Standalone usage example
def main():
    """
    Example of standalone usage
    """
    tool = PodcastfyOperatorTool()
    
    # Test health check
    health = tool.health_check()
    print(f"Health check: {health}")
    
    # Generate a podcast from a topic
    result = tool.generate_podcast(
        topic="The Future of AI in Software Development",
        tts_model="edge",
        conversation_style="educational"
    )
    
    if result.success:
        print(f"✅ Podcast generated successfully!")
        print(f"🎵 Audio URL: {result.audio_url}")
        print(f"📝 Transcript URL: {result.transcript_url}")
        print(f"💬 Message: {result.message}")
    else:
        print(f"❌ Failed to generate podcast: {result.error}")


if __name__ == "__main__":
    main() 