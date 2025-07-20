#!/usr/bin/env python3
"""
Podcastfy Backend API Server

This server provides API endpoints for podcast generation.
Frontend is deployed separately on Vercel.
"""

import os
import sys
import json
import uuid
import logging
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import tempfile
import shutil

# Get the project root (podcastfy directory) - works from any working directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BACKEND_DIR = Path(__file__).parent.resolve()

# Add podcastfy to Python path
sys.path.insert(0, str(PROJECT_ROOT))

# Import pydub patch before importing pydub
try:
    from backend.pydub_patch import *
except ImportError:
    # If we can't import from backend, try to create the patch inline
    import sys
    import warnings
    
    # Create a dummy audioop module if it doesn't exist
    try:
        import audioop
    except ImportError:
        # Create a dummy module
        class DummyAudioop:
            def __getattr__(self, name):
                def dummy_function(*args, **kwargs):
                    warnings.warn(f"audioop.{name} is not available in Python 3.13+", RuntimeWarning)
                    return None
                return dummy_function
        
        # Create a dummy module
        import types
        audioop = types.ModuleType('audioop')
        audioop.__dict__.update(DummyAudioop().__dict__)
        
        # Add it to sys.modules so pydub can import it
        sys.modules['audioop'] = audioop

    # Also handle pyaudioop
    try:
        import pyaudioop
    except ImportError:
        sys.modules['pyaudioop'] = audioop

from podcastfy.client import generate_podcast
from podcastfy.utils.image_processor import ImageProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure CORS for Vercel frontend
CORS(app, origins=[
    "https://your-vercel-frontend.vercel.app",  # Update with your Vercel URL
    "http://localhost:3000",  # Local development
    "http://localhost:5000"   # Local development
])

# Vercel-specific configuration
if os.environ.get("VERCEL"):
    # Running on Vercel - use temporary storage
    UPLOAD_DIR = Path("/tmp/uploads")
    AUDIO_DIR = Path("/tmp/audio")
    TRANSCRIPT_DIR = Path("/tmp/transcripts")
else:
    # Local development - use project directories
    UPLOAD_DIR = BACKEND_DIR / "uploads"
    AUDIO_DIR = PROJECT_ROOT / "data" / "audio"
    TRANSCRIPT_DIR = PROJECT_ROOT / "data" / "transcripts"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'podcastfy-backend',
        'version': '1.0.0'
    })

@app.route('/api/generate', methods=['POST'])
def generate_podcast_api():
    """Generate podcast from various content sources"""
    try:
        # Check if request has content
        if not request.form and not request.files:
            return jsonify({'success': False, 'error': 'No content provided'}), 400
        
        # Parse JSON data
        data = json.loads(request.form.get('data', '{}'))
        
        # Handle file uploads
        pdf_files = request.files.getlist('pdf_files')
        image_files = request.files.getlist('image_files')
        
        # Save uploaded files
        saved_files = []
        
        for file in pdf_files + image_files:
            if file.filename:
                filename = f"{uuid.uuid4()}_{file.filename}"
                file_path = UPLOAD_DIR / filename
                file.save(file_path)
                saved_files.append(str(file_path))
        
        # Prepare content sources
        content_sources = []
        
        if data.get('urls'):
            content_sources.extend(data['urls'])
        
        if data.get('text'):
            content_sources.append(data['text'])
        
        if data.get('topic'):
            content_sources.append(data['topic'])
        
        if saved_files:
            content_sources.extend(saved_files)
        
        if not content_sources:
            return jsonify({'success': False, 'error': 'No valid content provided'}), 400
        
        # Generate podcast
        logger.info(f"Generating podcast from {len(content_sources)} sources")
        
        # Call the podcast generation function
        result = generate_podcast(
            content_source=content_sources,
            voice=data.get('tts_model', 'en-US-Neural2-F'),
            language='en',
            output_dir=str(AUDIO_DIR)
        )
        
        if result and result.get('audio_file'):
            audio_file = result['audio_file']
            transcript = result.get('transcript', 'No transcript available')
            
            # Create response with file URLs
            audio_url = f"/api/audio/{Path(audio_file).name}"
            transcript_url = f"/api/transcript/{uuid.uuid4()}.txt"
            
            # Save transcript
            transcript_path = TRANSCRIPT_DIR / f"{uuid.uuid4()}.txt"
            with open(transcript_path, 'w') as f:
                f.write(transcript)
            
            return jsonify({
                'success': True,
                'audio_url': audio_url,
                'transcript_url': transcript_url,
                'message': 'Podcast generated successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to generate podcast'}), 500
            
    except Exception as e:
        logger.error(f"Error generating podcast: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    """Serve generated audio files"""
    try:
        audio_path = AUDIO_DIR / filename
        if audio_path.exists():
            return send_file(audio_path, mimetype='audio/mpeg')
        else:
            return jsonify({'error': 'Audio file not found'}), 404
    except Exception as e:
        logger.error(f"Error serving audio: {str(e)}")
        return jsonify({'error': 'Error serving audio file'}), 500

@app.route('/api/transcript/<filename>', methods=['GET'])
def serve_transcript(filename):
    """Serve generated transcript files"""
    try:
        transcript_path = TRANSCRIPT_DIR / filename
        if transcript_path.exists():
            return send_file(transcript_path, mimetype='text/plain')
        else:
            return jsonify({'error': 'Transcript file not found'}), 404
    except Exception as e:
        logger.error(f"Error serving transcript: {str(e)}")
        return jsonify({'error': 'Error serving transcript file'}), 500

# Export the Flask app for Vercel
app.debug = False
