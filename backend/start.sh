#!/bin/bash
# Simple startup script for Render deployment
# This avoids the Doppler dependency issue

echo "Starting Podcastfy Backend Server..."
echo "Environment variables:"
echo "GEMINI_API_KEY: ${GEMINI_API_KEY:+'***SET***'}"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+'***SET***'}"
echo "ELEVENLABS_API_KEY: ${ELEVENLABS_API_KEY:+'***SET***'}"

# Run the Python server
python server.py 