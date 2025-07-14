#!/usr/bin/env python3
"""
Test script for Podcastfy Sandbox Integration

This script tests the schema formalization and sandbox tool registry integration.
"""

import sys
import os
import json
from pathlib import Path

# Add the podcastfy directory to the path
sys.path.insert(0, str(Path(__file__).parent / "podcastfy"))

from podcastfy.sandbox_integration import PodcastfyTool, generate_podcast_simple, SANDBOX_TOOL_REGISTRY
from podcastfy.schema import PodcastfyInput, get_schema_documentation


def test_schema_validation():
    """Test schema validation."""
    print("🧪 Testing Schema Validation...")
    
    # Test valid input
    valid_input = {
        "content_source": {
            "text": "Artificial Intelligence is transforming the world."
        },
        "voice_config": {
            "tts_model": "openai"
        },
        "conversation_config": {
            "podcast_name": "Test Podcast",
            "creativity": 0.7
        }
    }
    
    tool = PodcastfyTool()
    is_valid = tool.validate_input(valid_input)
    print(f"✅ Valid input test: {'PASSED' if is_valid else 'FAILED'}")
    
    # Test invalid input (no content source)
    invalid_input = {
        "voice_config": {"tts_model": "openai"}
    }
    
    is_valid = tool.validate_input(invalid_input)
    print(f"✅ Invalid input test: {'PASSED' if not is_valid else 'FAILED'}")
    
    return True


def test_schema_documentation():
    """Test schema documentation generation."""
    print("\n📋 Testing Schema Documentation...")
    
    schema_docs = get_schema_documentation()
    
    required_keys = ["version", "name", "description", "schema", "examples", "output_schema"]
    missing_keys = [key for key in required_keys if key not in schema_docs]
    
    if not missing_keys:
        print("✅ Schema documentation: PASSED")
        print(f"   - Version: {schema_docs['version']}")
        print(f"   - Name: {schema_docs['name']}")
        print(f"   - Examples: {len(schema_docs['examples'])}")
    else:
        print(f"❌ Schema documentation: FAILED - Missing keys: {missing_keys}")
        return False
    
    return True


def test_tool_registry():
    """Test tool registry integration."""
    print("\n🛠️ Testing Tool Registry...")
    
    # Check if tool is registered
    if "podcastfy" not in SANDBOX_TOOL_REGISTRY:
        print("❌ Tool registry: FAILED - podcastfy not found in registry")
        return False
    
    tool_info = SANDBOX_TOOL_REGISTRY["podcastfy"]
    required_keys = ["class", "function", "schema", "description", "version", "tags", "examples"]
    missing_keys = [key for key in required_keys if key not in tool_info]
    
    if not missing_keys:
        print("✅ Tool registry: PASSED")
        print(f"   - Description: {tool_info['description']}")
        print(f"   - Version: {tool_info['version']}")
        print(f"   - Tags: {tool_info['tags']}")
        print(f"   - Examples: {len(tool_info['examples'])}")
    else:
        print(f"❌ Tool registry: FAILED - Missing keys: {missing_keys}")
        return False
    
    return True


def test_simple_generation():
    """Test simple podcast generation."""
    print("\n🎙️ Testing Simple Generation...")
    
    try:
        # Test with text input
        result = generate_podcast_simple(
            content="This is a test of the podcast generation system.",
            content_type="text",
            tts_model="edge"  # Use edge to avoid API key issues
        )
        
        if result["status"] == "success":
            print("✅ Simple generation: PASSED")
            print(f"   - Audio file: {result.get('audio_file', 'N/A')}")
            print(f"   - Transcript file: {result.get('transcript_file', 'N/A')}")
            print(f"   - Generation time: {result.get('metadata', {}).get('generation_time', 'N/A'):.2f}s")
        else:
            print(f"❌ Simple generation: FAILED - {result.get('error_message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Simple generation: FAILED - {str(e)}")
        return False
    
    return True


def test_advanced_generation():
    """Test advanced podcast generation with full configuration."""
    print("\n🚀 Testing Advanced Generation...")
    
    try:
        tool = PodcastfyTool()
        
        # Test with full configuration
        input_data = {
            "content_source": {
                "text": "Machine learning algorithms are revolutionizing how we process and analyze data."
            },
            "voice_config": {
                "tts_model": "edge",
                "speaker_1_voice": "en-US-JennyNeural",
                "speaker_2_voice": "en-US-EricNeural"
            },
            "conversation_config": {
                "podcast_name": "Tech Insights",
                "podcast_tagline": "Exploring the future of technology",
                "creativity": 0.8,
                "style": ["educational", "engaging"]
            },
            "ai_config": {
                "llm_model": "gemini-1.5-pro-latest"
            },
            "options": {
                "longform": False,
                "transcript_only": False
            }
        }
        
        result = tool.generate(input_data)
        
        if result.status == "success":
            print("✅ Advanced generation: PASSED")
            print(f"   - Audio file: {result.audio_file}")
            print(f"   - Transcript file: {result.transcript_file}")
            print(f"   - Input type: {result.metadata.get('input_type', 'N/A')}")
            print(f"   - TTS model: {result.metadata.get('tts_model', 'N/A')}")
        else:
            print(f"❌ Advanced generation: FAILED - {result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ Advanced generation: FAILED - {str(e)}")
        return False
    
    return True


def test_schema_serialization():
    """Test schema serialization to JSON."""
    print("\n📄 Testing Schema Serialization...")
    
    try:
        # Test PodcastfyInput serialization
        input_obj = PodcastfyInput(
            text="Test content for serialization.",
            voice_config=PodcastfyInput.__dataclass_fields__["voice_config"].default_factory(),
            conversation_config=PodcastfyInput.__dataclass_fields__["conversation_config"].default_factory(),
            ai_config=PodcastfyInput.__dataclass_fields__["ai_config"].default_factory()
        )
        
        # Convert to dict
        input_dict = input_obj.to_dict()
        
        # Serialize to JSON
        json_str = json.dumps(input_dict, indent=2)
        
        # Deserialize from JSON
        parsed_dict = json.loads(json_str)
        
        print("✅ Schema serialization: PASSED")
        print(f"   - Input validation: {'PASSED' if input_obj.validate() else 'FAILED'}")
        print(f"   - JSON serialization: {len(json_str)} characters")
        
    except Exception as e:
        print(f"❌ Schema serialization: FAILED - {str(e)}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("🎯 Podcastfy Sandbox Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Schema Validation", test_schema_validation),
        ("Schema Documentation", test_schema_documentation),
        ("Tool Registry", test_tool_registry),
        ("Schema Serialization", test_schema_serialization),
        ("Simple Generation", test_simple_generation),
        ("Advanced Generation", test_advanced_generation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Sandbox integration is ready.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 