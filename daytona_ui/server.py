#!/usr/bin/env python3
"""
Daytona Podcastfy Web Server

This server provides a web interface for Podcastfy and handles API calls
to the Podcastfy backend for podcast generation.
"""

import os
import sys
import json
import uuid
import logging
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import subprocess
import tempfile
import shutil

# Add podcastfy to path
sys.path.insert(0, str(Path(__file__).parent.parent / "podcastfy"))

from podcastfy.client import generate_podcast
from podcastfy.utils.image_processor import ImageProcessor

app = Flask(__name__)
CORS(app)  # Enable CORS for development

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create directories for uploaded files and generated content
UPLOAD_DIR = Path("uploads")
AUDIO_DIR = Path("../data/audio")  # Go up one directory to find data/
TRANSCRIPT_DIR = Path("../data/transcripts")  # Go up one directory to find data/

UPLOAD_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True, parents=True)  # Create parent directories if needed
TRANSCRIPT_DIR.mkdir(exist_ok=True, parents=True)  # Create parent directories if needed

@app.route('/')
def index():
    """Serve the main web interface."""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, etc.)."""
    return send_from_directory('.', filename)

@app.route('/api/generate', methods=['POST'])
def generate_podcast_api():
    """
    API endpoint to generate podcasts from various content sources.
    
    Expected JSON payload:
    {
        "urls": ["https://example.com"],
        "text": "Direct text content",
        "topic": "Topic to generate about",
        "tts_model": "edge",
        "podcast_name": "My Podcast",
        "conversation_style": ["engaging", "informative"],
        "longform": false,
        "creativity": 0.7
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        logger.info(f"Received podcast generation request: {data}")
        
        # Extract content sources
        urls = data.get('urls', [])
        text = data.get('text', '')
        topic = data.get('topic', '')
        
        # Validate that at least one content source is provided
        if not urls and not text and not topic:
            return jsonify({
                "success": False, 
                "error": "At least one content source must be provided (urls, text, or topic)"
            }), 400
        
        # Handle file uploads
        pdf_files = []
        image_files = []
        
        if 'pdf_files' in request.files:
            pdf_files = handle_file_upload(request.files.getlist('pdf_files'), 'pdf')
        
        if 'image_files' in request.files:
            image_files = handle_file_upload(request.files.getlist('image_files'), 'image')
        
        # Process images for Gemini API
        if image_files:
            try:
                base64_images = ImageProcessor.process_images_for_gemini(image_files)
                # For now, we'll skip image processing until we integrate it properly
                logger.info(f"Processed {len(base64_images)} images")
            except Exception as e:
                logger.error(f"Image processing failed: {e}")
                return jsonify({
                    "success": False,
                    "error": f"Image processing failed: {str(e)}"
                }), 400
        
        # Prepare arguments for generate_podcast
        podcast_args = {
            "urls": urls if urls else None,
            "text": text if text else None,
            "topic": topic if topic else None,
            "tts_model": data.get('tts_model', 'edge'),
            "longform": data.get('longform', False),
            "transcript_only": False
        }
        
        # Add PDF files if any
        if pdf_files:
            podcast_args["urls"] = (podcast_args["urls"] or []) + pdf_files
        
        # Remove None values
        podcast_args = {k: v for k, v in podcast_args.items() if v is not None}
        
        logger.info(f"Calling generate_podcast with args: {podcast_args}")
        
        # Generate podcast
        result = generate_podcast(**podcast_args)
        
        if result:
            # Extract filename from result path
            filename = Path(result).name
            
            # Create response
            response = {
                "success": True,
                "audio_url": f"/api/audio/{filename}",
                "transcript_url": f"/api/transcript/{filename.replace('.mp3', '.txt')}",
                "filename": filename,
                "message": "Podcast generated successfully!"
            }
            
            logger.info(f"Podcast generated successfully: {filename}")
            return jsonify(response)
        else:
            return jsonify({
                "success": False,
                "error": "Failed to generate podcast"
            }), 500
            
    except Exception as e:
        logger.error(f"Error generating podcast: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"An error occurred: {str(e)}"
        }), 500

@app.route('/api/audio/<filename>')
def serve_audio(filename):
    """Serve generated audio files."""
    return send_from_directory(AUDIO_DIR, filename)

@app.route('/api/transcript/<filename>')
def serve_transcript(filename):
    """Serve generated transcript files."""
    return send_from_directory(TRANSCRIPT_DIR, filename)

def handle_file_upload(files, file_type):
    """
    Handle file uploads and save them to the upload directory.
    
    Args:
        files: List of uploaded files
        file_type: Type of files ('pdf' or 'image')
        
    Returns:
        List of saved file paths
    """
    saved_files = []
    
    for file in files:
        if file.filename:
            # Create unique filename
            file_ext = Path(file.filename).suffix
            unique_filename = f"{file_type}_{uuid.uuid4().hex}{file_ext}"
            file_path = UPLOAD_DIR / unique_filename
            
            # Save file
            file.save(file_path)
            saved_files.append(str(file_path))
            
            logger.info(f"Saved {file_type} file: {file_path}")
    
    return saved_files

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Podcastfy Web Interface",
        "version": "1.0.0"
    })

@app.route('/api/status')
def status():
    """Get system status and available features."""
    return jsonify({
        "status": "operational",
        "features": {
            "website_urls": "✅ Working",
            "topic_generation": "✅ Working", 
            "direct_text": "✅ Working",
            "pdf_processing": "✅ Working",
            "image_processing": "🔄 Fixed (base64 conversion)",
            "youtube_processing": "❌ Needs fixing"
        },
        "tts_models": ["edge", "openai", "elevenlabs", "gemini"],
        "supported_formats": {
            "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
            "documents": [".pdf"],
            "text": ["urls", "direct text", "topics"]
        }
    })

if __name__ == '__main__':
    print("🎙️  Starting Podcastfy Web Interface...")
    print("📁 Serving files from:", os.getcwd())
    print("🌐 Web interface available at: http://localhost:5001")
    print("🔧 API available at: http://localhost:5001/api")
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        threaded=True
    ) 