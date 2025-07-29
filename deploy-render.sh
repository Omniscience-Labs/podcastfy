#!/bin/bash
# Render Deployment Script for Podcastfy

echo "🚀 Deploying Podcastfy Backend to Render..."

# Check if render CLI is available
if ! command -v render &> /dev/null; then
    echo "❌ Render CLI not found. Please install it first:"
    echo "brew install render"
    exit 1
fi

# Navigate to backend directory
cd backend

echo "📦 Creating Render service..."

# Create the service using the render.yaml configuration
render service create --config render.yaml

echo "✅ Render service created!"
echo "📝 Don't forget to set your environment variables in the Render dashboard:"
echo "   - GEMINI_API_KEY"
echo "   - OPENAI_API_KEY" 
echo "   - ELEVENLABS_API_KEY"
echo ""
echo "🌐 Your backend will be available at: https://podcastfy-backend.onrender.com" 