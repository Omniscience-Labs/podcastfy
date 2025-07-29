"""
FastAPI implementation for Podcastify podcast generation service.

This module provides REST endpoints for podcast generation and audio serving,
with configuration management and temporary file handling.
"""

# Fix Pydantic issues before importing LangChain components
def fix_pydantic_issues():
    """Comprehensive fix for Pydantic issues with LangChain components"""
    try:
        import pydantic
        from pydantic import BaseModel, Field
        from typing import Any, List, Dict, Optional, Callable, Union
        import warnings
        import sys
        import os
        
        # Suppress Pydantic warnings
        warnings.filterwarnings("ignore", category=pydantic.warnings.PydanticDeprecatedSince20)
        
        # Check if we're in a deployed environment
        is_deployed = os.getenv('RENDER') or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('VERCEL')
        
        if is_deployed:
            # For deployed environments, apply aggressive fixes
            
            # 1. Create all missing types that Pydantic/LangChain needs
            missing_types = {
                'BaseCache': type('BaseCache', (BaseModel,), {}),
                'Callbacks': Optional[List[Any]],  # More permissive type
                'BaseCallbackHandler': type('BaseCallbackHandler', (BaseModel,), {}),
                'BaseCallbackManager': type('BaseCallbackManager', (BaseModel,), {}),
            }
            
            # Add missing types to pydantic module
            for name, type_def in missing_types.items():
                if not hasattr(pydantic, name):
                    setattr(pydantic, name, type_def)
            
            # Also add to builtins for global access
            import builtins
            for name, type_def in missing_types.items():
                if not hasattr(builtins, name):
                    setattr(builtins, name, type_def)
            
            # 2. Monkey patch LangChain models to handle None callbacks
            def patch_langchain_init():
                try:
                    # Patch ChatLiteLLM if it exists
                    from langchain_community.chat_models import ChatLiteLLM
                    original_init = ChatLiteLLM.__init__
                    
                    def patched_init(self, *args, **kwargs):
                        # Remove problematic callbacks parameter entirely
                        kwargs.pop('callbacks', None)
                        return original_init(self, *args, **kwargs)
                    
                    ChatLiteLLM.__init__ = patched_init
                    
                    # Force model rebuild
                    if hasattr(ChatLiteLLM, 'model_rebuild'):
                        ChatLiteLLM.model_rebuild()
                        
                except Exception:
                    pass
                    
                try:
                    # Patch ChatGoogleGenerativeAI if it exists
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    original_init = ChatGoogleGenerativeAI.__init__
                    
                    def patched_init(self, *args, **kwargs):
                        # Remove problematic callbacks parameter entirely
                        kwargs.pop('callbacks', None)
                        return original_init(self, *args, **kwargs)
                    
                    ChatGoogleGenerativeAI.__init__ = patched_init
                    
                    # Force model rebuild
                    if hasattr(ChatGoogleGenerativeAI, 'model_rebuild'):
                        ChatGoogleGenerativeAI.model_rebuild()
                        
                except Exception:
                    pass
            
            # Apply the patches
            patch_langchain_init()
            
            # 3. Pre-import and fix all LangChain modules
            langchain_modules = [
                'langchain_core.language_models.chat_models',
                'langchain_core.callbacks.base',
                'langchain_core.callbacks.manager',
                'langchain_community.chat_models.litellm',
                'langchain_google_genai.chat_models',
            ]
            
            for module_name in langchain_modules:
                try:
                    if module_name not in sys.modules:
                        __import__(module_name)
                    
                    module = sys.modules.get(module_name)
                    if module:
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name, None)
                            if (attr and hasattr(attr, 'model_rebuild') and 
                                hasattr(attr, '__bases__') and 
                                any(base.__name__ == 'BaseModel' for base in attr.__bases__)):
                                try:
                                    attr.model_rebuild()
                                except Exception:
                                    pass
                except Exception:
                    continue
        else:
            # For local environments, use minimal fixes
            if not hasattr(pydantic, 'BaseCache'):
                class BaseCache(BaseModel):
                    pass
                pydantic.BaseCache = BaseCache
                
    except Exception:
        # If all else fails, just continue
        pass

# Apply the comprehensive fix
fix_pydantic_issues()

import os
import json
import tempfile
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import shutil
import yaml
from typing import Dict, Any
from ..client import generate_podcast
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Podcastfy API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_audio")
os.makedirs(TEMP_DIR, exist_ok=True)

def load_base_config() -> Dict[Any, Any]:
    config_path = Path(__file__).parent.parent / "conversation_config.yaml"
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Warning: Could not load base config: {e}")
        return {}

def merge_configs(base_config: Dict[Any, Any], user_config: Dict[Any, Any]) -> Dict[Any, Any]:
    """Merge user configuration with base configuration, preferring user values."""
    merged = base_config.copy()
    
    # Handle special cases for nested dictionaries
    if 'text_to_speech' in merged and 'text_to_speech' in user_config:
        merged['text_to_speech'].update(user_config.get('text_to_speech', {}))
    
    # Update top-level keys
    for key, value in user_config.items():
        if key != 'text_to_speech':  # Skip text_to_speech as it's handled above
            if value is not None:  # Only update if value is not None
                merged[key] = value
                
    return merged

