# 🚀 OMNI AGENT INTEGRATION GUIDE

## ✅ Deployment Status
Your Podcastfy service is now deployed and ready for Omni integration!

- **Service URL**: https://varnica-dev-podcastfy.onrender.com
- **Status**: ✅ Live and responding
- **Integration Files**: Ready in your repo

---

## 🎯 NEXT STEPS FOR YOUR OMNI AGENT

### **Step 1: Verify Service Connection**
Test your deployed service:
```bash
curl https://varnica-dev-podcastfy.onrender.com/api/health
# Should return: {"service":"podcastfy-backend","status":"healthy","version":"1.0.0"}
```

### **Step 2: Add Integration to Your Omni Agent**
In your `varnica-dev` branch in Omni, add these files from this repo:

**Required Files:**
1. `omni_tools_integration.py` - Core integration
2. `omni_tools_usage_example.py` - Usage examples

**Copy to your Omni project:**
```bash
# In your Omni project directory:
cp /path/to/podcastfy-2/omni_tools_integration.py ./tools/
cp /path/to/podcastfy-2/omni_tools_usage_example.py ./examples/
```

### **Step 3: Register the Tool in Your Omni Framework**
```python
# In your Omni agent setup:
from tools.omni_tools_integration import OmniAgentPodcastInterface, get_omni_tools_config

# Get configuration
config = get_omni_tools_config()

# Register in your Omni Tools registry
your_omni_registry.register_tool("podcastfy", config["tools"]["podcastfy"])
```

### **Step 4: Add to Your Agent's Command Handler**
```python
class YourOmniAgent:
    def __init__(self):
        self.podcast_tool = OmniAgentPodcastInterface()
    
    async def handle_command(self, command: str):
        if "podcast" in command.lower():
            # Parse and generate podcast
            result = await self.podcast_tool.generate_podcast(topic=command)
            return result["message"] if result["success"] else result["error"]
        
        # Your other command handlers...
```

---

## 🔍 HOW TO VERIFY OMNI CAN PICK UP THE INTEGRATION

### **Test 1: Connection Test**
In your Omni agent, run this test:
```python
import asyncio
from tools.omni_tools_integration import OmniAgentPodcastInterface

async def test_connection():
    interface = OmniAgentPodcastInterface()
    
    # Test service connection
    result = await interface.generate_podcast(topic="test")
    
    if result["success"]:
        print(f"✅ Connected! Task ID: {result['task_id']}")
        return result["task_id"]
    else:
        print(f"❌ Connection failed: {result['error']}")
        return None

# Run the test
task_id = asyncio.run(test_connection())
```

### **Test 2: Full Workflow Test**
```python
async def test_full_workflow():
    interface = OmniAgentPodcastInterface()
    
    # Start generation
    result = await interface.generate_podcast(
        topic="Artificial Intelligence in Healthcare",
        tts_model="edge"
    )
    
    if result["success"]:
        task_id = result["task_id"]
        print(f"✅ Started: {task_id}")
        
        # Poll until complete
        while True:
            await asyncio.sleep(10)
            status = await interface.check_status(task_id)
            
            print(f"Status: {status['message']}")
            
            if status["status"] in ["completed", "failed"]:
                break
        
        if status["status"] == "completed":
            print(f"🎵 Audio: {status['audio_url']}")
            print(f"📝 Transcript: {status['transcript_url']}")
    else:
        print(f"❌ Failed: {result['error']}")

# Run full test
asyncio.run(test_full_workflow())
```

### **Test 3: Schema Validation**
```python
from tools.omni_tools_integration import get_omni_tools_config

# Verify schema
config = get_omni_tools_config()
print("✅ Tool Schema:", config["tools"]["podcastfy"]["name"])
print("✅ Functions:", list(config["tools"]["podcastfy"]["functions"].keys()))
```

---

## 🎪 EXAMPLE COMMANDS FOR YOUR OMNI AGENT

Once integrated, your Omni agent can handle commands like:

```
User: "Create a podcast about the future of renewable energy"
Agent: "🎙️ Podcast generation started! Task ID: omni_abc12345
        ⏱️ This usually takes 1-3 minutes. I'll notify you when ready."

User: "Check status of task omni_abc12345"  
Agent: "⏳ Podcast generation in progress..."

User: "Check status of task omni_abc12345"
Agent: "🎉 Podcast is ready! 
       🎵 Audio: https://varnica-dev-podcastfy.onrender.com/api/audio/podcast_xyz.mp3
       📝 Transcript: https://varnica-dev-podcastfy.onrender.com/api/transcript/transcript_xyz.txt"

User: "List my active tasks"
Agent: "Active Tasks (2):
       📋 omni_abc12345: completed ✅
       📋 omni_def67890: processing ⏳"
```

---

## 🔧 INTEGRATION CHECKLIST

**Before Testing:**
- [ ] Service is deployed and responding: https://varnica-dev-podcastfy.onrender.com/api/health
- [ ] Integration files copied to your Omni project
- [ ] Dependencies installed: `pip install aiohttp`

**Integration Steps:**
- [ ] Tool registered in Omni framework
- [ ] Command handlers updated
- [ ] Test connection works
- [ ] Full workflow test passes

**Production Ready:**
- [ ] Error handling implemented
- [ ] Task cleanup scheduled  
- [ ] Monitoring/logging added
- [ ] Rate limiting considered

---

## 🚨 TROUBLESHOOTING

### **Common Issues:**

**1. Connection Errors**
```python
# Check if service is up
curl https://varnica-dev-podcastfy.onrender.com/api/health

# If down, check Render logs
```

**2. Import Errors**
```python
# Make sure files are in the right location
ls tools/omni_tools_integration.py

# Check Python path
import sys
print(sys.path)
```

**3. Async Errors**
```python
# Make sure you're running in async context
import asyncio

# Wrong:
result = interface.generate_podcast(topic="test")

# Right:
result = await interface.generate_podcast(topic="test")
```

**4. Task Not Found**
```python
# Tasks are stored in memory - they reset on restart
# For production, implement Redis storage
```

---

## 📞 SERVICE ENDPOINTS

Your deployed service provides these endpoints:

- **Health Check**: `GET /api/health`
- **Generate Podcast**: `POST /api/generate`
- **Get Audio**: `GET /api/audio/<filename>`
- **Get Transcript**: `GET /api/transcript/<filename>`

**Base URL**: `https://varnica-dev-podcastfy.onrender.com`

---

## 🎯 SUCCESS CRITERIA

You'll know the integration is working when:

1. ✅ Your Omni agent can import the integration files
2. ✅ Connection test returns a task ID  
3. ✅ Status checks return valid responses
4. ✅ Full workflow generates audio and transcript URLs
5. ✅ Your agent can handle podcast commands naturally

**Ready to integrate!** 🚀