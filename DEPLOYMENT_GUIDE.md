# 🚀 Podcastfy Deployment Guide

## 📋 Overview

This guide covers deploying Podcastfy to:
- **Backend**: Render (API service)
- **Frontend**: Vercel (Web interface)
- **Integration**: Operator (Tool integration)

## 🔑 Environment Variables Setup

### Step 1: Get Your API Keys

1. **Gemini API Key**: https://aistudio.google.com/app/apikey
2. **OpenAI API Key**: https://platform.openai.com/api-keys
3. **ElevenLabs API Key**: https://elevenlabs.io/app/speech-synthesis

### Step 2: Local Development Setup

```bash
# Copy the template
cp env.template .env

# Edit .env with your actual API keys
# The .env file is already in .gitignore so it won't be committed
```

## 🖥️ Backend Deployment (Render)

### Option 1: Render Dashboard (Recommended)

1. **Create Service**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository: `Omniscience-Labs/podcastfy`

2. **Configure Service**:
   - **Name**: `podcastfy-backend`
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `./Dockerfile_api`
   - **Plan**: Free

3. **Add Environment Variables**:
   - Go to your service → "Environment" tab
   - Add each variable from your `.env` file:
     ```
     GEMINI_API_KEY=your_actual_key_here
     OPENAI_API_KEY=your_actual_key_here
     ELEVENLABS_API_KEY=your_actual_key_here
     LANGCHAIN_TRACING_V2=False
     DEFAULT_VOICE=Rachel
     LANGUAGE=en
     LOG_LEVEL=INFO
     ```

4. **Deploy**: Click "Create Web Service"

### Option 2: Render CLI

```bash
# Login to Render
render login

# Deploy (after setting up environment variables in dashboard)
render services create
```

## 🌐 Frontend Deployment (Vercel)

```bash
# Deploy to Vercel
npx vercel --prod

# Your frontend will be available at:
# https://your-project-name.vercel.app
```

## 🔧 Operator Integration

### Standalone Usage

```python
from operator_integration import PodcastfyOperatorTool

# Initialize the tool
tool = PodcastfyOperatorTool(base_url="https://your-render-url.onrender.com")

# Generate a podcast
result = tool.generate_podcast(
    topic="AI in Healthcare",
    tts_model="edge",
    conversation_style="educational"
)

if result.success:
    print(f"Audio URL: {result.audio_url}")
    print(f"Transcript URL: {result.transcript_url}")
```

### Operator Integration

```python
from operator_integration import OperatorPodcastfyTool

# Register with Operator
podcastfy_tool = OperatorPodcastfyTool()

# Use in Operator workflows
result = podcastfy_tool.execute(
    topic="The Future of AI",
    tts_model="openai"
)
```

## 🧪 Testing Your Deployment

### Test Backend Health

```bash
curl https://your-render-url.onrender.com/health
# Should return: {"status":"healthy"}
```

### Test Podcast Generation

```bash
curl -X POST https://your-render-url.onrender.com/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Artificial Intelligence",
    "tts_model": "edge"
  }'
```

### Test Operator Integration

```python
python operator_integration.py
```

## 🔒 Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for all sensitive data
3. **Keep .env in .gitignore** (already configured)
4. **Use different API keys** for development and production
5. **Regularly rotate API keys**

## 🐛 Troubleshooting

### Common Issues

1. **404 Errors**: Check if you're using the correct endpoint paths:
   - FastAPI version: `/health`, `/generate`
   - Flask version: `/api/health`, `/api/generate`

2. **Environment Variables**: Ensure all required variables are set in Render

3. **API Key Issues**: Verify your API keys are valid and have sufficient quota

### Getting Help

- Check the logs in your Render dashboard
- Test endpoints individually
- Verify environment variables are set correctly

## 📚 API Documentation

### Endpoints

- `GET /health` - Health check
- `POST /generate` - Generate podcast

### Parameters

- `urls`: Array of URLs to process
- `text`: Direct text input
- `topic`: Topic to generate content about
- `tts_model`: TTS model (edge, openai, elevenlabs, gemini)
- `conversation_style`: Style (casual, formal, educational, interview)
- `longform`: Boolean for long-form content

## 🎯 Next Steps

1. Deploy your backend to Render
2. Deploy your frontend to Vercel
3. Test the integration
4. Integrate with Operator
5. Start generating podcasts! 