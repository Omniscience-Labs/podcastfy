#!/usr/bin/env python3
"""
YouTube Processing Test - Fixed Version
Uses more reliable videos and better error handling
"""

import subprocess
from pathlib import Path

def test_youtube_processing():
    """Test YouTube processing using reliable videos with transcripts."""
    
    # Use videos that are more likely to have transcripts
    test_videos = [
        {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll (has transcripts)
            "description": "Rick Roll video (reliable transcript)"
        },
        {
            "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",  # PSY - GANGNAM STYLE (has transcripts)
            "description": "Gangnam Style (reliable transcript)"
        },
        {
            "url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk",  # Despacito (has transcripts)
            "description": "Despacito (reliable transcript)"
        }
    ]
    
    print("📺 YouTube Processing Test - Fixed Version")
    print("=" * 60)
    print("Testing with videos that have reliable transcripts...")
    
    for i, video in enumerate(test_videos, 1):
        print(f"\n📺 Test {i}: {video['description']}")
        print(f"URL: {video['url']}")
        
        command = f'python -m podcastfy.client --url "{video["url"]}" --tts-model edge'
        print(f"Command: {command}")
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print("✅ SUCCESS! YouTube video processed successfully")
                print("Output:", result.stdout.strip())
                return True  # Stop at first success
            else:
                print("❌ FAILED!")
                print("Error:", result.stderr.strip())
                if i < len(test_videos):
                    print("Trying next video...")
                    continue
                else:
                    print("All videos failed. Check if YouTube transcript API is working.")
                    return False
        except subprocess.TimeoutExpired:
            print("⏰ TIMEOUT: Video processing took too long")
            if i < len(test_videos):
                print("Trying next video...")
                continue
            else:
                return False
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            if i < len(test_videos):
                print("Trying next video...")
                continue
            else:
                return False
    
    return False

if __name__ == "__main__":
    success = test_youtube_processing()
    if success:
        print("\n🎉 YouTube processing test PASSED!")
    else:
        print("\n❌ YouTube processing test FAILED!")
        print("This might be due to:")
        print("- YouTube API rate limiting")
        print("- Network connectivity issues")
        print("- Video transcript availability") 