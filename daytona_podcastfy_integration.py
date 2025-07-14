#!/usr/bin/env python3
"""
Daytona + Podcastfy Integration with Full Content Support

This module provides complete integration between Daytona sandbox and Podcastfy
for generating podcasts from real content sources: YouTube, PDFs, websites, etc.
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlparse

# Add podcastfy to path
sys.path.insert(0, str(Path(__file__).parent / "podcastfy"))

from podcastfy.sandbox_integration import PodcastfyTool, SANDBOX_TOOL_REGISTRY
from podcastfy.schema import PodcastfyInput, VoiceConfig, ConversationConfig, AIConfig, TTSModel, LLMModel, ContentSource

logger = logging.getLogger(__name__)


class DaytonaPodcastfyIntegration:
    """
    Main integration class for Daytona + Podcastfy with full content support.
    
    This class provides methods to generate podcasts from:
    - YouTube videos
    - PDF documents  
    - Website articles
    - Direct text
    - AI-generated topics
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Daytona integration."""
        self.podcastfy_tool = PodcastfyTool(config_path)
        self.content_extractor = self._init_content_extractor()
        
    def _init_content_extractor(self):
        """Initialize content extractor for various sources."""
        try:
            from podcastfy.content_parser.content_extractor import ContentExtractor
            return ContentExtractor()
        except ImportError:
            logger.warning("ContentExtractor not available, using basic extraction")
            return None
    
    def detect_content_type(self, source: str) -> ContentSource:
        """Detect the type of content source."""
        if self._is_youtube_url(source):
            return ContentSource.URL
        elif self._is_pdf_file(source):
            return ContentSource.PDF
        elif self._is_url(source):
            return ContentSource.URL
        elif len(source.strip()) > 100:
            return ContentSource.TEXT
        else:
            return ContentSource.TOPIC
    
    def _is_youtube_url(self, url: str) -> bool:
        """Check if URL is a YouTube video."""
        youtube_patterns = ["youtube.com", "youtu.be"]
        return any(pattern in url.lower() for pattern in youtube_patterns)
    
    def _is_pdf_file(self, path: str) -> bool:
        """Check if path is a PDF file."""
        return path.lower().endswith('.pdf') and os.path.exists(path)
    
    def _is_url(self, text: str) -> bool:
        """Check if text is a URL."""
        try:
            result = urlparse(text)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def generate_podcast_from_youtube(self, youtube_url: str, **kwargs) -> Dict[str, Any]:
        """
        Generate podcast from YouTube video.
        
        Args:
            youtube_url: YouTube video URL
            **kwargs: Additional configuration options
            
        Returns:
            Dictionary with podcast generation results
        """
        logger.info(f"Generating podcast from YouTube: {youtube_url}")
        
        input_data = {
            "content_source": {
                "urls": [youtube_url]
            },
            "voice_config": {
                "tts_model": kwargs.get("tts_model", "edge"),
                "speaker_1_voice": kwargs.get("speaker_1_voice", "en-US-JennyNeural"),
                "speaker_2_voice": kwargs.get("speaker_2_voice", "en-US-EricNeural")
            },
            "conversation_config": {
                "podcast_name": kwargs.get("podcast_name", "YouTube Content Podcast"),
                "podcast_tagline": kwargs.get("podcast_tagline", "Generated from YouTube video"),
                "creativity": kwargs.get("creativity", 0.7),
                "style": kwargs.get("style", ["engaging", "informative"])
            },
            "ai_config": {
                "llm_model": kwargs.get("llm_model", "gemini-1.5-pro-latest")
            }
        }
        
        result = self.podcastfy_tool.generate(input_data)
        return result.to_dict()
    
    def generate_podcast_from_pdf(self, pdf_path: str, **kwargs) -> Dict[str, Any]:
        """
        Generate podcast from PDF document.
        
        Args:
            pdf_path: Path to PDF file
            **kwargs: Additional configuration options
            
        Returns:
            Dictionary with podcast generation results
        """
        logger.info(f"Generating podcast from PDF: {pdf_path}")
        
        input_data = {
            "content_source": {
                "pdf_files": [pdf_path]
            },
            "voice_config": {
                "tts_model": kwargs.get("tts_model", "openai"),
                "speaker_1_voice": kwargs.get("speaker_1_voice"),
                "speaker_2_voice": kwargs.get("speaker_2_voice")
            },
            "conversation_config": {
                "podcast_name": kwargs.get("podcast_name", "Document Analysis Podcast"),
                "podcast_tagline": kwargs.get("podcast_tagline", "Generated from PDF document"),
                "creativity": kwargs.get("creativity", 0.6),
                "style": kwargs.get("style", ["educational", "analytical"])
            },
            "ai_config": {
                "llm_model": kwargs.get("llm_model", "gpt-4")
            }
        }
        
        result = self.podcastfy_tool.generate(input_data)
        return result.to_dict()
    
    def generate_podcast_from_website(self, website_url: str, **kwargs) -> Dict[str, Any]:
        """
        Generate podcast from website content.
        
        Args:
            website_url: Website URL
            **kwargs: Additional configuration options
            
        Returns:
            Dictionary with podcast generation results
        """
        logger.info(f"Generating podcast from website: {website_url}")
        
        input_data = {
            "content_source": {
                "urls": [website_url]
            },
            "voice_config": {
                "tts_model": kwargs.get("tts_model", "elevenlabs"),
                "speaker_1_voice": kwargs.get("speaker_1_voice"),
                "speaker_2_voice": kwargs.get("speaker_2_voice")
            },
            "conversation_config": {
                "podcast_name": kwargs.get("podcast_name", "Web Content Podcast"),
                "podcast_tagline": kwargs.get("podcast_tagline", "Generated from website content"),
                "creativity": kwargs.get("creativity", 0.8),
                "style": kwargs.get("style", ["casual", "informative"])
            },
            "ai_config": {
                "llm_model": kwargs.get("llm_model", "gemini-1.5-pro-latest")
            }
        }
        
        result = self.podcastfy_tool.generate(input_data)
        return result.to_dict()
    
    def generate_podcast_from_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Generate podcast from direct text input.
        
        Args:
            text: Text content
            **kwargs: Additional configuration options
            
        Returns:
            Dictionary with podcast generation results
        """
        logger.info(f"Generating podcast from text (length: {len(text)})")
        
        input_data = {
            "content_source": {
                "text": text
            },
            "voice_config": {
                "tts_model": kwargs.get("tts_model", "edge"),
                "speaker_1_voice": kwargs.get("speaker_1_voice", "en-US-JennyNeural"),
                "speaker_2_voice": kwargs.get("speaker_2_voice", "en-US-EricNeural")
            },
            "conversation_config": {
                "podcast_name": kwargs.get("podcast_name", "Text Content Podcast"),
                "podcast_tagline": kwargs.get("podcast_tagline", "Generated from text input"),
                "creativity": kwargs.get("creativity", 0.7),
                "style": kwargs.get("style", ["engaging", "conversational"])
            },
            "ai_config": {
                "llm_model": kwargs.get("llm_model", "gemini-1.5-pro-latest")
            }
        }
        
        result = self.podcastfy_tool.generate(input_data)
        return result.to_dict()
    
    def generate_podcast_from_topic(self, topic: str, **kwargs) -> Dict[str, Any]:
        """
        Generate podcast from topic (AI-generated content).
        
        Args:
            topic: Topic to generate content about
            **kwargs: Additional configuration options
            
        Returns:
            Dictionary with podcast generation results
        """
        logger.info(f"Generating podcast from topic: {topic}")
        
        input_data = {
            "content_source": {
                "topic": topic
            },
            "voice_config": {
                "tts_model": kwargs.get("tts_model", "edge"),
                "speaker_1_voice": kwargs.get("speaker_1_voice", "en-US-JennyNeural"),
                "speaker_2_voice": kwargs.get("speaker_2_voice", "en-US-EricNeural")
            },
            "conversation_config": {
                "podcast_name": kwargs.get("podcast_name", "Topic Exploration Podcast"),
                "podcast_tagline": kwargs.get("podcast_tagline", f"Exploring: {topic}"),
                "creativity": kwargs.get("creativity", 0.8),
                "style": kwargs.get("style", ["exploratory", "educational"])
            },
            "ai_config": {
                "llm_model": kwargs.get("llm_model", "gemini-1.5-pro-latest")
            }
        }
        
        result = self.podcastfy_tool.generate(input_data)
        return result.to_dict()
    
    def generate_podcast_auto(self, source: str, **kwargs) -> Dict[str, Any]:
        """
        Automatically detect content type and generate podcast.
        
        Args:
            source: Content source (URL, file path, text, or topic)
            **kwargs: Additional configuration options
            
        Returns:
            Dictionary with podcast generation results
        """
        content_type = self.detect_content_type(source)
        logger.info(f"Auto-detected content type: {content_type} for source: {source}")
        
        if content_type == ContentSource.URL:
            if self._is_youtube_url(source):
                return self.generate_podcast_from_youtube(source, **kwargs)
            else:
                return self.generate_podcast_from_website(source, **kwargs)
        elif content_type == ContentSource.PDF:
            return self.generate_podcast_from_pdf(source, **kwargs)
        elif content_type == ContentSource.TEXT:
            return self.generate_podcast_from_text(source, **kwargs)
        elif content_type == ContentSource.TOPIC:
            return self.generate_podcast_from_topic(source, **kwargs)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")


