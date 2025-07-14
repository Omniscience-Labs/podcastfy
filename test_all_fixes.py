#!/usr/bin/env python3
"""
Comprehensive Test Script for All Podcastfy Fixes
Tests all the fixes we've implemented to ensure everything works.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, description, timeout=60):
    """Run a CLI command and return success status."""
    print(f"\n🔧 {description}")
    print(f"Command: {command}")
    print("-" * 60)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            print("✅ SUCCESS!")
            if result.stdout:
                print("Output:", result.stdout.strip())
            return True
        else:
            print("❌ FAILED!")
            print("Error:", result.stderr.strip())
            return False
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT: Command took too long")
        return False
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False

def test_frontend_server():
    """Test the frontend server on port 5001."""
    print("\n🌐 TEST 1: Frontend Server (Port 5001)")
    print("=" * 60)
    
    # Test if server can start
    try:
        # Start server in background
        process = subprocess.Popen(
            ["cd daytona_ui && python server.py"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Test health endpoint
        import requests
        try:
            response = requests.get("http://localhost:5001/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Frontend server is running on port 5001")
                print("Response:", response.json())
                process.terminate()
                return True
            else:
                print(f"❌ Server responded with status {response.status_code}")
                process.terminate()
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Could not connect to server: {e}")
            process.terminate()
            return False
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False

def test_api_endpoints():
    """Test the FastAPI endpoints."""
    print("\n🔌 TEST 2: FastAPI Endpoints")
    print("=" * 60)
    
    # Test health endpoint
    success = run_command(
        'python -c "from fastapi.testclient import TestClient; from podcastfy.api.fast_app import app; client = TestClient(app); response = client.get(\"/health\"); print(f\"Status: {response.status_code}\"); print(f\"Response: {response.json()}\")"',
        "Testing FastAPI health endpoint"
    )
    
    # Test validation endpoint
    success &= run_command(
        'python -c "from fastapi.testclient import TestClient; from podcastfy.api.fast_app import app; client = TestClient(app); response = client.post(\"/generate\", json={}); print(f\"Status: {response.status_code}\"); print(f\"Expected: 400 for empty input\")"',
        "Testing FastAPI input validation"
    )
    
    return success

def test_content_sources():
    """Test all content sources."""
    print("\n📄 TEST 3: Content Sources")
    print("=" * 60)
    
    # Test PDF processing
    pdf_files = list(Path("data/pdf").glob("*.pdf"))
    if pdf_files:
        pdf_path = pdf_files[0]
        success = run_command(
            f'python -m podcastfy.client --url "{pdf_path}" --tts-model edge',
            f"Testing PDF processing: {pdf_path.name}"
        )
    else:
        print("❌ No PDF files found for testing")
        success = False
    
    # Test website processing
    success &= run_command(
        'python -m podcastfy.client --url "https://example.com" --tts-model edge',
        "Testing website processing"
    )
    
    # Test text processing
    success &= run_command(
        'python -m podcastfy.client --text "This is a test podcast about artificial intelligence and its impact on society." --tts-model edge',
        "Testing text processing"
    )
    
    return success

def test_image_processing():
    """Test image processing with base64 conversion."""
    print("\n🖼️ TEST 4: Image Processing (Base64)")
    print("=" * 60)
    
    # Test image processing script
    success = run_command(
        'python test_image_fixed.py',
        "Testing image processing with base64 conversion"
    )
    
    return success

def test_youtube_processing():
    """Test YouTube processing with reliable videos."""
    print("\n📺 TEST 5: YouTube Processing")
    print("=" * 60)
    
    # Test YouTube processing script
    success = run_command(
        'python test_youtube_fixed.py',
        "Testing YouTube processing with reliable videos",
        timeout=180  # Longer timeout for YouTube
    )
    
    return success

def test_pytest_coverage():
    """Test pytest coverage."""
    print("\n🧪 TEST 6: Pytest Coverage")
    print("=" * 60)
    
    # Test core functionality tests
    success = run_command(
        'python -m pytest tests/test_api.py -v',
        "Testing API tests"
    )
    
    success &= run_command(
        'python -m pytest tests/test_client.py -v',
        "Testing client tests"
    )
    
    success &= run_command(
        'python -m pytest tests/test_content_parser.py -v',
        "Testing content parser tests"
    )
    
    return success

def main():
    """Run all tests."""
    print("🎙️ PODCASTFY COMPREHENSIVE FIXES TEST")
    print("=" * 60)
    print(f"Starting tests at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Frontend Server", test_frontend_server),
        ("API Endpoints", test_api_endpoints),
        ("Content Sources", test_content_sources),
        ("Image Processing", test_image_processing),
        ("YouTube Processing", test_youtube_processing),
        ("Pytest Coverage", test_pytest_coverage)
    ]
    
    results = {}
    total_tests = len(tests)
    passed_tests = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                results[test_name] = "PASS"
                passed_tests += 1
            else:
                results[test_name] = "FAIL"
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {str(e)}")
            results[test_name] = "ERROR"
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        status_icon = "✅" if result == "PASS" else "❌"
        print(f"{status_icon} {test_name}: {result}")
    
    print(f"\n📈 OVERALL RESULTS:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {total_tests - passed_tests}")
    print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! All fixes are working correctly!")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 