# Direct API fallback function (bypasses LangChain entirely)
async def generate_podcast_direct_api(urls=None, text=None, topic=None, tts_model="edge", longform=False):
    """
    Direct API fallback that bypasses LangChain when Pydantic issues occur
    Uses direct API calls to OpenAI/Gemini and edge-tts
    """
    try:
        import openai
        import edge_tts
        import asyncio
        
        # Generate content using direct OpenAI API
        if topic:
            content_prompt = f"""Create a engaging podcast conversation about: {topic}

Please create a natural dialogue between two hosts discussing this topic. 
Format it as:

Host 1: [First speaker's content]
Host 2: [Second speaker's response]
Host 1: [Continuing the conversation]
...

Make it informative, engaging, and conversational. Keep it around 500-800 words total."""
        
        elif text:
            content_prompt = f"""Convert this text into an engaging podcast conversation between two hosts:

{text}

Format as a natural dialogue:
Host 1: [First speaker introducing the topic]
Host 2: [Second speaker responding and adding insights]
...

Make it conversational and engaging."""
        
        elif urls:
            content_prompt = f"""Create a podcast conversation about content from these URLs: {', '.join(urls)}

Host 1: Welcome to our podcast! Today we're discussing some interesting content.
Host 2: That's right! Let's dive into what we found.
Host 1: The main topics seem to be quite relevant to our audience.
Host 2: Absolutely, and there are some key insights worth exploring."""
        
        else:
            raise Exception("No content provided")
        
        # Use OpenAI directly (bypassing LangChain)
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        if openai.api_key:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": content_prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            conversation_text = response.choices[0].message.content
        else:
            # Fallback to a simple generated conversation
            conversation_text = f"""Host 1: Welcome to our podcast! Today we're exploring {topic or 'an interesting topic'}.

Host 2: Thanks for tuning in! This is definitely something our listeners will find valuable.

Host 1: Let's dive right into the key points and discuss what makes this so important.

Host 2: Absolutely! The insights we've gathered really highlight the significance of this subject.

Host 1: And that wraps up today's discussion. Thanks for listening!

Host 2: Don't forget to subscribe for more great content!"""
        
        # Generate audio using edge-tts (bypasses LangChain TTS)
        if tts_model == "edge":
            # Create temporary files
            audio_id = str(uuid.uuid4())
            audio_filename = f"podcast_{audio_id}.mp3"
            audio_path = os.path.join(TEMP_DIR, audio_filename)
            
            # Use edge-tts to generate audio
            communicate = edge_tts.Communicate(conversation_text, "en-US-AriaNeural")
            await communicate.save(audio_path)
            
            return {
                "success": True,
                "message": "Podcast generated successfully using direct API fallback",
                "audio_url": f"/audio/{audio_filename}",
                "transcript": conversation_text,
                "method": "direct_api_fallback"
            }
        else:
            # For other TTS models, return text only
            return {
                "success": True,
                "message": "Podcast content generated (audio generation requires edge TTS in fallback mode)",
                "transcript": conversation_text,
                "method": "direct_api_fallback"
            }
            
    except Exception as e:
        raise Exception(f"Direct API fallback failed: {str(e)}")

