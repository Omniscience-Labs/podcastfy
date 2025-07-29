#!/usr/bin/env python3
"""
Test Podcastfy Integration with Local Backend
"""

import sys
import os
sys.path.append('..')

from operator_integration import PodcastfyOperatorTool

def test_local_integration():
    """Test the integration with local Flask backend"""
    
    # Use local Flask backend (uses /api/ endpoints)
    tool = PodcastfyOperatorTool(base_url="http://localhost:8000")
    
    print("🧪 Testing Podcastfy Integration")
    print("=" * 50)
    
    # Test health check
    print("1. Health Check:")
    health = tool.health_check()
    print(f"   Status: {health}")
    
    if health.get('status') != 'healthy':
        print("❌ Backend not healthy, stopping test")
        return
    
    print("\n2. Generating Podcast:")
    print("   Topic: 'The Future of AI in Software Development'")
    print("   TTS Model: edge")
    print("   Style: educational")
    
    # Generate a podcast
    result = tool.generate_podcast(
        topic="The Future of AI in Software Development",
        tts_model="edge", 
        conversation_style="educational"
    )
    
    print(f"\n3. Results:")
    if result.success:
        print("✅ Podcast generated successfully!")
        print(f"🎵 Audio URL: {result.audio_url}")
        print(f"📝 Transcript URL: {result.transcript_url}")
        print(f"💬 Message: {result.message}")
    else:
        print("❌ Failed to generate podcast")
        print(f"Error: {result.error}")

if __name__ == "__main__":
    test_local_integration() 