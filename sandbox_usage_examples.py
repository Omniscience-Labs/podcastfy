#!/usr/bin/env python3
"""
Podcastfy Sandbox Integration Usage Examples

This file demonstrates how to use the Podcastfy sandbox integration
in various scenarios and environments.
"""

import sys
from pathlib import Path

# Add the podcastfy directory to the path
sys.path.insert(0, str(Path(__file__).parent / "podcastfy"))

from podcastfy.sandbox_integration import PodcastfyTool, generate_podcast_simple, SANDBOX_TOOL_REGISTRY
from podcastfy.schema import PodcastfyInput, VoiceConfig, ConversationConfig, AIConfig, TTSModel, LLMModel


def example_1_simple_usage():
    """Example 1: Simple usage with minimal configuration."""
    print("🎯 Example 1: Simple Usage")
    print("-" * 40)
    
    # Generate podcast from text with minimal config
    result = generate_podcast_simple(
        content="Artificial Intelligence is transforming how we work and live.",
        content_type="text",
        tts_model="edge"  # Free, no API key needed
    )
    
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Audio file: {result['audio_file']}")
        print(f"Transcript file: {result['transcript_file']}")
        print(f"Generation time: {result['metadata']['generation_time']:.2f}s")
    
    print()


def example_2_advanced_usage():
    """Example 2: Advanced usage with full configuration."""
    print("🎯 Example 2: Advanced Usage")
    print("-" * 40)
    
    # Create tool instance
    tool = PodcastfyTool()
    
    # Prepare input with full configuration
    input_data = {
        "content_source": {
            "text": "Machine learning and deep learning are revolutionizing the field of artificial intelligence."
        },
        "voice_config": {
            "tts_model": "edge",
            "speaker_1_voice": "en-US-JennyNeural",
            "speaker_2_voice": "en-US-EricNeural"
        },
        "conversation_config": {
            "podcast_name": "AI Insights",
            "podcast_tagline": "Exploring the future of artificial intelligence",
            "creativity": 0.8,
            "style": ["educational", "engaging"],
            "roles_person1": "AI researcher",
            "roles_person2": "curious journalist"
        },
        "ai_config": {
            "llm_model": "gemini-1.5-pro-latest"
        },
        "options": {
            "longform": False,
            "transcript_only": False
        }
    }
    
    # Generate podcast
    result = tool.generate(input_data)
    
    print(f"Status: {result.status}")
    if result.status == 'success':
        print(f"Audio file: {result.audio_file}")
        print(f"Transcript file: {result.transcript_file}")
        print(f"Input type: {result.metadata['input_type']}")
        print(f"TTS model: {result.metadata['tts_model']}")
        print(f"LLM model: {result.metadata['llm_model']}")
    
    print()


def example_3_url_processing():
    """Example 3: Processing content from URLs."""
    print("🎯 Example 3: URL Processing")
    print("-" * 40)
    
    tool = PodcastfyTool()
    
    input_data = {
        "content_source": {
            "urls": ["https://www.bbc.com/news/world-us-canada-68845678"]
        },
        "voice_config": {
            "tts_model": "edge"
        },
        "conversation_config": {
            "podcast_name": "News Brief",
            "creativity": 0.6
        }
    }
    
    result = tool.generate(input_data)
    
    print(f"Status: {result.status}")
    if result.status == 'success':
        print(f"Audio file: {result.audio_file}")
        print(f"Input type: {result.metadata['input_type']}")
    else:
        print(f"Error: {result.error_message}")
    
    print()


def example_4_topic_generation():
    """Example 4: Generating content from topics."""
    print("🎯 Example 4: Topic Generation")
    print("-" * 40)
    
    tool = PodcastfyTool()
    
    input_data = {
        "content_source": {
            "topic": "The future of renewable energy"
        },
        "voice_config": {
            "tts_model": "edge"
        },
        "conversation_config": {
            "podcast_name": "Green Future",
            "podcast_tagline": "Exploring sustainable energy solutions",
            "style": ["informative", "optimistic"]
        }
    }
    
    result = tool.generate(input_data)
    
    print(f"Status: {result.status}")
    if result.status == 'success':
        print(f"Audio file: {result.audio_file}")
        print(f"Input type: {result.metadata['input_type']}")
    else:
        print(f"Error: {result.error_message}")
    
    print()


