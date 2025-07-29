# 🎙️ Podcastfy Usage Guide

## 📋 Overview

Podcastfy can be used in multiple ways:
1. **Web Interface** (Easiest)
2. **Python API** (Programmatic) 
3. **Operator Integration** (Workflow automation)
4. **Command Line** (CLI)

---

## 🌐 1. Web Interface Usage

### **Live Web App**
Visit: **https://podcastfy-g0ebyv6nq-latent-labs1.vercel.app**

### **Features:**
- ✅ Generate from URLs
- ✅ Generate from text
- ✅ Generate from topics
- ✅ Upload PDFs and images
- ✅ Multiple TTS models
- ✅ Different conversation styles
- ✅ Download audio and transcripts

### **How to Use:**
1. **Choose Content Source:**
   - **URLs**: Paste website links
   - **Text**: Enter your content directly
   - **Topic**: Just enter a topic like "AI in Healthcare"
   - **Files**: Upload PDFs or images

2. **Configure Settings:**
   - **TTS Model**: Edge (free), OpenAI, ElevenLabs, Gemini
   - **Style**: Casual, Formal, Educational, Interview
   - **Length**: Regular or Long-form

3. **Generate**: Click "Generate Podcast"
4. **Download**: Get your audio file and transcript

---

## 🐍 2. Python API Usage

### **Installation**
```python
# Use the operator_integration.py file
from operator_integration import PodcastfyOperatorTool
```

### **Basic Usage**
```python
# Initialize the tool
tool = PodcastfyOperatorTool()

# Generate from topic
result = tool.generate_podcast(
    topic="The Future of Artificial Intelligence",
    tts_model="edge",
    conversation_style="educational"
)

if result.success:
    print(f"Audio: {result.audio_url}")
    print(f"Transcript: {result.transcript_url}")
else:
    print(f"Error: {result.error}")
```

### **Advanced Usage**
```python
# Generate from URLs
result = tool.generate_podcast(
    urls=["https://www.bbc.com/news/technology"],
    tts_model="openai",
    conversation_style="casual",
    longform=True
)

# Generate from text
result = tool.generate_podcast(
    text="Your long text content here...",
    tts_model="elevenlabs",
    conversation_style="interview"
)

# Mix multiple sources
result = tool.generate_podcast(
    urls=["https://example.com/article"],
    text="Additional context...",
    topic="AI Ethics",
    tts_model="gemini"
)
```

---

## 🔧 3. Operator Integration

### **Setup for Operator**
```python
from operator_integration import OperatorPodcastfyTool

# Initialize for Operator
podcastfy_tool = OperatorPodcastfyTool()

# Get tool schema (for Operator registration)
schema = podcastfy_tool.get_schema()
print(schema)
```

### **Execute in Operator Workflow**
```python
# This is how Operator would call the tool
result = podcastfy_tool.execute(
    topic="Climate Change Solutions",
    tts_model="edge",
    conversation_style="educational",
    longform=False
)

# Result format for Operator
{
    "success": True,
    "data": {
        "audio_url": "https://...",
        "transcript_url": "https://...",
        "message": "Podcast generated successfully"
    },
    "error": None
}
```

### **Tool Configuration for Operator**
```json
{
  "name": "podcastfy",
  "description": "Generate AI-powered podcasts from various content sources",
  "parameters": {
    "topic": "Topic to generate podcast about",
    "urls": "List of URLs to process",
    "text": "Direct text content",
    "tts_model": "TTS model (edge, openai, elevenlabs, gemini)",
    "conversation_style": "Style (casual, formal, educational, interview)",
    "longform": "Generate long-form content (boolean)"
  }
}
```

---

## 💻 4. Local Development

### **Start Local Backend**
```bash
cd backend
PORT=8000 python server.py
```

### **Test Local API**
```python
# Use localhost for testing
tool = PodcastfyOperatorTool(base_url="http://localhost:8000")
result = tool.generate_podcast(topic="Test Topic")
```

---

## 🎛️ Configuration Options

### **TTS Models**
- **`edge`**: Free, good quality, fast
- **`openai`**: High quality, requires API key
- **`elevenlabs`**: Premium quality, requires API key
- **`gemini`**: Google's TTS, requires API key

### **Conversation Styles**
- **`casual`**: Relaxed, friendly conversation
- **`formal`**: Professional, structured discussion
- **`educational`**: Teaching-focused, explanatory
- **`interview`**: Q&A format, journalistic

### **Content Sources**
- **URLs**: Web articles, blog posts, news
- **Text**: Direct text input, documents
- **Topics**: AI generates content about the topic
- **PDFs**: Extract and process PDF content
- **Images**: Analyze and discuss images

---

## 🔍 Examples

### **Example 1: News Podcast**
```python
tool = PodcastfyOperatorTool()

result = tool.generate_podcast(
    urls=[
        "https://www.bbc.com/news/technology",
        "https://techcrunch.com/latest"
    ],
    tts_model="edge",
    conversation_style="casual"
)
```

### **Example 2: Educational Content**
```python
result = tool.generate_podcast(
    topic="Quantum Computing Basics",
    tts_model="openai",
    conversation_style="educational",
    longform=True
)
```

### **Example 3: Research Paper Discussion**
```python
result = tool.generate_podcast(
    text="""
    Abstract: This paper presents a novel approach to...
    [Your research paper content]
    """,
    tts_model="elevenlabs",
    conversation_style="interview"
)
```

---

## 🚨 Troubleshooting

### **Common Issues**

1. **"Request timed out"**
   - TTS generation can take 2-5 minutes
   - Try shorter content or different TTS model

2. **"API request failed"**
   - Check your internet connection
   - Verify the backend is running

3. **"No content provided"**
   - Ensure at least one of: urls, text, or topic is provided
   - Check content is not empty

### **Debug Mode**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test health check
tool = PodcastfyOperatorTool()
health = tool.health_check()
print(health)
```

---

## 🎯 Best Practices

### **Content Guidelines**
- **Topics**: Be specific (good: "AI in Healthcare", bad: "AI")
- **URLs**: Use recent, text-heavy articles
- **Text**: 500-5000 words works best
- **Length**: Start with regular, use longform for detailed content

### **Performance Tips**
- **Edge TTS**: Fastest, good for testing
- **Shorter content**: Faster generation
- **Local backend**: Faster for development

### **Production Usage**
- Use the web interface for one-off podcasts
- Use the Python API for automation
- Use Operator integration for workflows

---

## 📞 Support

- **Issues**: Check the troubleshooting section
- **Development**: Use local backend for testing
- **Production**: Use the deployed web interface

---

## 🎉 You're Ready!

Podcastfy is now set up and ready to use in multiple ways:

✅ **Web Interface**: https://podcastfy-g0ebyv6nq-latent-labs1.vercel.app  
✅ **Python API**: Use `operator_integration.py`  
✅ **Operator Integration**: Ready for workflow automation  
✅ **Local Development**: Flask backend working  

Start generating podcasts! 🎙️ 