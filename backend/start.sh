#!/bin/bash
# Simple startup script for Render deployment
# This avoids the Doppler dependency issue

echo "Starting Podcastfy Backend Server..."
echo "Environment variables:"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+'***SET***'}"
echo "ELEVENLABS_API_KEY: ${ELEVENLABS_API_KEY:+'***SET***'}"
echo "GOOGLE_API_KEY: ${GOOGLE_API_KEY:+'***SET***'}"

# Run the Python server
python server.py 