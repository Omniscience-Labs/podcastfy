"""
SIMPLE OMNI AGENT INTEGRATION FOR PODCASTFY
==========================================

This is a streamlined example specifically for your Omni Agent + Cursor setup.
Focus on practical, production-ready async patterns.
"""

import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import uuid
import time


@dataclass
class PodcastRequest:
    """Simple podcast request structure"""
    topic: Optional[str] = None
    urls: Optional[list] = None
    text: Optional[str] = None
    tts_model: str = "edge"  # Free option: edge, paid: openai/elevenlabs
    style: str = "casual"    # casual, formal, educational, interview


@dataclass 
class PodcastResponse:
    """Podcast generation response"""
    success: bool
    task_id: str
    audio_url: Optional[str] = None
    transcript_url: Optional[str] = None
    error: Optional[str] = None
    status: str = "pending"  # pending, processing, completed, failed


class OmniAgentPodcastfy:
    """
    PRODUCTION-READY ASYNC INTEGRATION
    
    This is what you'd actually use in your Omni Agent.
    Clean, simple, handles errors gracefully.
    """
    
    def __init__(self):
        self.base_url = "https://varnica-dev-podcastfy.onrender.com"
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes max
        self.tasks = {}  # Store active tasks (use Redis in production)
    
    async def generate_podcast(self, request: PodcastRequest) -> PodcastResponse:
        """
        MAIN METHOD: Generate podcast asynchronously
        
        Usage in your Omni Agent:
        ```python
        request = PodcastRequest(topic="AI in Healthcare")
        response = await podcast_client.generate_podcast(request)
        
        if response.success:
            print(f"Started: {response.task_id}")
            # Check status later with: check_status(response.task_id)
        ```
        """
        task_id = f"omni_{uuid.uuid4().hex[:8]}"
        
        try:
            # Build payload
            payload = {
                "tts_model": request.tts_model,
                "conversation_style": request.style
            }
            
            if request.topic:
                payload["topic"] = request.topic
            elif request.urls:
                payload["urls"] = request.urls
            elif request.text:
                payload["text"] = request.text
            else:
                return PodcastResponse(
                    success=False, 
                    task_id=task_id, 
                    error="Must provide topic, URLs, or text"
                )
            
            # Start async generation
            response = PodcastResponse(success=True, task_id=task_id, status="processing")
            self.tasks[task_id] = response
            
            # Fire-and-forget background task
            asyncio.create_task(self._background_generation(task_id, payload))
            
            return response
            
        except Exception as e:
            return PodcastResponse(
                success=False, 
                task_id=task_id, 
                error=f"Failed to start: {str(e)}"
            )
    
    async def _background_generation(self, task_id: str, payload: Dict[str, Any]):
        """Background podcast generation"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success"):
                            # Success!
                            self.tasks[task_id].status = "completed"
                            self.tasks[task_id].audio_url = data.get("audio_url")
                            self.tasks[task_id].transcript_url = data.get("transcript_url")
                        else:
                            # API returned error
                            self.tasks[task_id].status = "failed"
                            self.tasks[task_id].error = data.get("error", "API returned failure")
                    else:
                        # HTTP error
                        self.tasks[task_id].status = "failed"
                        self.tasks[task_id].error = f"HTTP {resp.status}: {await resp.text()}"
                        
        except asyncio.TimeoutError:
            self.tasks[task_id].status = "failed"
            self.tasks[task_id].error = "Generation timeout (5+ minutes)"
        except Exception as e:
            self.tasks[task_id].status = "failed"
            self.tasks[task_id].error = str(e)
    
    async def check_status(self, task_id: str) -> Optional[PodcastResponse]:
        """
        CHECK TASK STATUS
        
        Usage in your Omni Agent:
        ```python
        status = await podcast_client.check_status(task_id)
        if status and status.status == "completed":
            print(f"Ready! {status.audio_url}")
        ```
        """
        return self.tasks.get(task_id)
    
    async def wait_for_completion(self, task_id: str, poll_interval: int = 3) -> Optional[PodcastResponse]:
        """
        BLOCKING WAIT (if needed)
        
        Only use if you need to wait for completion in your agent workflow.
        """
        while True:
            task = await self.check_status(task_id)
            if not task:
                return None
            
            if task.status in ["completed", "failed"]:
                return task
            
            await asyncio.sleep(poll_interval)


# ============================================================================
# OMNI AGENT INTEGRATION EXAMPLES
# ============================================================================

class OmniAgentExample:
    """Example of how your Omni Agent would use this"""
    
    def __init__(self):
        self.podcast_client = OmniAgentPodcastfy()
        self.active_tasks = {}
    
    async def handle_user_request(self, user_input: str) -> str:
        """
        MAIN AGENT HANDLER
        
        This is how your Omni Agent processes podcast requests.
        """
        
        # Parse user input (customize for your agent)
        if "podcast about" in user_input.lower():
            topic = user_input.lower().split("podcast about")[1].strip()
            request = PodcastRequest(topic=topic)
            
        elif "http" in user_input:
            urls = [url.strip() for url in user_input.split() if url.startswith("http")]
            request = PodcastRequest(urls=urls)
            
        else:
            # Default: treat as topic
            request = PodcastRequest(topic=user_input)
        
        # Generate podcast
        response = await self.podcast_client.generate_podcast(request)
        
        if response.success:
            self.active_tasks[response.task_id] = response
            return f"🎙️ Started podcast generation! Task ID: {response.task_id}\\n⏱️ This usually takes 1-3 minutes. I'll notify you when ready."
        else:
            return f"❌ Failed to start podcast: {response.error}"
    
    async def check_all_tasks(self) -> str:
        """Check status of all active tasks"""
        if not self.active_tasks:
            return "No active podcast tasks."
        
        results = []
        completed_tasks = []
        
        for task_id in list(self.active_tasks.keys()):
            status = await self.podcast_client.check_status(task_id)
            if not status:
                continue
                
            if status.status == "completed":
                results.append(f"✅ {task_id}: Ready! Audio: {status.audio_url}")
                completed_tasks.append(task_id)
            elif status.status == "failed":
                results.append(f"❌ {task_id}: Failed - {status.error}")
                completed_tasks.append(task_id)
            else:
                results.append(f"⏳ {task_id}: {status.status}")
        
        # Clean up completed tasks
        for task_id in completed_tasks:
            del self.active_tasks[task_id]
        
        return "\\n".join(results) if results else "No tasks found."


# ============================================================================
# USAGE EXAMPLES FOR TESTING
# ============================================================================

async def test_simple_usage():
    """Simple test example"""
    
    agent = OmniAgentExample()
    
    # Test 1: Generate podcast
    print("🤖 User: Create a podcast about artificial intelligence")
    response = await agent.handle_user_request("podcast about artificial intelligence")
    print(f"Agent: {response}")
    
    # Test 2: Wait a bit then check status
    await asyncio.sleep(5)
    print("\\n🤖 Checking status...")
    status = await agent.check_all_tasks()
    print(f"Agent: {status}")


async def test_concurrent_requests():
    """Test multiple concurrent requests"""
    
    client = OmniAgentPodcastfy()
    
    requests = [
        PodcastRequest(topic="Climate Change"),
        PodcastRequest(topic="Space Exploration"),
        PodcastRequest(topic="Machine Learning")
    ]
    
    print("🚀 Starting 3 concurrent podcasts...")
    responses = []
    for req in requests:
        resp = await client.generate_podcast(req)
        responses.append(resp)
        if resp.success:
            print(f"Started: {resp.task_id}")
    
    # Check progress every 10 seconds
    while True:
        await asyncio.sleep(10)
        
        completed = 0
        for resp in responses:
            if resp.success:
                status = await client.check_status(resp.task_id)
                if status and status.status in ["completed", "failed"]:
                    completed += 1
                    if status.status == "completed":
                        print(f"✅ {resp.task_id} completed: {status.audio_url}")
                    else:
                        print(f"❌ {resp.task_id} failed: {status.error}")
        
        print(f"Progress: {completed}/{len(responses)}")
        if completed == len(responses):
            break


# ============================================================================
# PRODUCTION TIPS FOR YOUR OMNI AGENT
# ============================================================================

"""
INTEGRATION TIPS FOR YOUR OMNI AGENT:

1. **Task Storage**: 
   - Use Redis instead of self.tasks for production
   - Persist tasks across agent restarts

2. **Error Handling**:
   - Always check response.success before proceeding
   - Handle timeouts gracefully (5+ minute podcasts are possible)
   - Log errors for debugging

3. **User Experience**:
   - Show progress updates ("Generation started...", "Still processing...")
   - Provide estimated completion times
   - Allow users to cancel long-running tasks

4. **Performance**:
   - Don't wait synchronously for completion in main thread
   - Use background tasks for polling
   - Consider webhooks if your service supports them

5. **Resource Management**:
   - Clean up completed tasks periodically
   - Limit concurrent requests per user
   - Monitor API rate limits

EXAMPLE OMNI AGENT COMMANDS:
- "Generate a podcast about AI ethics"
- "Create podcast from https://example.com/article"  
- "Check my podcast status"
- "List all active podcasts"
"""

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_simple_usage())