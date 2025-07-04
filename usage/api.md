
# Podcastfy REST API Documentation

## Overview

The Podcastfy API allows you to programmatically generate AI podcasts from various input sources. This document outlines the API endpoints and their usage.

## Using cURL with Podcastfy API

### Prerequisites
1. Confirm cURL installation:
```bash
curl --version
```

### API Request Flow
Making a prediction requires two sequential requests:
1. POST request to initiate processing - returns an `EVENT_ID`
2. GET request to fetch results - uses the `EVENT_ID` to fetch results

Between step 1 and 2, there is a delay of 1-3 minutes. We are working on reducing this delay and implementing a way to notify the user when the podcast is ready. Thanks for your patience!

### Basic Request Structure
```bash
# Step 1: POST request to initiate processing
# Make sure to include http:// or https:// in the URL
curl -X POST https://thatupiso-podcastfy-ai-demo.hf.space/gradio_api/call/process_inputs \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      "text_input",
      "https://yourwebsite.com",
      [],  # pdf_files
      [],  # image_files
      "gemini_key",
      "openai_key",
      "elevenlabs_key",
      2000,  # word_count
      "engaging,fast-paced",  # conversation_style
      "main summarizer",  # roles_person1
      "questioner",  # roles_person2
      "Introduction,Content,Conclusion",  # dialogue_structure
      "PODCASTFY",  # podcast_name
      "YOUR PODCAST",  # podcast_tagline
      "openai",  # tts_model
      0.7,  # creativity_level
      ""  # user_instructions
    ]
  }'

# Step 2: GET request to fetch results
curl -N https://thatupiso-podcastfy-ai-demo.hf.space/gradio_api/call/process_inputs/$EVENT_ID


# Example output result
event: complete
data: [{"path": "/tmp/gradio/bcb143f492b1c9a6dbde512557541e62f090bca083356be0f82c2e12b59af100/podcast_81106b4ca62542f1b209889832a421df.mp3", "url": "https://thatupiso-podcastfy-ai-demo.hf.space/gradio_a/gradio_api/file=/tmp/gradio/bcb143f492b1c9a6dbde512557541e62f090bca083356be0f82c2e12b59af100/podcast_81106b4ca62542f1b209889832a421df.mp3", "size": null, "orig_name": "podcast_81106b4ca62542f1b209889832a421df.mp3", "mime_type": null, "is_stream": false, "meta": {"_type": "gradio.FileData"}}]

```

You can download the file by extending the URL prefix "https://thatupiso-podcastfy-ai-demo.hf.space/gradio_a/gradio_api/file=" with the path to the file in variable `path`. (Note: The variable "url" above has a bug introduced by Gradio, so please ignore it.)

## FastAPI Endpoint (Direct REST API)

Podcastfy also provides a direct FastAPI endpoint for podcast generation that supports multiple input types.

### Available Input Types

The API supports three types of input sources:
1. **URLs** - Process content from web pages
2. **Direct Text** - Convert your own text content into a podcast
3. **Topic** - Generate a podcast about a specific topic (uses AI to research and create content)

### Endpoint: `/generate`

**Method:** `POST`  
**URL:** `http://localhost:8080/generate`

### Request Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| urls | array | No* | List of URLs to process |
| text | string | No* | Direct text input for podcast generation |
| topic | string | No* | Topic to generate podcast content about |
| openai_key | string | No | OpenAI API key |
| google_key | string | No | Google Gemini API key |
| elevenlabs_key | string | No | ElevenLabs API key |
| tts_model | string | No | TTS model ("openai", "elevenlabs", "edge", "gemini") |
| creativity | number | No | Creativity level (0-1) |
| conversation_style | array | No | Style descriptors (e.g. ["engaging", "informative"]) |
| roles_person1 | string | No | Role of first speaker |
| roles_person2 | string | No | Role of second speaker |
| dialogue_structure | array | No | Structure (e.g. ["Introduction", "Content", "Conclusion"]) |
| name | string | No | Podcast name |
| tagline | string | No | Podcast tagline |
| output_language | string | No | Output language |
| user_instructions | string | No | Custom instructions |
| engagement_techniques | array | No | Engagement techniques |
| voices | object | No | Voice selection {"question": "voice1", "answer": "voice2"} |
| is_long_form | boolean | No | Generate long-form content |

*At least one of `urls`, `text`, or `topic` must be provided.

### Example Requests

#### 1. Generate from URLs
```bash
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com/article"],
    "openai_key": "your-openai-key",
    "tts_model": "openai",
    "name": "Tech News",
    "creativity": 0.7
  }'
```

