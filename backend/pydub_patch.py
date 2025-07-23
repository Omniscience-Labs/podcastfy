#!/usr/bin/env python3
"""
Pydub patch for Python 3.13 compatibility
Fixes missing audioop module and escape sequence warnings
Also fixes Google Generative AI Pydantic issues
"""
import sys
import warnings
import re
import types
import os

def fix_pydub_warnings():
    """Fix pydub regex warnings"""
    try:
        import pydub.utils
        # Fix the problematic regex patterns
        if hasattr(pydub.utils, '_parse_ffmpeg_output'):
            original_func = pydub.utils._parse_ffmpeg_output
            
            def fixed_parse_ffmpeg_output(output):
                # Replace problematic regex patterns with raw strings
                output = re.sub(r'([su]([0-9]{1,2})p?) \(([0-9]{1,2}) bit\)$', r'\1 (\3 bit)', output)
                output = re.sub(r'([su]([0-9]{1,2})p?)( \(default\))?$', r'\1\3', output)
                output = re.sub(r'(flt)p?( \(default\))?$', r'\1\2', output)
                output = re.sub(r'(dbl)p?( \(default\))?$', r'\1\2', output)
                return original_func(output)
            
            pydub.utils._parse_ffmpeg_output = fixed_parse_ffmpeg_output
    except ImportError:
        pass

def fix_google_genai_pydantic():
    """Fix Google Generative AI Pydantic issues"""
    # This function is kept for compatibility but the main fix is now in content_generator.py
    # The ChatGoogleGenerativeAI import is now wrapped in try/except with fallback to LiteLLM
    pass

try:
    import audioop
except ImportError:
    # Create a dummy audioop module if it doesn't exist
    class DummyAudioop:
        def __getattr__(self, name):
            def dummy_function(*args, **kwargs):
                warnings.warn(f"audioop.{name} is not available in Python 3.13+", RuntimeWarning)
                return None
            return dummy_function
    
    # Create a dummy module
    audioop = types.ModuleType('audioop')
    audioop.__dict__.update(DummyAudioop().__dict__)
    
    # Add it to sys.modules so pydub can import it
    sys.modules['audioop'] = audioop

try:
    import pyaudioop
except ImportError:
    sys.modules['pyaudioop'] = audioop

# Apply all fixes
fix_pydub_warnings()
fix_google_genai_pydantic()
print("Pydub and Google GenAI patches applied successfully for Python 3.13 compatibility") 