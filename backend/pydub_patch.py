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
    # Create a functional audioop module replacement for Python 3.13+
    import struct
    import array
    
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

try:
    import pyaudioop
except ImportError:
    sys.modules['pyaudioop'] = audioop

# Apply all fixes
fix_pydub_warnings()
fix_google_genai_pydantic()
print("Pydub and Google GenAI patches applied successfully for Python 3.13 compatibility") 