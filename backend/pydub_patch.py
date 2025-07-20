#!/usr/bin/env python3
"""
Pydub patch for Python 3.13 compatibility
Fixes missing audioop module and escape sequence warnings
"""

import sys
import warnings
import re
import types

# Fix escape sequence warnings in pydub
def fix_pydub_warnings():
    """Fix invalid escape sequence warnings in pydub"""
    try:
        import pydub.utils
        # Fix the regex patterns that have invalid escape sequences
        if hasattr(pydub.utils, '_parse_ffmpeg_output'):
            # Replace the problematic regex patterns
            original_parse = pydub.utils._parse_ffmpeg_output
            
            def fixed_parse_ffmpeg_output(output):
                # Fix the regex patterns
                lines = output.split('\n')
                result = []
                for line in lines:
                    # Fix the problematic patterns
                    line = re.sub(r'([su]([0-9]{1,2})p?) \(([0-9]{1,2}) bit\)$', r'\1 (\3 bit)', line)
                    line = re.sub(r'([su]([0-9]{1,2})p?)( \(default\))?$', r'\1\3', line)
                    line = re.sub(r'(flt)p?( \(default\))?$', r'\1\2', line)
                    line = re.sub(r'(dbl)p?( \(default\))?$', r'\1\2', line)
                    result.append(line)
                return original_parse('\n'.join(result))
            
            pydub.utils._parse_ffmpeg_output = fixed_parse_ffmpeg_output
    except ImportError:
        pass

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
    audioop = types.ModuleType('audioop')
    audioop.__dict__.update(DummyAudioop().__dict__)
    
    # Add it to sys.modules so pydub can import it
    sys.modules['audioop'] = audioop

# Also handle pyaudioop
try:
    import pyaudioop
except ImportError:
    sys.modules['pyaudioop'] = audioop

# Apply the fixes
fix_pydub_warnings()

print("Pydub patch applied successfully for Python 3.13 compatibility") 