"""
FastAPI Fix for Environment Variables
====================================

This patch fixes the issue where the FastAPI version overwrites environment variables
with None values from the request data.
"""

# Original problematic code:
# os.environ['OPENAI_API_KEY'] = data.get('openai_key')
# os.environ['GEMINI_API_KEY'] = data.get('google_key')
# os.environ['ELEVENLABS_API_KEY'] = data.get('elevenlabs_key')

# Fixed code:
def set_api_keys_from_request(data: dict):
    """
    Set API keys from request data, but only if they're provided.
    Otherwise, keep existing environment variables.
    """
    # Only set environment variables if they're provided in the request
    if data.get('openai_key'):
        os.environ['OPENAI_API_KEY'] = data.get('openai_key')
    
    if data.get('google_key'):
        os.environ['GEMINI_API_KEY'] = data.get('google_key')
    
    if data.get('elevenlabs_key'):
        os.environ['ELEVENLABS_API_KEY'] = data.get('elevenlabs_key')

# The lines 92-94 in fast_app.py should be replaced with:
# set_api_keys_from_request(data) 