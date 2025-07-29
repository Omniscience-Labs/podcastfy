#!/bin/bash
# Flask Backend Startup Script for Render

echo "Starting Podcastfy Flask Backend..."
echo "Environment variables:"
echo "GEMINI_API_KEY: ${GEMINI_API_KEY:+'***SET***'}"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+'***SET***'}"
echo "ELEVENLABS_API_KEY: ${ELEVENLABS_API_KEY:+'***SET***'}"
echo "PORT: ${PORT:-8000}"

# Change to backend directory
cd /opt/render/project/src/backend

# Run the Flask server
python server.py 