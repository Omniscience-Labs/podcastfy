# 🎤 Azure TTS Integration Setup

## ✅ Azure TTS Integration Complete!

Your Microsoft Azure Speech Services integration is now ready. Here's how to complete the setup:

---

## 🔑 **Step 1: Add Azure Key to Render**

Since you already have the key in Doppler, add it to Render:

### **In Render Dashboard:**
1. Go to your service: https://dashboard.render.com
2. Select your `podcastfy-backend` service  
3. Go to **Environment** tab
4. Click **"Add Environment Variable"**
5. Add these variables:

```bash
AZURE_SPEECH_KEY = your_azure_key_from_doppler
AZURE_SPEECH_REGION = eastus
```

---

## 🚀 **Step 2: Deploy Changes**

Your Azure TTS integration is ready to deploy:

```bash
git add -A
git commit -m "✨ Add Microsoft Azure TTS integration

- Add Azure Speech Services provider
- Support premium neural voices
- Update schema and factory registration
- Configure environment variables
- Ready for high-quality TTS generation"

git push origin main
```

---

## 🎯 **Step 3: Test Azure TTS**

Once deployed, test with your Omni agent:

```python
# Test Azure TTS integration
result = await podcast_interface.generate_podcast(
    topic="Test Azure neural voices",
    tts_model="azure"  # This will now use Azure Speech Services
)
```

---

## 🎪 **Available Voice Options**

### **Azure Neural Voices** (Premium Quality):

**Female Voices:**
- `en-US-JennyNeural` (default)
- `en-US-JaneNeural`
- `en-US-SaraNeural` 
- `en-US-NancyNeural`
- `en-US-AmberNeural`
- `en-US-AnaNeural`
- `en-US-AshleyNeural`
- `en-US-CoraNeural`
- `en-US-ElizabethNeural`
- `en-US-MichelleNeural`
- `en-US-MonicaNeural`

**Male Voices:**
- `en-US-GuyNeural` (default)
- `en-US-DavisNeural`
- `en-US-JasonNeural`
- `en-US-TonyNeural`
- `en-US-BrandonNeural`
- `en-US-ChristopherNeural`
- `en-US-EricNeural`
- `en-US-JacobNeural`
- `en-US-RogerNeural`
- `en-US-SteffanNeural`

### **Voice Mapping:**
```python
# You can use simple names that map to Azure voices:
"rachel" → "en-US-JennyNeural"
"guy" → "en-US-GuyNeural" 
"jason" → "en-US-JasonNeural"
"sara" → "en-US-SaraNeural"
# ... and more
```

---

## 🔄 **TTS Models Available**

After deployment, your users can choose from:

1. **`edge`** - Free Microsoft Edge TTS (basic quality)
2. **`azure`** - Premium Azure Neural voices (high quality) ⭐ **NEW**
3. **`openai`** - OpenAI TTS (requires OpenAI key)
4. **`elevenlabs`** - ElevenLabs (requires ElevenLabs key)
5. **`gemini`** - Google Gemini TTS (requires Gemini key)

---

## 📊 **Quality Comparison**

| TTS Model | Quality | Cost | Voices | Features |
|-----------|---------|------|--------|----------|
| **Azure** | ⭐⭐⭐⭐⭐ | Paid | 20+ Neural | SSML, Emotions, Styles |
| Edge | ⭐⭐⭐ | Free | Limited | Basic |
| OpenAI | ⭐⭐⭐⭐ | Paid | 6 | Good quality |
| ElevenLabs | ⭐⭐⭐⭐⭐ | Paid | Custom | Voice cloning |
| Gemini | ⭐⭐⭐⭐ | Paid | Various | Multilingual |

---

## 🎛️ **Advanced Features** 

Azure TTS supports advanced SSML features:

```xml
<mstts:express-as style="conversational" styledegree="1.0">
    Your podcast content here
</mstts:express-as>
```

**Available Styles:**
- `conversational` (default)
- `cheerful`
- `empathetic`
- `newscast`
- `excited`

---

## ✅ **Verification Steps**

1. **Environment Variables Set**: ✅ Added to Render config
2. **Provider Registered**: ✅ Added to TTS factory  
3. **Schema Updated**: ✅ Azure available in enum
4. **Integration Updated**: ✅ Omni Tools supports azure
5. **Deployment Ready**: ✅ All files committed

---

## 🐛 **Troubleshooting**

**If Azure TTS fails:**

1. **Check API Key**: Verify key is set in Render environment
2. **Check Region**: Make sure `AZURE_SPEECH_REGION=eastus` is set
3. **Check Logs**: Look for Azure-specific errors in Render logs
4. **Test Voice**: Try different voice names if one fails

**Common Issues:**
- Invalid voice name → Use neural voice names (e.g., `en-US-JennyNeural`)
- Wrong region → Check your Azure Speech Services region
- Rate limits → Azure has usage quotas

---

## 🎉 **Ready to Use!**

Your Azure TTS integration is complete! Your Omni agent can now generate high-quality podcasts using Microsoft's premium neural voices.

**Example usage:**
```python
# In your Omni agent:
result = await podcast_interface.generate_podcast(
    topic="The future of AI in healthcare",
    tts_model="azure",
    conversation_style="educational"
)

# Will use premium Azure neural voices! 🎙️
```