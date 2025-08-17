"""
Podcastfy Schema Definitions for Sandbox Integration

This module provides formal schema definitions for integrating Podcastfy
into sandbox tool registries and external systems.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Union, Dict, Any
from enum import Enum
import json


class TTSModel(str, Enum):
    """Available Text-to-Speech models."""
    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"
    EDGE = "edge"
    GEMINI = "gemini"
    GEMINIMULTI = "geminimulti"


class LLMModel(str, Enum):
    """Available Large Language Models."""
    GPT4 = "gpt-4"
    GPT35 = "gpt-3.5-turbo"
    GEMINI_PRO = "gemini-1.5-pro-latest"
    GEMINI_FLASH = "gemini-1.5-flash"
    CLAUDE = "claude-3-sonnet"


class ContentSource(str, Enum):
    """Types of content sources."""
    URL = "url"
    TEXT = "text"
    TOPIC = "topic"
    PDF = "pdf"
    IMAGE = "image"


@dataclass
class VoiceConfig:
    """Voice configuration for TTS."""
    tts_model: TTSModel = TTSModel.OPENAI
    speaker_1_voice: Optional[str] = None
    speaker_2_voice: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tts_model": self.tts_model.value,
            "speaker_1_voice": self.speaker_1_voice,
            "speaker_2_voice": self.speaker_2_voice
        }


@dataclass
class ConversationConfig:
    """Conversation style and structure configuration."""
    style: List[str] = field(default_factory=lambda: ["engaging", "fast-paced"])
    roles_person1: str = "main summarizer"
    roles_person2: str = "questioner/clarifier"
    dialogue_structure: List[str] = field(default_factory=lambda: ["Introduction", "Main Content", "Conclusion"])
    podcast_name: str = "PODCASTIFY"
    podcast_tagline: str = "Your Personal Generative AI Podcast"
    output_language: str = "English"
    engagement_techniques: List[str] = field(default_factory=lambda: ["rhetorical questions", "anecdotes", "analogies"])
    creativity: float = 0.7
    user_instructions: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_style": self.style,
            "roles_person1": self.roles_person1,
            "roles_person2": self.roles_person2,
            "dialogue_structure": self.dialogue_structure,
            "podcast_name": self.podcast_name,
            "podcast_tagline": self.podcast_tagline,
            "output_language": self.output_language,
            "engagement_techniques": self.engagement_techniques,
            "creativity": self.creativity,
            "user_instructions": self.user_instructions
        }


@dataclass
class AIConfig:
    """AI model configuration."""
    llm_model: LLMModel = LLMModel.GEMINI_PRO
    api_key_label: str = "GEMINI_API_KEY"
    is_local: bool = False
    max_output_tokens: int = 8192
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "llm_model": self.llm_model.value,
            "api_key_label": self.api_key_label,
            "is_local": self.is_local,
            "max_output_tokens": self.max_output_tokens
        }


@dataclass
class PodcastfyInput:
    """Complete input schema for Podcastfy."""
    # Content source (one of these must be provided)
    urls: Optional[List[str]] = None
    text: Optional[str] = None
    topic: Optional[str] = None
    pdf_files: Optional[List[str]] = None
    image_files: Optional[List[str]] = None
    
    # Configuration
    voice_config: VoiceConfig = field(default_factory=VoiceConfig)
    conversation_config: ConversationConfig = field(default_factory=ConversationConfig)
    ai_config: AIConfig = field(default_factory=AIConfig)
    
    # Additional options
    longform: bool = False
    transcript_only: bool = False
    
    def validate(self) -> None:
        """Validate that at least one content source is provided."""
        content_sources = [
            self.urls and len(self.urls) > 0,
            self.text and len(self.text.strip()) > 0,
            self.topic and len(self.topic.strip()) > 0,
            self.pdf_files and len(self.pdf_files) > 0,
            self.image_files and len(self.image_files) > 0
        ]
        
        if not any(content_sources):
            raise ValueError("At least one content source must be provided: urls, text, topic, pdf_files, or image_files")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for API calls."""
        self.validate()
        
        result = {
            "longform": self.longform,
            "transcript_only": self.transcript_only
        }
        
        # Add content sources
        if self.urls:
            result["urls"] = self.urls
        if self.text:
            result["text"] = self.text
        if self.topic:
            result["topic"] = self.topic
        if self.pdf_files:
            result["pdf_files"] = self.pdf_files
        if self.image_files:
            result["image_files"] = self.image_files
        
        # Add configurations
        result.update(self.voice_config.to_dict())
        result.update(self.conversation_config.to_dict())
        result.update(self.ai_config.to_dict())
        
        return result


