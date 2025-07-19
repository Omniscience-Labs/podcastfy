"""
Patch for pydub to handle missing audioop module in Python 3.13+
This should be imported before importing pydub
"""

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
    # Use the same dummy module for pyaudioop
    sys.modules['pyaudioop'] = audioop 