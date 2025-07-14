#!/usr/bin/env python3
"""
Image-to-Podcast Test - Fixed Version
Uses base64 conversion for Gemini API compatibility
"""

import sys
import os
from pathlib import Path

# Add podcastfy to path
sys.path.insert(0, str(Path(__file__).parent / "podcastfy"))

from podcastfy.utils.image_processor import ImageProcessor, validate_images_for_podcastfy
from podcastfy.content_generator import ContentGenerator
from podcastfy.utils.config_conversation import load_conversation_config
import uuid

def test_image_processing():
    """Test image processing with base64 conversion."""
    
    print("🖼️  Image-to-Podcast Test - Fixed Version")
    print("=" * 60)
    
    # Find image files in the data directory
    image_dir = Path("data/images")
    image_files = list(image_dir.glob("*"))
    
    if not image_files:
        print("❌ No image files found in data/images/")
        return False
    
    # Filter for image files
    test_images = []
    for img in image_files:
        if img.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            test_images.append(str(img))
            if len(test_images) >= 2:  # Test up to 2 images
                break
    
    if not test_images:
        print("❌ No valid image files found")
        return False
    
    print(f"📁 Found {len(test_images)} test images:")
    for img in test_images:
        print(f"   - {Path(img).name}")
    
    # Validate images
    print("\n🔍 Validating images...")
    validation_results = validate_images_for_podcastfy(test_images)
    
    for i, result in enumerate(validation_results):
        if "error" in result:
            print(f"❌ {Path(test_images[i]).name}: {result['error']}")
        else:
            status = "✅" if result["is_valid"] else "❌"
            print(f"{status} {Path(test_images[i]).name}: {result['size_mb']}MB, {result['mime_type']}")
    
    # Test base64 conversion
    print("\n🔄 Testing base64 conversion...")
    try:
        base64_images = ImageProcessor.process_images_for_gemini(test_images)
        print(f"✅ Successfully converted {len(base64_images)} images to base64")
        
        # Show sample of base64 data
        for i, base64_img in enumerate(base64_images):
            sample = base64_img[:50] + "..." if len(base64_img) > 50 else base64_img
            print(f"   Image {i+1}: {sample}")
            
    except Exception as e:
        print(f"❌ Base64 conversion failed: {str(e)}")
        return False
    
    # Test content generation with images
    print("\n🎙️  Testing content generation with images...")
    try:
        # Initialize content generator
        config = load_conversation_config()
        content_generator = ContentGenerator(
            model_name="gemini-1.5-pro-latest",
            api_key_label="GEMINI_API_KEY",
            conversation_config=config.to_dict()
        )
        
        # Generate content with images
        output_filepath = f"data/transcripts/transcript_image_test_{uuid.uuid4().hex}.txt"
        
        response = content_generator.generate_qa_content(
            input_texts="Please analyze these images and generate an engaging podcast conversation about what you see.",
            image_file_paths=base64_images,  # Use base64 images
            output_filepath=output_filepath
        )
        
        print("✅ Content generation successful!")
        print(f"📝 Transcript saved to: {output_filepath}")
        print(f"📄 Response length: {len(response)} characters")
        
        # Show sample of generated content
        sample = response[:200] + "..." if len(response) > 200 else response
        print(f"📖 Sample content: {sample}")
        
        return True
        
    except Exception as e:
        print(f"❌ Content generation failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_image_processing()
    if success:
        print("\n🎉 Image processing test completed successfully!")
    else:
        print("\n❌ Image processing test failed!")
        sys.exit(1) 