class DaytonaToolRegistry:
    """
    Daytona tool registry that integrates Podcastfy with full content support.
    """
    
    def __init__(self):
        self.integration = DaytonaPodcastfyIntegration()
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, Any]:
        """Register all Podcastfy tools in Daytona registry."""
        return {
            "podcastfy": {
                "name": "podcastfy",
                "description": "Generate AI-powered podcast conversations from various content sources",
                "version": "1.0.0",
                "tags": ["audio", "ai", "podcast", "tts", "content-generation"],
                "functions": {
                    "generate_from_youtube": self.integration.generate_podcast_from_youtube,
                    "generate_from_pdf": self.integration.generate_podcast_from_pdf,
                    "generate_from_website": self.integration.generate_podcast_from_website,
                    "generate_from_text": self.integration.generate_podcast_from_text,
                    "generate_from_topic": self.integration.generate_podcast_from_topic,
                    "generate_auto": self.integration.generate_podcast_auto
                },
                "schema": self.integration.podcastfy_tool.get_schema(),
                "examples": self._get_examples()
            }
        }
    
    def _get_examples(self) -> List[Dict[str, Any]]:
        """Get example usage for each content type."""
        return [
            {
                "name": "YouTube Video",
                "description": "Generate podcast from YouTube video",
                "input": {
                    "source": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "tts_model": "edge",
                    "podcast_name": "YouTube Content"
                },
                "function": "generate_from_youtube"
            },
            {
                "name": "PDF Document",
                "description": "Generate podcast from PDF file",
                "input": {
                    "source": "./data/pdf/research_paper.pdf",
                    "tts_model": "openai",
                    "podcast_name": "Document Analysis"
                },
                "function": "generate_from_pdf"
            },
            {
                "name": "Website Article",
                "description": "Generate podcast from website content",
                "input": {
                    "source": "https://www.bbc.com/news/technology",
                    "tts_model": "elevenlabs",
                    "podcast_name": "Tech News"
                },
                "function": "generate_from_website"
            },
            {
                "name": "Direct Text",
                "description": "Generate podcast from text input",
                "input": {
                    "source": "Artificial Intelligence is transforming industries...",
                    "tts_model": "edge",
                    "podcast_name": "AI Discussion"
                },
                "function": "generate_from_text"
            },
            {
                "name": "Topic Generation",
                "description": "Generate podcast from topic",
                "input": {
                    "source": "The future of renewable energy",
                    "tts_model": "edge",
                    "podcast_name": "Green Future"
                },
                "function": "generate_from_topic"
            }
        ]
    
    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get a tool from the registry."""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List all available tools."""
        return list(self.tools.keys())
    
    def execute_tool(self, tool_name: str, function_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a specific tool function."""
        tool = self.get_tool(tool_name)
        if not tool:
            return {"status": "error", "message": f"Tool {tool_name} not found"}
        
        function = tool["functions"].get(function_name)
        if not function:
            return {"status": "error", "message": f"Function {function_name} not found in {tool_name}"}
        
        try:
            result = function(**kwargs)
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}


class DaytonaChatInterface:
    """
    Daytona chat interface that uses the tool registry.
    """
    
    def __init__(self):
        self.tool_registry = DaytonaToolRegistry()
    
    def handle_user_message(self, message: str) -> str:
        """Handle user message and trigger appropriate podcast generation."""
        
        message_lower = message.lower()
        
        # Check for podcast generation requests
        if any(keyword in message_lower for keyword in ["generate podcast", "create podcast", "make podcast"]):
            return self._handle_podcast_request(message)
        
        return "I can help you generate podcasts from YouTube videos, PDFs, websites, text, or topics. Try saying 'generate podcast from this YouTube video: [URL]'"
    
    def _handle_podcast_request(self, message: str) -> str:
        """Handle podcast generation request."""
        
        # Extract content source from message
        source = self._extract_source_from_message(message)
        if not source:
            return "❌ Please provide a content source (YouTube URL, PDF path, website URL, text, or topic)"
        
        # Detect content type and generate podcast
        try:
            result = self.tool_registry.integration.generate_podcast_auto(source)
            
            if result["status"] == "success":
                return f"🎙️ Podcast generated successfully!\n" \
                       f"📁 Audio: {result['audio_file']}\n" \
                       f"📝 Transcript: {result['transcript_file']}\n" \
                       f"⏱️ Time: {result['metadata'].get('generation_time', 'N/A'):.2f}s"
            else:
                return f"❌ Failed to generate podcast: {result['error_message']}"
                
        except Exception as e:
            return f"❌ Error generating podcast: {str(e)}"
    
    def _extract_source_from_message(self, message: str) -> Optional[str]:
        """Extract content source from user message."""
        
        # Extract URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, message)
        if urls:
            return urls[0]
        
        # Extract file paths
        file_pattern = r'[./][^\s]*\.(pdf|txt|md)'
        files = re.findall(file_pattern, message)
        if files:
            return files[0]
        
        # Extract text after keywords
        keywords = ["from", "about", "on", "regarding"]
        for keyword in keywords:
            if keyword in message.lower():
                parts = message.lower().split(keyword)
                if len(parts) > 1:
                    return parts[1].strip()
        
        return None


# Example usage and testing
def main():
    """Example usage of Daytona + Podcastfy integration."""
    
    print("🎯 Daytona + Podcastfy Integration with Full Content Support")
    print("=" * 70)
    
    # Initialize integration
    integration = DaytonaPodcastfyIntegration()
    chat_interface = DaytonaChatInterface()
    
    # Example 1: YouTube video
    print("\n🎥 Example 1: YouTube Video")
    print("-" * 40)
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = integration.generate_podcast_from_youtube(youtube_url)
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Audio: {result['audio_file']}")
    
    # Example 2: Topic generation
    print("\n🤖 Example 2: Topic Generation")
    print("-" * 40)
    topic = "The future of artificial intelligence"
    result = integration.generate_podcast_from_topic(topic)
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Audio: {result['audio_file']}")
    
    # Example 3: Auto-detection
    print("\n🔍 Example 3: Auto-detection")
    print("-" * 40)
    sources = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "The future of renewable energy",
        "Artificial Intelligence is transforming industries worldwide..."
    ]
    
    for source in sources:
        content_type = integration.detect_content_type(source)
        print(f"Source: {source[:50]}...")
        print(f"Detected type: {content_type}")
        print()
    
    print("🎉 Integration ready for Daytona!")


if __name__ == "__main__":
    main()
