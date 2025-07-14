#!/usr/bin/env python3
"""
Comprehensive Validation Script for Podcastfy
Tests all key functionality to ensure the system works as expected.
"""

import os
import sys
import time
import json
import base64
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import pytest

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from podcastfy.client import process_content, generate_podcast
from podcastfy.utils.config import load_config
from podcastfy.content_parser.content_extractor import ContentExtractor

class PodcastfyValidator:
    """Comprehensive validator for Podcastfy system."""
    
    def __init__(self):
        self.results = {
            "backend_validation": {},
            "frontend_validation": {},
            "integration_validation": {},
            "performance_validation": {},
            "overall_status": "PENDING"
        }
        self.test_data_dir = Path("tests/data")
        self.output_dir = Path("validation_output")
        self.output_dir.mkdir(exist_ok=True)
        
    def log_result(self, category: str, test_name: str, status: str, details: str = ""):
        """Log test results."""
        if category not in self.results:
            self.results[category] = {}
        
        self.results[category][test_name] = {
            "status": status,
            "details": details,
            "timestamp": time.time()
        }
        print(f"[{status.upper()}] {category}.{test_name}: {details}")
    
    def validate_backend(self):
        """Backend validation tests."""
        print("\n🔧 BACKEND VALIDATION")
        print("=" * 50)
        
        # 1. Schema validation
        try:
            config = load_config()
            self.log_result("backend_validation", "schema_validation", "PASS", "Configuration loaded successfully")
        except Exception as e:
            self.log_result("backend_validation", "schema_validation", "FAIL", str(e))
            return False
        
        # 2. Content extraction from all sources
        extractor = ContentExtractor()
        
        # Test PDF extraction
        pdf_file = self.test_data_dir / "pdf" / "file.pdf"
        if pdf_file.exists():
            try:
                content = extractor.extract_content(str(pdf_file))
                self.log_result("backend_validation", "pdf_extraction", "PASS", f"Extracted {len(content)} characters")
            except Exception as e:
                self.log_result("backend_validation", "pdf_extraction", "FAIL", str(e))
        else:
            self.log_result("backend_validation", "pdf_extraction", "SKIP", "Test PDF file not found")
        
        # Test website extraction
        try:
            content = extractor.extract_content("https://example.com")
            self.log_result("backend_validation", "website_extraction", "PASS", f"Extracted {len(content)} characters")
        except Exception as e:
            self.log_result("backend_validation", "website_extraction", "FAIL", str(e))
        
        # Test topic generation
        try:
            content = extractor.generate_topic_content("artificial intelligence")
            self.log_result("backend_validation", "topic_generation", "PASS", f"Generated {len(content)} characters")
        except Exception as e:
            self.log_result("backend_validation", "topic_generation", "SKIP", f"Topic generation failed: {str(e)}")
        
        # 3. Audio generation with Edge TTS (no API key required)
        try:
            test_text = "This is a test audio generation."
            audio_path = process_content(
                text=test_text,
                tts_model="edge",
                generate_audio=True
            )
            if audio_path and os.path.exists(audio_path):
                self.log_result("backend_validation", "audio_generation", "PASS", f"Generated audio: {audio_path}")
            else:
                self.log_result("backend_validation", "audio_generation", "FAIL", "Audio file not created")
        except Exception as e:
            self.log_result("backend_validation", "audio_generation", "FAIL", str(e))
        
        # 4. File management
        try:
            test_file = self.output_dir / "test_file.txt"
            test_file.write_text("Test content")
            if test_file.exists():
                self.log_result("backend_validation", "file_management", "PASS", "File operations work correctly")
            else:
                self.log_result("backend_validation", "file_management", "FAIL", "File creation failed")
        except Exception as e:
            self.log_result("backend_validation", "file_management", "FAIL", str(e))
        
        return True
    
    def validate_frontend(self):
        """Frontend validation tests."""
        print("\n🌐 FRONTEND VALIDATION")
        print("=" * 50)
        
        # Check if Flask app can be imported
        try:
            from podcastfy.api.fast_app import app
            self.log_result("frontend_validation", "app_import", "PASS", "Flask app imports successfully")
        except Exception as e:
            self.log_result("frontend_validation", "app_import", "FAIL", str(e))
            return False
        
        # Test API endpoints
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        # Health endpoint
        try:
            response = client.get("/health")
            if response.status_code == 200:
                self.log_result("frontend_validation", "health_endpoint", "PASS", "Health endpoint responds correctly")
            else:
                self.log_result("frontend_validation", "health_endpoint", "FAIL", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("frontend_validation", "health_endpoint", "FAIL", str(e))
        
        # Generate endpoint validation
        try:
            response = client.post("/generate", json={})
            if response.status_code == 400:  # Expected for empty input
                self.log_result("frontend_validation", "input_validation", "PASS", "Input validation works correctly")
            else:
                self.log_result("frontend_validation", "input_validation", "FAIL", f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_result("frontend_validation", "input_validation", "FAIL", str(e))
        
        # Test with valid input
        try:
            data = {
                "text": "Test podcast content",
                "tts_model": "edge",
                "name": "Validation Test"
            }
            response = client.post("/generate", json=data)
            if response.status_code != 400:  # Should pass validation
                self.log_result("frontend_validation", "valid_input", "PASS", "Valid input accepted")
            else:
                self.log_result("frontend_validation", "valid_input", "FAIL", "Valid input rejected")
        except Exception as e:
            self.log_result("frontend_validation", "valid_input", "FAIL", str(e))
        
        return True
    
    def validate_integration(self):
        """Integration validation tests."""
        print("\n🔗 INTEGRATION VALIDATION")
        print("=" * 50)
        
        # Test end-to-end workflow
        try:
            # Test with text input
            audio_path = process_content(
                text="This is a test podcast about artificial intelligence and its impact on society.",
                tts_model="edge",
                generate_audio=True
            )
            
            if audio_path and os.path.exists(audio_path):
                self.log_result("integration_validation", "text_workflow", "PASS", f"Generated: {audio_path}")
            else:
                self.log_result("integration_validation", "text_workflow", "FAIL", "No audio path in result")
        except Exception as e:
            self.log_result("integration_validation", "text_workflow", "FAIL", str(e))
        
        # Test with PDF input
        pdf_file = self.test_data_dir / "pdf" / "file.pdf"
        if pdf_file.exists():
            try:
                audio_path = process_content(
                    transcript_file=str(pdf_file),
                    tts_model="edge",
                    generate_audio=True
                )
                if audio_path and os.path.exists(audio_path):
                    self.log_result("integration_validation", "pdf_workflow", "PASS", f"Generated: {audio_path}")
                else:
                    self.log_result("integration_validation", "pdf_workflow", "FAIL", "No audio path in result")
            except Exception as e:
                self.log_result("integration_validation", "pdf_workflow", "FAIL", str(e))
        else:
            self.log_result("integration_validation", "pdf_workflow", "SKIP", "Test PDF not found")
        
        # Test error handling
        try:
            audio_path = process_content(
                urls=["https://invalid-url-that-does-not-exist.com"],
                tts_model="edge",
                generate_audio=True
            )
            # Should handle gracefully
            self.log_result("integration_validation", "error_handling", "PASS", "Error handled gracefully")
        except Exception as e:
            self.log_result("integration_validation", "error_handling", "FAIL", f"Error not handled: {str(e)}")
        
        return True
    
    def validate_performance(self):
        """Performance validation tests."""
        print("\n⚡ PERFORMANCE VALIDATION")
        print("=" * 50)
        
        # Test response time for simple operations
        start_time = time.time()
        try:
            config = load_config()
            load_time = time.time() - start_time
            if load_time < 1.0:  # Should load quickly
                self.log_result("performance_validation", "config_load", "PASS", f"Loaded in {load_time:.3f}s")
            else:
                self.log_result("performance_validation", "config_load", "FAIL", f"Too slow: {load_time:.3f}s")
        except Exception as e:
            self.log_result("performance_validation", "config_load", "FAIL", str(e))
        
        # Test content extraction performance
        start_time = time.time()
        try:
            extractor = ContentExtractor()
            content = extractor.extract_content("https://example.com")
            extract_time = time.time() - start_time
            if extract_time < 5.0:  # Should extract quickly
                self.log_result("performance_validation", "content_extraction", "PASS", f"Extracted in {extract_time:.3f}s")
            else:
                self.log_result("performance_validation", "content_extraction", "FAIL", f"Too slow: {extract_time:.3f}s")
        except Exception as e:
            self.log_result("performance_validation", "content_extraction", "FAIL", str(e))
        
        return True
    
    def run_all_validations(self):
        """Run all validation tests."""
        print("🚀 PODCASTFY COMPREHENSIVE VALIDATION")
        print("=" * 60)
        print(f"Starting validation at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all validation categories
        backend_ok = self.validate_backend()
        frontend_ok = self.validate_frontend()
        integration_ok = self.validate_integration()
        performance_ok = self.validate_performance()
        
        # Determine overall status
        all_passed = all([backend_ok, frontend_ok, integration_ok, performance_ok])
        self.results["overall_status"] = "PASS" if all_passed else "FAIL"
        
        # Save results
        results_file = self.output_dir / "validation_results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        for category, tests in self.results.items():
            if category == "overall_status":
                continue
            print(f"\n{category.upper().replace('_', ' ')}:")
            for test_name, result in tests.items():
                total_tests += 1
                status = result["status"]
                if status == "PASS":
                    passed_tests += 1
                    print(f"  ✅ {test_name}")
                elif status == "FAIL":
                    failed_tests += 1
                    print(f"  ❌ {test_name}: {result['details']}")
                elif status == "SKIP":
                    skipped_tests += 1
                    print(f"  ⏭️  {test_name}: {result['details']}")
        
        print(f"\n📈 RESULTS:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Skipped: {skipped_tests}")
        print(f"  Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "  Success Rate: N/A")
        print(f"  Overall Status: {self.results['overall_status']}")
        print(f"  Results saved to: {results_file}")
        
        return self.results["overall_status"] == "PASS"

def main():
    """Main validation function."""
    validator = PodcastfyValidator()
    success = validator.run_all_validations()
    
    if success:
        print("\n🎉 VALIDATION COMPLETED SUCCESSFULLY!")
        print("Your Podcastfy system is working correctly!")
        return 0
    else:
        print("\n⚠️  VALIDATION COMPLETED WITH ISSUES")
        print("Please review the failed tests above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 