# FastAPI Implementation for Podcastify

This FastAPI implementation provides REST endpoints for serving the Podcastify functionality via HTTP API.

## Features
- **Multiple Input Types**:
  - URL-based podcast generation from web content
  - Direct text input for custom content
  - Topic-based generation (AI researches and creates content)
- Multiple TTS models (OpenAI, ElevenLabs, Gemini, Edge)
- Audio file serving with temporary storage
- Full conversation configuration support
- Environment variable handling for API keys

## Endpoints

### `POST /generate`
Generate a podcast from various input sources.

**Input Types (at least one required):**
- `urls`: Array of URLs to process
- `text`: Direct text content 
- `topic`: Topic for AI to research and generate content about

**Example Requests:**

#### From URLs:
```json
{
  "urls": ["https://example.com/article"],
  "openai_key": "your-key",
  "tts_model": "openai"
}
```

#### From Text:
```json
{
  "text": "Your content here...",
  "openai_key": "your-key", 
  "tts_model": "openai",
  "name": "Custom Podcast"
}
```

#### From Topic:
```json
{
  "topic": "Climate change solutions",
  "google_key": "your-gemini-key",
  "tts_model": "openai",
  "creativity": 0.7
}
```

### `GET /audio/{filename}`
Serve generated audio files.

### `GET /health`
Health check endpoint.

## Usage
See `usage/fast_api_example.py` for complete usage examples demonstrating all input types.

## Requirements
- Uvicorn
- FastAPI
- aiohttp
- pyyaml