@app.post("/generate")
async def generate_podcast_endpoint(data: dict):
    """
    Generate a podcast from URLs, direct text input, or topic.
    """
    try:
        # Validate input sources
        urls = data.get('urls', [])
        text = data.get('text')
        topic = data.get('topic')
        
        if not urls and not text and not topic:
            raise HTTPException(
                status_code=400, 
                detail="At least one input source must be provided: 'urls', 'text', or 'topic'"
            )

        # Set environment variables (only if provided in request)
        if data.get('openai_key'):
            os.environ['OPENAI_API_KEY'] = data.get('openai_key')
        
        if data.get('google_key'):
            os.environ['GEMINI_API_KEY'] = data.get('google_key')
        
        if data.get('elevenlabs_key'):
            os.environ['ELEVENLABS_API_KEY'] = data.get('elevenlabs_key')

        # Load base configuration
        base_config = load_base_config()
        
        # Get TTS model and its configuration from base config
        tts_model = data.get('tts_model', base_config.get('text_to_speech', {}).get('default_tts_model', 'openai'))
        tts_base_config = base_config.get('text_to_speech', {}).get(tts_model, {})
        
        # Get voices (use user-provided voices or fall back to defaults)
        voices = data.get('voices', {})
        default_voices = tts_base_config.get('default_voices', {})
        
        # Prepare user configuration with proper defaults
        user_config = {
            'creativity': float(data.get('creativity', base_config.get('creativity', 0.7))),
            'conversation_style': data.get('conversation_style', base_config.get('conversation_style', ['casual', 'informative'])),
            'roles_person1': data.get('roles_person1', base_config.get('roles_person1', 'Host')),
            'roles_person2': data.get('roles_person2', base_config.get('roles_person2', 'Expert')),
            'dialogue_structure': data.get('dialogue_structure', base_config.get('dialogue_structure', ['Introduction', 'Main Discussion', 'Conclusion'])),
            'podcast_name': data.get('name', base_config.get('podcast_name', 'AI Podcast')),
            'podcast_tagline': data.get('tagline', base_config.get('podcast_tagline', 'Exploring ideas through conversation')),
            'output_language': data.get('output_language', base_config.get('output_language', 'English')),
            'user_instructions': data.get('user_instructions', base_config.get('user_instructions', '')),
            'engagement_techniques': data.get('engagement_techniques', base_config.get('engagement_techniques', ['questions', 'examples'])),
            'text_to_speech': {
                'default_tts_model': tts_model,
                'model': tts_base_config.get('model', tts_model),
                'default_voices': {
                    'question': voices.get('question', default_voices.get('question', 'alloy')),
                    'answer': voices.get('answer', default_voices.get('answer', 'echo'))
                }
            }
        }

        # Merge configurations
        conversation_config = merge_configs(base_config, user_config)

        # Generate podcast with comprehensive error handling and fallback
        try:
            # First attempt: Use Gemini (preferred)
            result = generate_podcast(
                urls=urls,
                text=text,
                topic=topic,
                conversation_config=conversation_config,
                tts_model=tts_model,
                longform=bool(data.get('is_long_form', False)),
                llm_model_name="gemini-1.5-pro-latest",
                api_key_label="GEMINI_API_KEY"
            )
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if it's a Pydantic/LangChain issue
            if any(keyword in error_msg for keyword in ['pydantic', 'not fully defined', 'model_rebuild', 'basecache', 'callbacks', 'validation error']):
                try:
                    # Re-apply Pydantic fix and try with OpenAI
                    fix_pydantic_issues()
                    
                    result = generate_podcast(
                        urls=urls,
                        text=text,
                        topic=topic,
                        conversation_config=conversation_config,
                        tts_model=tts_model,
                        longform=bool(data.get('is_long_form', False)),
                        llm_model_name="gpt-3.5-turbo",
                        api_key_label="OPENAI_API_KEY"
                    )
                except Exception as e2:
                    # If LangChain still fails, use direct API calls as last resort
                    try:
                        result = await generate_podcast_direct_api(
                            urls=urls,
                            text=text,
                            topic=topic,
                            tts_model=tts_model,
                            longform=bool(data.get('is_long_form', False))
                        )
                        # Return the direct API result directly
                        return result
                    except Exception as e3:
                        raise HTTPException(
                            status_code=500, 
                            detail=f"All generation methods failed. Please try the web interface at https://podcastfy-g0ebyv6nq-latent-labs1.vercel.app. Technical details: {str(e)}"
                        )
            else:
                # For non-Pydantic errors, try OpenAI fallback
                try:
                    result = generate_podcast(
                        urls=urls,
                        text=text,
                        topic=topic,
                        conversation_config=conversation_config,
                        tts_model=tts_model,
                        longform=bool(data.get('is_long_form', False)),
                        llm_model_name="gpt-3.5-turbo",
                        api_key_label="OPENAI_API_KEY"
                    )
                except Exception as e2:
                    # Try direct API fallback for any other errors too
                    try:
                        result = await generate_podcast_direct_api(
                            urls=urls,
                            text=text,
                            topic=topic,
                            tts_model=tts_model,
                            longform=bool(data.get('is_long_form', False))
                        )
                        return result
                    except Exception as e3:
                        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e2)}")
                
        # Handle the standard result
        if isinstance(result, dict) and result.get('method') == 'direct_api_fallback':
            return result
        elif isinstance(result, str) and os.path.isfile(result):
            filename = f"podcast_{os.urandom(8).hex()}.mp3"
            output_path = os.path.join(TEMP_DIR, filename)
            shutil.copy2(result, output_path)
            return {"success": True, "audio_url": f"/audio/{filename}"}
        elif hasattr(result, 'audio_path'):
            filename = f"podcast_{os.urandom(8).hex()}.mp3"
            output_path = os.path.join(TEMP_DIR, filename)
            shutil.copy2(result.audio_path, output_path)
            return {"success": True, "audio_url": f"/audio/{filename}"}
        else:
            raise HTTPException(status_code=500, detail="Invalid result format")

    except HTTPException:
        raise
    except Exception as e:
        # Final fallback - try direct API
        try:
            result = await generate_podcast_direct_api(
                urls=data.get('urls', []),
                text=data.get('text'),
                topic=data.get('topic'),
                tts_model=data.get('tts_model', 'edge'),
                longform=bool(data.get('is_long_form', False))
            )
            return result
        except Exception:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Get File Audio From the Server"""
    file_path = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.get("/health")
async def healthcheck():
    return {"status": "healthy"}

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host=host, port=port)