@dataclass
class PodcastfyOutput:
    """Output schema for Podcastfy."""
    audio_file: Optional[str] = None
    transcript_file: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "success"
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "audio_file": self.audio_file,
            "transcript_file": self.transcript_file,
            "metadata": self.metadata,
            "status": self.status,
            "error_message": self.error_message
        }


# JSON Schema for external integrations
PODCASTFY_JSON_SCHEMA = {
    "type": "object",
    "title": "Podcastfy Input Schema",
    "description": "Schema for generating AI-powered podcast conversations",
    "properties": {
        "content_source": {
            "type": "object",
            "oneOf": [
                {
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {"type": "string", "format": "uri"},
                            "description": "URLs to extract content from"
                        }
                    },
                    "required": ["urls"]
                },
                {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Direct text input for podcast generation"
                        }
                    },
                    "required": ["text"]
                },
                {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Topic to generate content about"
                        }
                    },
                    "required": ["topic"]
                }
            ]
        },
        "voice_config": {
            "type": "object",
            "properties": {
                "tts_model": {
                    "type": "string",
                    "enum": ["openai", "elevenlabs", "edge", "gemini", "geminimulti"],
                    "default": "openai"
                },
                "speaker_1_voice": {"type": "string"},
                "speaker_2_voice": {"type": "string"}
            }
        },
        "conversation_config": {
            "type": "object",
            "properties": {
                "style": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["engaging", "fast-paced"]
                },
                "roles_person1": {"type": "string", "default": "main summarizer"},
                "roles_person2": {"type": "string", "default": "questioner/clarifier"},
                "podcast_name": {"type": "string", "default": "PODCASTIFY"},
                "creativity": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.7
                }
            }
        },
        "ai_config": {
            "type": "object",
            "properties": {
                "llm_model": {
                    "type": "string",
                    "enum": ["gpt-4", "gpt-3.5-turbo", "gemini-1.5-pro-latest", "gemini-1.5-flash"],
                    "default": "gemini-1.5-pro-latest"
                }
            }
        },
        "options": {
            "type": "object",
            "properties": {
                "longform": {"type": "boolean", "default": False},
                "transcript_only": {"type": "boolean", "default": False}
            }
        }
    },
    "required": ["content_source"]
}


def get_schema_documentation() -> Dict[str, Any]:
    """Get complete schema documentation for external integrations."""
    return {
        "version": "1.0.0",
        "name": "podcastfy",
        "description": "Generate AI-powered podcast conversations from various content sources",
        "schema": PODCASTFY_JSON_SCHEMA,
        "examples": [
            {
                "name": "Generate from URL",
                "input": {
                    "content_source": {
                        "urls": ["https://www.bbc.com/news"]
                    },
                    "voice_config": {
                        "tts_model": "openai"
                    },
                    "conversation_config": {
                        "podcast_name": "News Brief",
                        "creativity": 0.7
                    }
                }
            },
            {
                "name": "Generate from Text",
                "input": {
                    "content_source": {
                        "text": "Artificial Intelligence is transforming the world..."
                    },
                    "voice_config": {
                        "tts_model": "elevenlabs"
                    }
                }
            },
            {
                "name": "Generate from Topic",
                "input": {
                    "content_source": {
                        "topic": "The future of renewable energy"
                    },
                    "ai_config": {
                        "llm_model": "gpt-4"
                    }
                }
            }
        ],
        "output_schema": {
            "type": "object",
            "properties": {
                "audio_file": {
                    "type": "string",
                    "format": "file-path",
                    "description": "Path to generated MP3 audio file"
                },
                "transcript_file": {
                    "type": "string",
                    "format": "file-path",
                    "description": "Path to generated transcript text file"
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "duration": {"type": "number"},
                        "word_count": {"type": "number"},
                        "generation_time": {"type": "number"}
                    }
                },
                "status": {"type": "string", "enum": ["success", "error"]},
                "error_message": {"type": "string"}
            }
        }
    } 