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

# Configure CORS for frontend
CORS(app, origins=[
    "https://podcastfy-opxm6bilx-latent-labs1.vercel.app",  # Production Vercel URL
    "https://podcastfy-3iyy3vo66-latent-labs1.vercel.app",  # Preview Vercel URL
    "http://localhost:3000",  # Local development
    "http://localhost:5000",  # Local development
    "http://127.0.0.1:5500",  # Live Server
    "http://localhost:8080",  # Common dev server
    "null"  # File protocol for local HTML files
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

@app.route('/', methods=['GET'])
def root():
    """Root endpoint - API information"""
    return jsonify({
        'service': 'Podcastfy Backend API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'generate': '/api/generate',
            'audio': '/api/audio/<filename>',
            'transcript': '/api/transcript/<filename>'
        },
        'frontend': 'https://podcastfy-opxm6bilx-latent-labs1.vercel.app'
    })

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
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            pdf_files = []
            image_files = []
        else:
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
        
        # Call the podcast generation function with the first content source
        # For now, we'll use the first text content or topic
        text_content = None
        topic_content = None
        urls_list = []
        
        for source in content_sources:
            if source.startswith('http'):
                urls_list.append(source)
            elif len(source) > 100:  # Likely text content
                text_content = source
            else:  # Likely topic
                topic_content = source
        
        # Call generate_podcast with appropriate parameters
        # Temporarily use a different model to avoid Google AI issues
        result = generate_podcast(
            urls=urls_list if urls_list else None,
            text=text_content,
            topic=topic_content,
            tts_model=data.get('tts_model', 'en-US-Neural2-F'),
            llm_model_name="gpt-3.5-turbo",  # Use OpenAI instead of Gemini
            api_key_label="OPENAI_API_KEY"   # Use OpenAI API key
        )
        
        if result:
            # Handle different result types
            if isinstance(result, str):
                # Result is a file path
                audio_file = result
                # Try to find the corresponding transcript file
                try:
                    # Look for the most recent transcript file
                    transcript_files = list(TRANSCRIPT_DIR.glob("*.txt"))
                    if transcript_files:
                        # Get the most recent transcript file
                        latest_transcript = max(transcript_files, key=os.path.getctime)
                        with open(latest_transcript, 'r') as f:
                            transcript = f.read()
                    else:
                        transcript = "Transcript not available"
                except Exception as e:
                    logger.warning(f"Could not load transcript: {e}")
                    transcript = "Transcript not available"
            elif isinstance(result, dict) and result.get('audio_file'):
                # Result is a dictionary with audio_file
                audio_file = result['audio_file']
                transcript = result.get('transcript', 'No transcript available')
            elif hasattr(result, 'audio_path'):
                # Result is an object with audio_path attribute
                audio_file = result.audio_path
                transcript = getattr(result, 'transcript', 'No transcript available')
            else:
                return jsonify({'success': False, 'error': 'Invalid result format'}), 500
            
            # Create response with absolute file URLs
            audio_filename = Path(audio_file).name
            transcript_filename = f"{uuid.uuid4()}.txt"
            
            # Get the base URL from the request
            base_url = request.host_url.rstrip('/')
            audio_url = f"{base_url}/api/audio/{audio_filename}"
            transcript_url = f"{base_url}/api/transcript/{transcript_filename}"
            
            # Save transcript
            transcript_path = TRANSCRIPT_DIR / transcript_filename
            with open(transcript_path, 'w') as f:
                f.write(str(transcript))
            
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

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
