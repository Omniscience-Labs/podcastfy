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
    """Load base configuration from conversation_config.yaml"""
    config_path = Path(__file__).parent.parent / "conversation_config.yaml"
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.warning(f"Could not load base config: {e}")
        return {
            'creativity': 0.7,
            'conversation_style': ['casual', 'informative'],
            'roles_person1': 'Host',
            'roles_person2': 'Expert',
            'dialogue_structure': ['Introduction', 'Main Discussion', 'Conclusion'],
            'podcast_name': 'AI Podcast',
            'podcast_tagline': 'Exploring ideas through conversation',
            'output_language': 'English',
            'user_instructions': '',
            'engagement_techniques': ['questions', 'examples'],
            'text_to_speech': {
                'default_tts_model': 'edge',
                'edge': {
                    'model': 'edge',
                    'default_voices': {
                        'question': 'en-US-AriaNeural',
                        'answer': 'en-US-GuyNeural'
                    }
                }
            }
        }

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
        import requests
        from bs4 import BeautifulSoup
        
        logger.info(f"Direct API fallback: generating content for topic='{topic}', text_length={len(text) if text else 0}, urls={len(urls) if urls else 0}")
        
        # Extract content from URLs if provided
        url_content = ""
        if urls:
            for url in urls[:3]:  # Limit to first 3 URLs for performance
                try:
                    logger.info(f"Extracting content from URL: {url}")
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                    response = requests.get(url, headers=headers, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove unwanted elements
                    for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript', 'iframe']):
                        element.decompose()
                    
                    # Extract main content with multiple strategies
                    content_text = ""
                    
                    # Strategy 1: Look for main content areas
                    main_content = (
                        soup.find('main') or 
                        soup.find('article') or 
                        soup.find('div', class_=lambda x: x and ('content' in x or 'article' in x or 'post' in x))
                    )
                    
                    if main_content:
                        content_text = main_content.get_text(separator=' ', strip=True)
                        logger.info(f"Found main content section: {len(content_text)} chars")
                    
                    # Strategy 2: If content is too short, look for specific news content patterns
                    if len(content_text) < 1500:
                        # Look for paragraphs, list items, and divs that might contain news content
                        content_elements = soup.find_all(['p', 'li', 'div'], text=True)
                        additional_content = []
                        
                        for elem in content_elements:
                            text = elem.get_text(strip=True)
                            # Skip very short text or common navigation elements
                            if (len(text) > 50 and 
                                not any(skip in text.lower() for skip in ['cookie', 'subscribe', 'sign in', 'menu', 'navigation', 'advertisement'])):
                                additional_content.append(text)
                        
                        if additional_content:
                            content_text += " " + " ".join(additional_content[:10])  # Take first 10 relevant elements
                            logger.info(f"Added additional content elements: {len(additional_content)} found")
                    
                    # Strategy 3: If still too short, get all text but filter more carefully
                    if len(content_text) < 1000:
                        all_text = soup.get_text(separator=' ', strip=True)
                        # Split into sentences and filter
                        sentences = [s.strip() for s in all_text.split('.') if len(s.strip()) > 30]
                        relevant_sentences = [s for s in sentences[:20] if not any(skip in s.lower() for skip in 
                                            ['cookie', 'subscribe', 'sign in', 'menu', 'follow us', 'advertisement', 'newsletter'])]
                        content_text = '. '.join(relevant_sentences[:15]) + '.'
                        logger.info(f"Using filtered sentences approach: {len(relevant_sentences)} sentences")
                    
                    # Clean and limit content
                    content_text = ' '.join(content_text.split())  # Remove extra whitespace
                    content_text = content_text[:5000]  # Increased limit for better content
                    
                    if content_text and len(content_text) > 200:
                        url_content += f"\n\nContent from {url}:\n{content_text}"
                        logger.info(f"Successfully extracted {len(content_text)} characters from {url}")
                    else:
                        logger.warning(f"Insufficient content extracted from {url}: {len(content_text)} chars")
                        
                except Exception as url_error:
                    logger.warning(f"Failed to extract content from {url}: {str(url_error)}")
                    continue
        
        # Generate content using direct OpenAI API
        if topic:
            if url_content:
                content_prompt = f"""Create an engaging podcast conversation about: {topic}

Using this additional context from web sources:
{url_content}

Please create a natural dialogue between two hosts discussing this topic. 
Format it as:

Host 1: [First speaker's content]
Host 2: [Second speaker's response]
Host 1: [Continuing the conversation]
...

Make it informative, engaging, and conversational. Incorporate the key insights from the provided context. Keep it around 400-600 words total."""
            else:
                content_prompt = f"""Create an engaging podcast conversation about: {topic}

Please create a natural dialogue between two hosts discussing this topic. 
Format it as:

Host 1: [First speaker's content]
Host 2: [Second speaker's response]
Host 1: [Continuing the conversation]
...

Make it informative, engaging, and conversational. Keep it around 300-500 words total for faster processing."""
        
        elif text:
            content_prompt = f"""Convert this text into an engaging podcast conversation between two hosts:

{text[:1500] if len(text) > 1500 else text}

Format as a natural dialogue:
Host 1: [First speaker introducing the topic]
Host 2: [Second speaker responding and adding insights]
...

Make it conversational and engaging. Keep it concise."""
        
        elif urls and url_content:
            content_prompt = f"""Create a podcast conversation about this content from the web:

{url_content}

Format as a natural dialogue between two hosts:
Host 1: [First speaker introducing the topic]
Host 2: [Second speaker responding and adding insights]
...

Make it informative and engaging, discussing the key points from the content."""
        
        elif urls:
            content_prompt = f"""Create a podcast conversation about content from these URLs: {', '.join(urls[:3])}

Host 1: Welcome to our podcast! Today we're discussing some interesting content from the web.
Host 2: That's right! Let's dive into what we found and explore the key insights.
Host 1: The main topics seem to be quite relevant to our audience.
Host 2: Absolutely, and there are some fascinating points worth exploring further."""
        
        else:
            raise Exception("No content provided")
        
        # Use OpenAI directly (bypassing LangChain)
        conversation_text = ""
        openai_key = os.environ.get("OPENAI_API_KEY")
        
        if openai_key:
            try:
                import openai
                openai.api_key = openai_key
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": content_prompt}],
                    max_tokens=1000,
                    temperature=0.7
                )
                conversation_text = response.choices[0].message.content
                logger.info("Generated content using OpenAI")
            except Exception as e:
                logger.warning(f"OpenAI failed: {e}, using fallback content")
                conversation_text = None
        
        # Fallback to a simple generated conversation if OpenAI fails
        if not conversation_text:
            if url_content:
                # Use the extracted content for a more relevant fallback
                topic_name = topic or "the topics we found in the news"
                
                # Extract key points from the content for the conversation
                key_points = []
                sentences = url_content.split('.')[:10]  # First 10 sentences
                for sentence in sentences:
                    if len(sentence.strip()) > 30:  # Only meaningful sentences
                        key_points.append(sentence.strip())
                
                # Create a conversation based on the actual content
                conversation_text = f"""Host 1: Welcome to our podcast! Today we're discussing {topic_name}.

Host 2: Thanks for tuning in! We've gathered some important information that our listeners need to know about.

Host 1: That's right. Let me share what we've learned: {key_points[0] if key_points else 'There have been significant developments'}.

Host 2: This is really important information. {key_points[1] if len(key_points) > 1 else 'The details are quite significant.'} 

Host 1: Absolutely. {key_points[2] if len(key_points) > 2 else 'There are several key aspects to consider here.'}

Host 2: What stands out to me is how this impacts the community. {key_points[3] if len(key_points) > 3 else 'The implications are far-reaching.'}

Host 1: I think our listeners will find this information valuable. {key_points[4] if len(key_points) > 4 else 'It\'s important to stay informed about these developments.'}

Host 2: Definitely. This is exactly the kind of content that makes our podcast relevant and informative.

Host 1: And that wraps up today's discussion. Thanks for listening, and don't forget to subscribe for more important updates!

Host 2: Until next time, stay informed and stay safe!"""
                
                logger.info("Using content-based fallback conversation")
            else:
                topic_name = topic or "interesting topics" 
                conversation_text = f"""Host 1: Welcome to our podcast! Today we're exploring {topic_name}.

Host 2: Thanks for tuning in! This is definitely something our listeners will find valuable and thought-provoking.

Host 1: Let's dive right into the key points and discuss what makes this so important in today's world.

Host 2: Absolutely! The insights we've gathered really highlight the significance of this subject and its impact.

Host 1: There are so many fascinating aspects to consider, and I think our audience will really appreciate this discussion.

Host 2: I couldn't agree more. It's topics like these that make our podcast so engaging and informative.

Host 1: And that wraps up today's discussion. Thanks for listening, and don't forget to subscribe!

Host 2: Until next time, keep exploring and stay curious!"""
                logger.info("Using generic fallback conversation content")
        
        # Generate audio using edge-tts (bypasses LangChain TTS)
        if tts_model == "edge":
            try:
                # Create temporary files
                audio_id = str(uuid.uuid4())
                audio_filename = f"podcast_{audio_id}.mp3"
                audio_path = os.path.join(TEMP_DIR, audio_filename)
                
                # Use edge-tts to generate audio
                communicate = edge_tts.Communicate(conversation_text, "en-US-AriaNeural")
                await communicate.save(audio_path)
                
                logger.info(f"Generated audio file: {audio_filename}")
                
                return {
                    "success": True,
                    "message": "Podcast generated successfully using direct API fallback",
                    "audio_url": f"/audio/{audio_filename}",
                    "transcript": conversation_text,
                    "method": "direct_api_fallback"
                }
            except Exception as e:
                logger.error(f"Edge TTS failed: {e}")
                # Return text-only response if TTS fails
                return {
                    "success": True,
                    "message": "Podcast content generated (audio generation failed, text only)",
                    "transcript": conversation_text,
                    "method": "direct_api_fallback",
                    "error": f"TTS failed: {str(e)}"
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
        logger.error(f"Direct API fallback failed: {str(e)}")
        raise Exception(f"Direct API fallback failed: {str(e)}")

@app.post("/generate")
async def generate_podcast_endpoint(data: dict):
    """
    Generate a podcast from URLs, direct text input, or topic.
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
    
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
        tts_model = data.get('tts_model', base_config.get('text_to_speech', {}).get('default_tts_model', 'edge'))
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

        # Create a wrapper function for timeout handling
        def generate_with_timeout():
            try:
                # For deployed environments, try LangChain first with better error handling
                if os.getenv('RENDER'):
                    logger.info("Render deployment detected - using optimized generation")
                    try:
                        # Try the full LangChain pipeline first
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
                        logger.info("Successfully generated using LangChain pipeline")
                        return result
                    except Exception as langchain_error:
                        logger.warning(f"LangChain pipeline failed: {str(langchain_error)}")
                        # Fall back to direct API if LangChain fails
                        logger.info("Falling back to direct API method")
                        return asyncio.run(generate_podcast_direct_api(
                            urls=urls,
                            text=text,
                            topic=topic,
                            tts_model=tts_model,
                            longform=bool(data.get('is_long_form', False))
                        ))
                
                # For non-deployed environments, try LangChain first
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
                return result
            except Exception as e:
                # Fallback to direct API
                logger.warning(f"All LangChain methods failed, using direct API: {str(e)}")
                return asyncio.run(generate_podcast_direct_api(
                    urls=urls,
                    text=text,
                    topic=topic,
                    tts_model=tts_model,
                    longform=bool(data.get('is_long_form', False))
                ))

        # Execute with timeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(generate_with_timeout)
            try:
                # Wait for result with 120 second timeout
                result = future.result(timeout=120)
            except FuturesTimeoutError:
                # Cancel the future and return timeout error
                future.cancel()
                raise HTTPException(
                    status_code=408,
                    detail="Request timeout. Podcast generation is taking longer than expected. Please try again with a shorter topic or text."
                )

        # Handle the result
        if isinstance(result, dict):
            if result.get('method') == 'direct_api_fallback':
                return result
            elif result.get('audio_file'):
                filename = f"podcast_{os.urandom(8).hex()}.mp3"
                output_path = os.path.join(TEMP_DIR, filename)
                shutil.copy2(result['audio_file'], output_path)
                return {"success": True, "audio_url": f"/audio/{filename}"}
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
        logger.error(f"Unexpected error in generate_podcast_endpoint: {str(e)}")
        # Final fallback - try direct API with minimal timeout
        try:
            result = await generate_podcast_direct_api(
                urls=data.get('urls', []),
                text=data.get('text'),
                topic=data.get('topic'),
                tts_model=data.get('tts_model', 'edge'),
                longform=bool(data.get('is_long_form', False))
            )
            return result
        except Exception as e2:
            raise HTTPException(
                status_code=500, 
                detail=f"All generation methods failed. Error: {str(e2)}"
            )

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
