#!/usr/bin/env python3
"""
Podcastfy Backend API Server

This server provides API endpoints for podcast generation.
Frontend is deployed separately on Vercel.
"""

# CRITICAL: Import pydub patch FIRST before ANY other imports
import os
import sys
from pathlib import Path

# Get the project root (podcastfy directory) - works from any working directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BACKEND_DIR = Path(__file__).parent.resolve()

# Add podcastfy to Python path
sys.path.insert(0, str(PROJECT_ROOT))

# Apply pydub patch IMMEDIATELY - this must be first
print("Loading pydub patch for Python 3.13+ compatibility...")
sys.path.insert(0, str(BACKEND_DIR))

# Import pydub patch before ANY other imports including pydub
try:
    import backend.pydub_patch
    print("✅ Pydub patch loaded successfully")
except ImportError as e:
    print(f"⚠️ Pydub patch import failed: {e}")
    # Apply the patch inline as fallback
    import warnings
    import types
    import array
    import struct
    
    # Create a functional audioop module replacement for Python 3.13+
    try:
        import audioop
    except ImportError:
        class WorkingAudioop:
            """Working audioop implementation for Python 3.13+ compatibility"""
            
            @staticmethod
            def lin2lin(fragment, width, newwidth):
                """Convert samples between different widths"""
                if width == newwidth:
                    return fragment
                
                # Convert to array for processing
                if width == 1:
                    fmt = 'b'
                elif width == 2:
                    fmt = 'h'
                elif width == 4:
                    fmt = 'l'
                else:
                    raise ValueError(f"Unsupported width: {width}")
                
                if newwidth == 1:
                    newfmt = 'b'
                    maxval = 127
                elif newwidth == 2:
                    newfmt = 'h'
                    maxval = 32767
                elif newwidth == 4:
                    newfmt = 'l'
                    maxval = 2147483647
                else:
                    raise ValueError(f"Unsupported newwidth: {newwidth}")
                
                try:
                    # Convert fragment to samples
                    samples = array.array(fmt)
                    samples.frombytes(fragment)
                    
                    # Convert to new width
                    if width < newwidth:
                        # Expanding - multiply by scale factor
                        scale = maxval // (2**(width*8-1) - 1)
                        new_samples = array.array(newfmt, [min(maxval, max(-maxval-1, s * scale)) for s in samples])
                    else:
                        # Shrinking - divide by scale factor
                        scale = (2**(width*8-1) - 1) // maxval
                        new_samples = array.array(newfmt, [s // scale for s in samples])
                    
                    return new_samples.tobytes()
                except Exception:
                    # Fallback: return fragment padded or truncated
                    if newwidth > width:
                        # Pad with zeros
                        return fragment + b'\x00' * (len(fragment) * (newwidth - width) // width)
                    else:
                        # Truncate
                        return fragment[::width//newwidth]
            
            @staticmethod 
            def ratecv(fragment, width, nchannels, inrate, outrate, state, weightA=1, weightB=0):
                """Rate conversion - simplified implementation"""
                if inrate == outrate:
                    return fragment, state
                
                # Simple resampling by duplicating/skipping samples
                ratio = float(outrate) / inrate
                frame_size = width * nchannels
                frames_in = len(fragment) // frame_size
                frames_out = int(frames_in * ratio)
                
                new_fragment = bytearray()
                for i in range(frames_out):
                    src_frame = int(i / ratio)
                    if src_frame < frames_in:
                        start = src_frame * frame_size
                        end = start + frame_size
                        new_fragment.extend(fragment[start:end])
                
                return bytes(new_fragment), state
            
            @staticmethod
            def mul(fragment, width, factor):
                """Multiply amplitude by factor"""
                if width == 1:
                    fmt = 'b'
                elif width == 2:
                    fmt = 'h'  
                elif width == 4:
                    fmt = 'l'
                else:
                    return fragment
                
                try:
                    samples = array.array(fmt)
                    samples.frombytes(fragment)
                    
                    # Apply factor with clipping
                    if width == 1:
                        maxval = 127
                    elif width == 2:
                        maxval = 32767
                    else:
                        maxval = 2147483647
                    
                    new_samples = array.array(fmt, [
                        min(maxval, max(-maxval-1, int(s * factor))) for s in samples
                    ])
                    return new_samples.tobytes()
                except Exception:
                    return fragment
            
            def __getattr__(self, name):
                """Fallback for other audioop methods"""
                def safe_fallback(*args, **kwargs):
                    # Return reasonable defaults for common operations
                    if name in ['add', 'bias', 'reverse']:
                        return args[0] if args else b''
                    elif name in ['max', 'minmax']:
                        return 0
                    elif name == 'cross':
                        return len(args[0]) if args else 0
                    elif name in ['tomono', 'tostereo']:
                        return args[0] if args else b''
                    else:
                        warnings.warn(f"audioop.{name} fallback used", RuntimeWarning)
                        return args[0] if args else b''
                return safe_fallback
        
        # Create the module
        audioop = types.ModuleType('audioop')
        working_audioop = WorkingAudioop()
        
        # Add the methods to the module
        audioop.lin2lin = working_audioop.lin2lin
        audioop.ratecv = working_audioop.ratecv
        audioop.mul = working_audioop.mul
        
        # Add other common methods with fallbacks
        for attr in ['add', 'bias', 'cross', 'findfactor', 'findmax', 'getsample', 
                     'max', 'maxpp', 'minmax', 'reverse', 'rms', 'tomono', 'tostereo']:
            setattr(audioop, attr, getattr(working_audioop, attr))
        
        # Add it to sys.modules so pydub can import it
        sys.modules['audioop'] = audioop

        # Also handle pyaudioop
        try:
            import pyaudioop
        except ImportError:
            sys.modules['pyaudioop'] = audioop
        
        print("✅ Working audioop patch applied inline")

# Now import everything else
import json
import uuid
import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import tempfile
import shutil

from podcastfy.client import generate_podcast
from podcastfy.utils.image_processor import ImageProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure CORS for frontend
CORS(app, origins=[
    "https://podcastfy-azure.vercel.app",  # Current Production Vercel URL
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
            tts_model=data.get('tts_model', 'edge'),
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
        # Try multiple possible audio file locations
        possible_paths = [
            AUDIO_DIR / filename,  # Original path
            Path("./data/audio") / filename,  # Relative to working directory
            Path("/opt/render/project/src/data/audio") / filename,  # Render absolute path
            PROJECT_ROOT / "data" / "audio" / filename,  # Project root path
            Path.cwd() / "data" / "audio" / filename,  # Current working directory
            Path("/app/data/audio") / filename,  # Docker path
            Path("/tmp/audio") / filename,  # Temp path
            Path("data/audio") / filename,  # Simple relative
            BACKEND_DIR / "data" / "audio" / filename,  # Backend relative
        ]
        
        for audio_path in possible_paths:
            if audio_path.exists():
                logger.info(f"✅ Found audio file at: {audio_path}")
                return send_file(audio_path, mimetype='audio/mpeg')
        
        # Log all paths we tried for debugging
        logger.error(f"❌ Audio file not found. Tried paths:")
        for path in possible_paths:
            logger.error(f"   - {path} (exists: {path.exists()})")
        
        return jsonify({'error': 'Audio file not found'}), 404
        
    except Exception as e:
        logger.error(f"Error serving audio: {str(e)}")
        return jsonify({'error': 'Error serving audio file'}), 500

@app.route('/api/transcript/<filename>', methods=['GET'])
def serve_transcript(filename):
    """Serve generated transcript files"""
    try:
        # Try multiple possible transcript file locations
        possible_paths = [
            TRANSCRIPT_DIR / filename,  # Original path
            Path("./data/transcripts") / filename,  # Relative to working directory
            Path("/opt/render/project/src/data/transcripts") / filename,  # Render absolute path
            PROJECT_ROOT / "data" / "transcripts" / filename,  # Project root path
            Path.cwd() / "data" / "transcripts" / filename,  # Current working directory
        ]
        
        for transcript_path in possible_paths:
            if transcript_path.exists():
                logger.info(f"✅ Found transcript file at: {transcript_path}")
                return send_file(transcript_path, mimetype='text/plain')
        
        # Log paths we tried
        logger.error(f"❌ Transcript file not found. Tried paths:")
        for path in possible_paths:
            logger.error(f"   - {path} (exists: {path.exists()})")
            
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
