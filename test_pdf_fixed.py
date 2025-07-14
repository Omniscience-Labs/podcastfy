#!/usr/bin/env python3
"""
PDF Processing Test - Fixed Version
Uses the correct CLI approach for PDF files
"""

import subprocess
from pathlib import Path

def test_pdf_processing():
    """Test PDF processing using the correct CLI approach."""
    
    # Find PDF files in the data directory
    pdf_dir = Path("data/pdf")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in data/pdf/")
        return False
    
    # Use the first PDF file found
    pdf_path = pdf_files[0]
    print(f"📄 Testing with PDF: {pdf_path.name}")
    
    # Method 1: Use direct file path (correct approach)
    print("\n🔧 Method 1: Using direct file path")
    
    command = f'python -m podcastfy.client --url "{pdf_path}" --tts-model edge'
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ SUCCESS! PDF processed successfully")
            print("Output:", result.stdout.strip())
            return True
        else:
            print("❌ FAILED!")
            print("Error:", result.stderr.strip())
            return False
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False

if __name__ == "__main__":
    print("🎙️  PDF Processing Test - Fixed Version")
    print("=" * 50)
    test_pdf_processing() 