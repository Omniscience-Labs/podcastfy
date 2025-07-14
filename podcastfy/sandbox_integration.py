"""
Podcastfy Sandbox Tool Registry Integration

This module provides the interface for integrating Podcastfy into sandbox
tool registries and external systems.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path

from .schema import PodcastfyInput, PodcastfyOutput, TTSModel, LLMModel
from .client import generate_podcast
from .utils.config import load_config

logger = logging.getLogger(__name__)


class PodcastfyTool:
    """
    Main tool class for sandbox integration.
    
    This class provides a clean interface for generating podcasts
    that can be easily integrated into sandbox environments.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Podcastfy tool.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config = load_config(config_path) if config_path else load_config()
        self.schema_docs = self._get_schema_documentation()
    
    def _get_schema_documentation(self) -> Dict[str, Any]:
        """Get schema documentation for tool registry."""
        from .schema import get_schema_documentation
        return get_schema_documentation()
    
    def generate(
        self,
        input_data: Union[Dict[str, Any], PodcastfyInput]
    ) -> PodcastfyOutput:
        """
        Generate a podcast from input data.
        
        Args:
            input_data: Input data as dictionary or PodcastfyInput object
            
        Returns:
            PodcastfyOutput: Generated podcast results
        """
        start_time = time.time()
        
        try:
            # Convert dict to PodcastfyInput if needed
            if isinstance(input_data, dict):
                input_obj = self._dict_to_input(input_data)
            else:
                input_obj = input_data
            
            # Validate input
            input_obj.validate()
            
            # Convert to format expected by generate_podcast
            podcast_args = self._prepare_podcast_args(input_obj)
            
            # Generate podcast
            result = generate_podcast(**podcast_args)
            
            # Prepare output
            output = PodcastfyOutput(
                audio_file=result if isinstance(result, str) else None,
                transcript_file=self._find_transcript_file(),
                metadata={
                    "generation_time": time.time() - start_time,
                    "input_type": self._get_input_type(input_obj),
                    "tts_model": input_obj.voice_config.tts_model.value,
                    "llm_model": input_obj.ai_config.llm_model.value
                }
            )
            
            logger.info(f"Podcast generated successfully: {output.audio_file}")
            return output
            
        except Exception as e:
            logger.error(f"Error generating podcast: {str(e)}")
            return PodcastfyOutput(
                status="error",
                error_message=str(e),
                metadata={"generation_time": time.time() - start_time}
            )
    
    def _dict_to_input(self, data: Dict[str, Any]) -> PodcastfyInput:
        """Convert dictionary to PodcastfyInput object."""
        # Extract content sources
        content_source = data.get("content_source", {})
        
        # Extract configurations
        voice_config_data = data.get("voice_config", {})
        conversation_config_data = data.get("conversation_config", {})
        ai_config_data = data.get("ai_config", {})
        options_data = data.get("options", {})
        
        # Create input object
        return PodcastfyInput(
            urls=content_source.get("urls"),
            text=content_source.get("text"),
            topic=content_source.get("topic"),
            pdf_files=content_source.get("pdf_files"),
            image_files=content_source.get("image_files"),
            voice_config=self._create_voice_config(voice_config_data),
            conversation_config=self._create_conversation_config(conversation_config_data),
            ai_config=self._create_ai_config(ai_config_data),
            longform=options_data.get("longform", False),
            transcript_only=options_data.get("transcript_only", False)
        )
    
    def _create_voice_config(self, data: Dict[str, Any]) -> 'VoiceConfig':
        """Create VoiceConfig from dictionary."""
        from .schema import VoiceConfig, TTSModel
        
        return VoiceConfig(
            tts_model=TTSModel(data.get("tts_model", "openai")),
            speaker_1_voice=data.get("speaker_1_voice"),
            speaker_2_voice=data.get("speaker_2_voice")
        )
    
    def _create_conversation_config(self, data: Dict[str, Any]) -> 'ConversationConfig':
        """Create ConversationConfig from dictionary."""
        from .schema import ConversationConfig
        
        return ConversationConfig(
            style=data.get("style", ["engaging", "fast-paced"]),
            roles_person1=data.get("roles_person1", "main summarizer"),
            roles_person2=data.get("roles_person2", "questioner/clarifier"),
            dialogue_structure=data.get("dialogue_structure", ["Introduction", "Main Content", "Conclusion"]),
            podcast_name=data.get("podcast_name", "PODCASTIFY"),
            podcast_tagline=data.get("podcast_tagline", "Your Personal Generative AI Podcast"),
            output_language=data.get("output_language", "English"),
            engagement_techniques=data.get("engagement_techniques", ["rhetorical questions", "anecdotes", "analogies"]),
            creativity=data.get("creativity", 0.7),
            user_instructions=data.get("user_instructions", "")
        )
    
    def _create_ai_config(self, data: Dict[str, Any]) -> 'AIConfig':
        """Create AIConfig from dictionary."""
        from .schema import AIConfig, LLMModel
        
        return AIConfig(
            llm_model=LLMModel(data.get("llm_model", "gemini-1.5-pro-latest")),
            api_key_label=data.get("api_key_label", "GEMINI_API_KEY"),
            is_local=data.get("is_local", False),
            max_output_tokens=data.get("max_output_tokens", 8192)
        )
    
    def _prepare_podcast_args(self, input_obj: PodcastfyInput) -> Dict[str, Any]:
        """Prepare arguments for generate_podcast function."""
        args = {
            "tts_model": input_obj.voice_config.tts_model.value,
            "transcript_only": input_obj.transcript_only,
            "longform": input_obj.longform,
            "llm_model_name": input_obj.ai_config.llm_model.value,
            "api_key_label": input_obj.ai_config.api_key_label,
            "is_local": input_obj.ai_config.is_local
        }
        
        # Add content sources
        if input_obj.urls:
            args["urls"] = input_obj.urls
        if input_obj.text:
            args["text"] = input_obj.text
        if input_obj.topic:
            args["topic"] = input_obj.topic
        if input_obj.pdf_files:
            args["pdf_files"] = input_obj.pdf_files
        if input_obj.image_files:
            args["image_paths"] = input_obj.image_files
        
        # Add conversation configuration
        conversation_config = {
            "conversation_style": input_obj.conversation_config.style,
            "roles_person1": input_obj.conversation_config.roles_person1,
            "roles_person2": input_obj.conversation_config.roles_person2,
            "dialogue_structure": input_obj.conversation_config.dialogue_structure,
            "podcast_name": input_obj.conversation_config.podcast_name,
            "podcast_tagline": input_obj.conversation_config.podcast_tagline,
            "output_language": input_obj.conversation_config.output_language,
            "engagement_techniques": input_obj.conversation_config.engagement_techniques,
            "creativity": input_obj.conversation_config.creativity,
            "user_instructions": input_obj.conversation_config.user_instructions,
            "text_to_speech": {
                "default_tts_model": input_obj.voice_config.tts_model.value,
                "default_voices": {
                    "question": input_obj.voice_config.speaker_1_voice,
                    "answer": input_obj.voice_config.speaker_2_voice
                }
            }
        }
        
        args["conversation_config"] = conversation_config
        
        return args
    
    def _get_input_type(self, input_obj: PodcastfyInput) -> str:
        """Get the type of input provided."""
        if input_obj.urls:
            return "urls"
        elif input_obj.text:
            return "text"
        elif input_obj.topic:
            return "topic"
        elif input_obj.pdf_files:
            return "pdf_files"
        elif input_obj.image_files:
            return "image_files"
        else:
            return "unknown"
    
    def _find_transcript_file(self) -> Optional[str]:
        """Find the most recent transcript file."""
        transcripts_dir = Path("./data/transcripts")
        if not transcripts_dir.exists():
            return None
        
        transcript_files = list(transcripts_dir.glob("transcript_*.txt"))
        if not transcript_files:
            return None
        
        # Return the most recent file
        latest_file = max(transcript_files, key=lambda f: f.stat().st_mtime)
        return str(latest_file)
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return self.schema_docs
    
    def get_examples(self) -> list:
        """Get example inputs for this tool."""
        return self.schema_docs.get("examples", [])
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data against schema."""
        try:
            input_obj = self._dict_to_input(input_data)
            input_obj.validate()
            return True
        except Exception as e:
            logger.error(f"Input validation failed: {str(e)}")
            return False


# Convenience functions for easy integration
def create_podcastfy_tool(config_path: Optional[str] = None) -> PodcastfyTool:
    """Create a Podcastfy tool instance."""
    return PodcastfyTool(config_path)


def generate_podcast_simple(
    content: str,
    content_type: str = "text",
    tts_model: str = "openai",
    **kwargs
) -> Dict[str, Any]:
    """
    Simple function for generating podcasts with minimal configuration.
    
    Args:
        content: The content to process (URL, text, or topic)
        content_type: Type of content ("url", "text", or "topic")
        tts_model: TTS model to use
        **kwargs: Additional configuration options
        
    Returns:
        Dictionary with results
    """
    tool = PodcastfyTool()
    
    # Prepare input data
    input_data = {
        "content_source": {},
        "voice_config": {"tts_model": tts_model},
        "conversation_config": kwargs.get("conversation_config", {}),
        "ai_config": kwargs.get("ai_config", {}),
        "options": kwargs.get("options", {})
    }
    
    # Set content source
    if content_type == "url":
        input_data["content_source"]["urls"] = [content]
    elif content_type == "text":
        input_data["content_source"]["text"] = content
    elif content_type == "topic":
        input_data["content_source"]["topic"] = content
    else:
        raise ValueError(f"Invalid content_type: {content_type}")
    
    # Generate podcast
    result = tool.generate(input_data)
    return result.to_dict()


# Tool registry integration
SANDBOX_TOOL_REGISTRY = {
    "podcastfy": {
        "class": PodcastfyTool,
        "function": generate_podcast_simple,
        "schema": "get_schema_documentation",
        "description": "Generate AI-powered podcast conversations from various content sources",
        "version": "1.0.0",
        "tags": ["audio", "ai", "podcast", "tts", "content-generation"],
        "examples": [
            {
                "name": "Generate from URL",
                "input": {
                    "content_source": {"urls": ["https://www.bbc.com/news"]},
                    "voice_config": {"tts_model": "openai"},
                    "conversation_config": {"podcast_name": "News Brief"}
                }
            },
            {
                "name": "Generate from Text",
                "input": {
                    "content_source": {"text": "Artificial Intelligence is transforming the world..."},
                    "voice_config": {"tts_model": "elevenlabs"}
                }
            }
        ]
    }
} 