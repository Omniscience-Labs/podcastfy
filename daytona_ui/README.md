# 🎙️ Podcastfy Daytona Web Interface

A modern web interface for Podcastfy that allows users to generate AI podcasts from various content sources through a beautiful, intuitive UI.

## ✨ Features

- **Multiple Content Sources**: URLs, direct text, topics, PDFs, and images
- **Real-time Processing**: Live progress tracking and status updates
- **Audio Player**: Built-in audio player with download and share options
- **Transcript Viewing**: View and download generated transcripts
- **Modern UI**: Beautiful, responsive design with Tailwind CSS
- **File Upload**: Drag-and-drop file upload for PDFs and images
- **Configuration Options**: TTS model selection, conversation styles, and more

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **Podcastfy** backend configured with API keys
3. **Flask** and dependencies installed

### Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API keys** (in parent directory):
   ```bash
   # Create .env file with your API keys
   GEMINI_API_KEY=your_gemini_key
   OPENAI_API_KEY=your_openai_key
   ELEVENLABS_API_KEY=your_elevenlabs_key
   ```

3. **Start the server**:
   ```bash
   python server.py
   ```

4. **Open your browser**:
   ```
   http://localhost:5000
   ```

## 📁 File Structure

```
daytona_ui/
├── index.html          # Main web interface
├── app.js              # Frontend JavaScript
├── server.py           # Flask backend server
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── uploads/           # Uploaded files (created automatically)
```

## 🎯 Usage

### 1. Content Sources

- **Website URLs**: Enter URLs (one per line) to scrape content
- **Direct Text**: Paste or type your content directly
- **Topic Generation**: Enter a topic for AI to research and generate content
- **PDF Files**: Upload PDF documents for processing
- **Images**: Upload images for visual content analysis

### 2. Configuration

- **TTS Model**: Choose from Edge (free), OpenAI, ElevenLabs, or Gemini
- **Podcast Name**: Customize your podcast title
- **Conversation Style**: Select from engaging, casual, professional, or entertaining
- **Long Form**: Enable for extended content generation

### 3. Generation Process

1. Fill in at least one content source
2. Configure your preferences
3. Click "Generate Podcast"
4. Watch the progress bar
5. Listen to your generated podcast
6. Download or share the results

## 🔧 API Endpoints

### Generate Podcast
```
POST /api/generate
Content-Type: application/json

{
    "urls": ["https://example.com"],
    "text": "Your text content",
    "topic": "Your topic",
    "tts_model": "edge",
    "podcast_name": "My Podcast",
    "conversation_style": ["engaging", "informative"],
    "longform": false
}
```

### Health Check
```
GET /api/health
```

### System Status
```
GET /api/status
```

### Download Audio
```
GET /api/audio/{filename}
```

### Download Transcript
```
GET /api/transcript/{filename}
```

## 🛠️ Development

### Frontend Development

The frontend uses:
- **HTML5** with semantic markup
- **Tailwind CSS** for styling
- **Vanilla JavaScript** for functionality
- **Font Awesome** for icons

### Backend Development

The backend uses:
- **Flask** web framework
- **Flask-CORS** for cross-origin requests
- **Podcastfy** integration for content processing

### Adding New Features

1. **Frontend**: Modify `index.html` and `app.js`
2. **Backend**: Add new routes to `server.py`
3. **Styling**: Use Tailwind CSS classes or add custom CSS

## 🐛 Troubleshooting

### Common Issues

1. **"No module named 'flask'"**
   ```bash
   pip install -r requirements.txt
   ```

2. **"API key not found"**
   - Ensure `.env` file exists in parent directory
   - Check that API keys are properly set

3. **"File upload failed"**
   - Check file size (max 20MB)
   - Verify file format is supported
   - Ensure uploads directory has write permissions

4. **"Podcast generation failed"**
   - Check API key validity
   - Verify content source is accessible
   - Review server logs for detailed error messages

### Debug Mode

Run the server in debug mode for detailed error messages:
```bash
export FLASK_ENV=development
python server.py
```

## 📊 Status Dashboard

The web interface includes a status dashboard showing:

- ✅ **Working Features**: Website URLs, topic generation, direct text, PDF processing
- 🔄 **Fixed Features**: Image processing (base64 conversion)
- ❌ **Needs Fixing**: YouTube processing

## 🔒 Security Considerations

- File upload validation and sanitization
- API key security (use environment variables)
- CORS configuration for production
- Input validation and sanitization

## 🚀 Production Deployment

For production deployment:

1. **Use a production WSGI server** (Gunicorn, uWSGI)
2. **Set up reverse proxy** (Nginx, Apache)
3. **Configure HTTPS** with SSL certificates
4. **Set up proper logging** and monitoring
5. **Implement rate limiting** and security headers
6. **Use environment variables** for configuration

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review Podcastfy documentation
- Check server logs for error details

## 📄 License

This project is part of the Podcastfy ecosystem and follows the same licensing terms. 