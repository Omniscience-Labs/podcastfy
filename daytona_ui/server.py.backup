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

# 🟢 ROBUST PATH HANDLING: Always resolve paths relative to project root
# Get the project root (podcastfy directory) - works from any working directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DAYTONA_UI_DIR = Path(__file__).parent.resolve()

# Add podcastfy to Python path
sys.path.insert(0, str(PROJECT_ROOT))

# Import pydub patch before any pydub imports
from pydub_patch import *

from flask import Flask, request, jsonify, send_from_directory, render_template_string, send_file
from flask_cors import CORS
import subprocess
import tempfile
import shutil

from podcastfy.client import generate_podcast
from podcastfy.utils.image_processor import ImageProcessor

app = Flask(__name__)
CORS(app)  # Enable CORS for development

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🟢 PROJECT-ROOT-RELATIVE PATHS: Always relative to project root, never current working directory
UPLOAD_DIR = DAYTONA_UI_DIR / "uploads"
AUDIO_DIR = PROJECT_ROOT / "data" / "audio"
TRANSCRIPT_DIR = PROJECT_ROOT / "data" / "transcripts"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
AUDIO_DIR.mkdir(exist_ok=True, parents=True)
TRANSCRIPT_DIR.mkdir(exist_ok=True, parents=True)

logger.info(f"📁 Project root: {PROJECT_ROOT}")
logger.info(f"📁 Daytona UI dir: {DAYTONA_UI_DIR}")
logger.info(f"📁 Upload dir: {UPLOAD_DIR}")
logger.info(f"📁 Audio dir: {AUDIO_DIR}")
logger.info(f"📁 Transcript dir: {TRANSCRIPT_DIR}")

def generate_podcast_with_transcript(**kwargs):
    """
    Generate both podcast audio and transcript, ensuring both are created.
    Returns a tuple of (audio_file_path, transcript_file_path)
    """
    from podcastfy.content_parser.content_extractor import ContentExtractor
    from podcastfy.content_generator import ContentGenerator
    from podcastfy.text_to_speech import TextToSpeech
    from podcastfy.utils.config import load_config
    from podcastfy.utils.config_conversation import load_conversation_config
    import uuid
    import os
    try:
        config = load_config()
        conv_config = load_conversation_config()
        tts_config = conv_config.get("text_to_speech", {})
        output_directories = tts_config.get("output_directories", {})
        audio_dir = os.path.join(PROJECT_ROOT, output_directories.get("audio", "data/audio"))
        transcript_dir = os.path.join(PROJECT_ROOT, output_directories.get("transcripts", "data/transcripts"))
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(transcript_dir, exist_ok=True)
        urls = kwargs.get('urls', [])
        text = kwargs.get('text', '')
        topic = kwargs.get('topic', '')
        tts_model = kwargs.get('tts_model', 'edge')
        longform = kwargs.get('longform', False)
        is_local = kwargs.get('is_local', False)
        model_name = kwargs.get('llm_model_name')
        api_key_label = kwargs.get('api_key_label')
        generation_id = uuid.uuid4().hex
        # Step 1: Generate transcript first
        logger.info("Step 1: Generating transcript...")
        content_extractor = None
        if urls or topic or (text and longform and len(text.strip()) < 100):
            content_extractor = ContentExtractor()
        content_generator = ContentGenerator(
            is_local=is_local,
            model_name=model_name,
            api_key_label=api_key_label,
            conversation_config=conv_config.to_dict()
        )
        combined_content = ""
        if urls:
            logger.info(f"Processing {len(urls)} links")
            contents = [content_extractor.extract_content(link) for link in urls]
            combined_content += "\n\n".join(contents)
        if text:
            if longform and len(text.strip()) < 100:
                logger.info("Text too short for direct long-form generation. Extracting context...")
                expanded_content = content_extractor.generate_topic_content(text)
                combined_content += f"\n\n{expanded_content}"
            else:
                combined_content += f"\n\n{text}"
        if topic:
            topic_content = content_extractor.generate_topic_content(topic)
            combined_content += f"\n\n{topic_content}"
        transcript_filename = f"transcript_{generation_id}.txt"
        transcript_filepath = os.path.join(transcript_dir, transcript_filename)
        qa_content = content_generator.generate_qa_content(
            combined_content,
            image_file_paths=kwargs.get('image_paths', []),
            output_filepath=transcript_filepath,
            longform=longform
        )
        logger.info(f"Transcript generated: {transcript_filepath}")
        # Step 2: Generate audio from the transcript
        logger.info("Step 2: Generating audio from transcript...")
        api_key = None
        if tts_model != "edge":
            api_key = getattr(config, f"{tts_model.upper().replace('MULTI', '')}_API_KEY")
        text_to_speech = TextToSpeech(
            model=tts_model,
            api_key=api_key,
            conversation_config=conv_config.to_dict(),
        )
        audio_filename = f"podcast_{generation_id}.mp3"
        audio_filepath = os.path.join(audio_dir, audio_filename)
        text_to_speech.convert_to_speech(qa_content, audio_filepath)
        logger.info(f"Audio generated: {audio_filepath}")
        return audio_filepath, transcript_filepath
    except Exception as e:
        logger.error(f"Error in generate_podcast_with_transcript: {str(e)}")
        raise

@app.route('/')
def index():
    """Serve the main web interface."""
    return send_from_directory(DAYTONA_UI_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, etc.)."""
    return send_from_directory(DAYTONA_UI_DIR, filename)

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
        # Handle both JSON and FormData
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle FormData (for file uploads)
            data_str = request.form.get('data')
            if not data_str:
                return jsonify({"success": False, "error": "No data provided"}), 400
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                return jsonify({"success": False, "error": "Invalid JSON data"}), 400
        else:
            # Handle regular JSON
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
        
        logger.info(f"Calling generate_podcast_with_transcript with args: {podcast_args}")
        
        # Generate podcast
        try:
            audio_filepath, transcript_filepath = generate_podcast_with_transcript(**podcast_args)
            audio_filename = Path(audio_filepath).name
            transcript_filename = Path(transcript_filepath).name
            response = {
                "success": True,
                "audio_url": f"/api/audio/{audio_filename}",
                "transcript_url": f"/api/transcript/{transcript_filename}",
                "filename": audio_filename,
                "message": "Podcast and transcript generated successfully!"
            }
            logger.info(f"Podcast generated successfully: {audio_filename}")
            logger.info(f"Transcript generated successfully: {transcript_filename}")
            logger.info(f"Audio URL: {response['audio_url']}")
            logger.info(f"Transcript URL: {response['transcript_url']}")
            return jsonify(response)
        except Exception as e:
            logger.error(f"Error in generate_podcast_with_transcript: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"Failed to generate podcast: {str(e)}"
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
    # Dynamically resolve the absolute path
    file_path = (TRANSCRIPT_DIR / filename).resolve()
    if not file_path.exists():
        logger.error(f"Transcript file not found: {file_path}")
        return jsonify({"error": "Transcript file not found"}), 404
    logger.info(f"Transcript file found, serving: {file_path}")
    return send_file(str(file_path), mimetype='text/plain')

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
    print(f"📁 Project root: {PROJECT_ROOT}")
    print(f"📁 Daytona UI directory: {DAYTONA_UI_DIR}")
    print(f"📁 Current working directory: {os.getcwd()}")
    print("🌐 Web interface available at: http://localhost:5001")
    print("🔧 API available at: http://localhost:5001/api")
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,  # Disable debug mode to avoid restart issues
        threaded=True
    ) 