def example_5_schema_validation():
    """Example 5: Schema validation and error handling."""
    print("🎯 Example 5: Schema Validation")
    print("-" * 40)
    
    tool = PodcastfyTool()
    
    # Test valid input
    valid_input = {
        "content_source": {
            "text": "This is valid input."
        },
        "voice_config": {
            "tts_model": "edge"
        }
    }
    
    is_valid = tool.validate_input(valid_input)
    print(f"Valid input: {'✅ PASSED' if is_valid else '❌ FAILED'}")
    
    # Test invalid input (no content source)
    invalid_input = {
        "voice_config": {
            "tts_model": "edge"
        }
    }
    
    is_valid = tool.validate_input(invalid_input)
    print(f"Invalid input: {'✅ PASSED' if not is_valid else '❌ FAILED'}")
    
    print()


def example_6_tool_registry_integration():
    """Example 6: Tool registry integration."""
    print("🎯 Example 6: Tool Registry Integration")
    print("-" * 40)
    
    # Access tool registry
    tool_info = SANDBOX_TOOL_REGISTRY["podcastfy"]
    
    print(f"Tool name: {tool_info['description']}")
    print(f"Version: {tool_info['version']}")
    print(f"Tags: {', '.join(tool_info['tags'])}")
    print(f"Examples: {len(tool_info['examples'])}")
    
    # Get schema documentation
    tool = PodcastfyTool()
    schema_docs = tool.get_schema()
    
    print(f"Schema version: {schema_docs['version']}")
    print(f"Available examples: {len(schema_docs['examples'])}")
    
    print()


def example_7_programmatic_usage():
    """Example 7: Programmatic usage with dataclasses."""
    print("🎯 Example 7: Programmatic Usage")
    print("-" * 40)
    
    # Create input using dataclasses
    voice_config = VoiceConfig(
        tts_model=TTSModel.EDGE,
        speaker_1_voice="en-US-JennyNeural",
        speaker_2_voice="en-US-EricNeural"
    )
    
    conversation_config = ConversationConfig(
        podcast_name="Tech Talk",
        podcast_tagline="Exploring technology trends",
        creativity=0.7,
        style=["casual", "informative"]
    )
    
    ai_config = AIConfig(
        llm_model=LLMModel.GEMINI_PRO,
        api_key_label="GEMINI_API_KEY"
    )
    
    input_obj = PodcastfyInput(
        text="Quantum computing represents the next frontier in computational power.",
        voice_config=voice_config,
        conversation_config=conversation_config,
        ai_config=ai_config
    )
    
    # Generate podcast
    tool = PodcastfyTool()
    result = tool.generate(input_obj)
    
    print(f"Status: {result.status}")
    if result.status == 'success':
        print(f"Audio file: {result.audio_file}")
        print(f"Generation time: {result.metadata['generation_time']:.2f}s")
    
    print()


def example_8_error_handling():
    """Example 8: Error handling and recovery."""
    print("🎯 Example 8: Error Handling")
    print("-" * 40)
    
    tool = PodcastfyTool()
    
    # Test with invalid configuration
    invalid_input = {
        "content_source": {
            "text": "This should work."
        },
        "voice_config": {
            "tts_model": "invalid_model"  # This will cause an error
        }
    }
    
    result = tool.generate(invalid_input)
    
    print(f"Status: {result.status}")
    if result.status == 'error':
        print(f"Error message: {result.error_message}")
        print("✅ Error handling: PASSED")
    else:
        print("❌ Error handling: FAILED - Expected error but got success")
    
    print()


def main():
    """Run all examples."""
    print("🎙️ Podcastfy Sandbox Integration Examples")
    print("=" * 60)
    
    examples = [
        example_1_simple_usage,
        example_2_advanced_usage,
        example_3_url_processing,
        example_4_topic_generation,
        example_5_schema_validation,
        example_6_tool_registry_integration,
        example_7_programmatic_usage,
        example_8_error_handling
    ]
    
    for i, example_func in enumerate(examples, 1):
        try:
            example_func()
        except Exception as e:
            print(f"❌ Example {i} failed: {str(e)}")
            print()
    
    print("🎉 All examples completed!")
    print("\n📚 Integration Summary:")
    print("- Schema formalization: ✅ Complete")
    print("- Tool registry: ✅ Ready")
    print("- Error handling: ✅ Implemented")
    print("- Documentation: ✅ Available")
    print("- Examples: ✅ Provided")


if __name__ == "__main__":
    main() 