#### 2. Generate from Direct Text
```bash
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artificial Intelligence is transforming industries worldwide. Machine learning algorithms can now process vast amounts of data to identify patterns and make predictions.",
    "openai_key": "your-openai-key",
    "tts_model": "openai",
    "name": "AI Insights",
    "conversation_style": ["educational", "accessible"],
    "roles_person1": "AI researcher",
    "roles_person2": "curious journalist"
  }'
```

#### 3. Generate from Topic
```bash
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "The future of renewable energy",
    "google_key": "your-gemini-key",
    "tts_model": "openai",
    "name": "Green Future",
    "conversation_style": ["informative", "optimistic"],
    "creativity": 0.6
  }'
```

### Response Format
```json
{
  "audioUrl": "/audio/podcast_abc123.mp3"
}
```

Use the `/audio/{filename}` endpoint to download the generated audio file.

---

## Gradio API (Legacy)

### Parameter Details
| Index | Parameter | Type | Description |
|-------|-----------|------|-------------|
| 0 | text_input | string | Direct text input for podcast generation |
| 1 | urls_input | string | URLs to process (include http:// or https://) |
| 2 | pdf_files | array | List of PDF files to process |
| 3 | image_files | array | List of image files to process |
| 4 | gemini_key | string | Google Gemini API key |
| 5 | openai_key | string | OpenAI API key |
| 6 | elevenlabs_key | string | ElevenLabs API key |
| 7 | word_count | number | Target word count for podcast |
| 8 | conversation_style | string | Conversation style descriptors (e.g. "engaging,fast-paced") |
| 9 | roles_person1 | string | Role of first speaker |
| 10 | roles_person2 | string | Role of second speaker |
| 11 | dialogue_structure | string | Structure of dialogue (e.g. "Introduction,Content,Conclusion") |
| 12 | podcast_name | string | Name of the podcast |
| 13 | podcast_tagline | string | Podcast tagline |
| 14 | tts_model | string | Text-to-speech model ("gemini", "openai", "elevenlabs", or "edge") |
| 15 | creativity_level | number | Level of creativity (0-1) |
| 16 | user_instructions | string | Custom instructions for generation |


## Using Python

### Installation

```bash
pip install gradio_client
```

### Quick Start

```python
from gradio_client import Client, handle_file

client = Client("thatupiso/Podcastfy.ai_demo")
```

### API Endpoints

#### Generate Podcast (`/process_inputs`)

Generates a podcast from provided text, URLs, PDFs, or images.

##### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| text_input | str | Yes | - | Raw text input for podcast generation |
| urls_input | str | Yes | - | Comma-separated URLs to process |
| pdf_files | List[filepath] | Yes | None | List of PDF files to process |
| image_files | List[filepath] | Yes | None | List of image files to process |
| gemini_key | str | No | "" | Google Gemini API key |
| openai_key | str | No | "" | OpenAI API key |
| elevenlabs_key | str | No | "" | ElevenLabs API key |
| word_count | float | No | 2000 | Target word count for podcast |
| conversation_style | str | No | "engaging,fast-paced,enthusiastic" | Conversation style descriptors |
| roles_person1 | str | No | "main summarizer" | Role of first speaker |
| roles_person2 | str | No | "questioner/clarifier" | Role of second speaker |
| dialogue_structure | str | No | "Introduction,Main Content Summary,Conclusion" | Structure of dialogue |
| podcast_name | str | No | "PODCASTFY" | Name of the podcast |
| podcast_tagline | str | No | "YOUR PERSONAL GenAI PODCAST" | Podcast tagline |
| tts_model | Literal['openai', 'elevenlabs', 'edge'] | No | "openai" | Text-to-speech model |
| creativity_level | float | No | 0.7 | Level of creativity (0-1) |
| user_instructions | str | No | "" | Custom instructions for generation |

##### Returns

| Type | Description |
|------|-------------|
| filepath | Path to generated audio file |

##### Example Usage

```python
from gradio_client import Client, handle_file

client = Client("thatupiso/Podcastfy.ai_demo")

# Generate podcast from URL
result = client.predict(
    text_input="",
    urls_input="https://example.com/article",
    pdf_files=[],
    image_files=[],
    gemini_key="your-gemini-key",
    openai_key="your-openai-key",
    word_count=1500,
    conversation_style="casual,informative",
    podcast_name="Tech Talk",
    tts_model="openai",
    creativity_level=0.8
)

print(f"Generated podcast: {result}")
```

### Error Handling

The API will return appropriate error messages for:
- Invalid API keys
- Malformed input
- Failed file processing
- TTS generation errors

### Rate Limits

Please be aware of the rate limits for the underlying services:
- Gemini API
- OpenAI API
- ElevenLabs API

## Notes

- At least one input source (text, URL, PDF, or image) must be provided
- API keys are required for corresponding services
- The generated audio file format is MP3