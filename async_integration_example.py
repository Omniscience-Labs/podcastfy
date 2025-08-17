"""
Async Integration Example for Omni Agent -> Podcastfy Service
=============================================================

This shows different patterns for calling Podcastfy asynchronously from your Omni agent.
"""

import asyncio
import aiohttp
import time
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class PodcastTask:
    """Represents an async podcast generation task"""
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    audio_url: Optional[str] = None
    transcript_url: Optional[str] = None
    error: Optional[str] = None
    created_at: float = None
    completed_at: Optional[float] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class AsyncPodcastfyClient:
    """
    Async client for calling Podcastfy service from Omni Agent
    
    Provides multiple patterns for async integration:
    1. Fire-and-Poll: Start task, poll for completion
    2. Fire-and-Forget: Start task, get notified later
    3. Concurrent Tasks: Handle multiple podcasts simultaneously
    """
    
    def __init__(self, base_url: str = "https://varnica-dev-podcastfy.onrender.com"):
        self.base_url = base_url.rstrip('/')
        self.tasks = {}  # In-memory task storage (use Redis in production)
        
    async def generate_podcast_async(
        self, 
        task_id: str,
        urls: Optional[list] = None,
        text: Optional[str] = None, 
        topic: Optional[str] = None,
        tts_model: str = "edge",
        **kwargs
    ) -> PodcastTask:
        """
        PATTERN 1: Fire-and-Poll
        
        Start podcast generation and return immediately with task_id.
        Use poll_task() to check completion status.
        """
        
        # Create task record
        task = PodcastTask(task_id=task_id, status="pending")
        self.tasks[task_id] = task
        
        # Start async generation (fire-and-forget)
        asyncio.create_task(self._generate_podcast_background(task_id, urls, text, topic, tts_model, **kwargs))
        
        return task
    
    async def _generate_podcast_background(
        self,
        task_id: str,
        urls: Optional[list] = None,
        text: Optional[str] = None,
        topic: Optional[str] = None,
        tts_model: str = "edge",
        **kwargs
    ):
        """Background task runner"""
        try:
            task = self.tasks[task_id]
            task.status = "processing"
            
            # Prepare payload
            payload = {
                "tts_model": tts_model,
                **kwargs
            }
            if urls:
                payload["urls"] = urls
            if text:
                payload["text"] = text
            if topic:
                payload["topic"] = topic
            
            # Make the actual API call
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            task.audio_url = data.get("audio_url")
                            task.transcript_url = data.get("transcript_url")
                            task.status = "completed"
                            task.completed_at = time.time()
                        else:
                            task.status = "failed"
                            task.error = data.get("error", "Unknown error")
                    else:
                        task.status = "failed"
                        task.error = f"HTTP {response.status}: {await response.text()}"
                        
        except Exception as e:
            self.tasks[task_id].status = "failed"
            self.tasks[task_id].error = str(e)
    
    async def poll_task(self, task_id: str) -> Optional[PodcastTask]:
        """Poll for task completion status"""
        return self.tasks.get(task_id)
    
    async def wait_for_completion(self, task_id: str, timeout: int = 300) -> PodcastTask:
        """
        PATTERN 2: Wait for Completion
        
        Block until task completes or timeout occurs.
        Useful for synchronous-style calls within async context.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            task = await self.poll_task(task_id)
            if task and task.status in ["completed", "failed"]:
                return task
            await asyncio.sleep(2)  # Poll every 2 seconds
        
        # Timeout occurred
        if task_id in self.tasks:
            self.tasks[task_id].status = "failed"
            self.tasks[task_id].error = "Timeout waiting for completion"
            return self.tasks[task_id]
        
        return PodcastTask(task_id=task_id, status="failed", error="Task not found")


class OmniAgentPodcastIntegration:
    """
    Example integration for your Omni Agent
    
    Shows how to integrate async podcast generation into your agent workflow.
    """
    
    def __init__(self):
        self.podcast_client = AsyncPodcastfyClient()
        self.active_tasks = {}
    
    async def handle_podcast_request(self, user_input: str) -> Dict[str, Any]:
        """
        OMNI AGENT INTEGRATION EXAMPLE
        
        This is how your Omni agent would handle podcast generation requests.
        """
        try:
            # Generate unique task ID
            import uuid
            task_id = f"podcast_{uuid.uuid4().hex[:8]}"
            
            # Parse user input (example)
            if "topic:" in user_input:
                topic = user_input.split("topic:")[1].strip()
                urls = None
                text = None
            elif "http" in user_input:
                urls = [url.strip() for url in user_input.split() if url.startswith("http")]
                topic = None
                text = None
            else:
                text = user_input
                topic = None
                urls = None
            
            # Start async podcast generation
            task = await self.podcast_client.generate_podcast_async(
                task_id=task_id,
                urls=urls,
                text=text,
                topic=topic,
                tts_model="edge"
            )
            
            # Store active task
            self.active_tasks[task_id] = task
            
            return {
                "status": "started",
                "task_id": task_id,
                "message": f"🎙️ Started podcast generation (ID: {task_id}). I'll let you know when it's ready!",
                "estimated_time": "1-3 minutes"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"❌ Failed to start podcast generation: {str(e)}"
            }
    
    async def check_podcast_status(self, task_id: str) -> Dict[str, Any]:
        """Check status of a podcast generation task"""
        task = await self.podcast_client.poll_task(task_id)
        
        if not task:
            return {"status": "not_found", "message": "Task not found"}
        
        if task.status == "completed":
            return {
                "status": "completed",
                "audio_url": task.audio_url,
                "transcript_url": task.transcript_url,
                "message": "🎉 Your podcast is ready!",
                "duration": f"{task.completed_at - task.created_at:.1f} seconds"
            }
        elif task.status == "failed":
            return {
                "status": "failed", 
                "error": task.error,
                "message": f"❌ Podcast generation failed: {task.error}"
            }
        else:
            return {
                "status": task.status,
                "message": f"⏳ Podcast generation in progress... ({task.status})"
            }
    
    async def handle_multiple_podcasts(self, requests: list) -> list:
        """
        PATTERN 3: Concurrent Tasks
        
        Handle multiple podcast requests simultaneously.
        """
        tasks = []
        for i, request in enumerate(requests):
            task_id = f"batch_podcast_{i}_{int(time.time())}"
            task = await self.podcast_client.generate_podcast_async(
                task_id=task_id,
                **request
            )
            tasks.append(task)
        
        return tasks


# ============================================================================
# USAGE EXAMPLES FOR YOUR OMNI AGENT
# ============================================================================

async def example_omni_agent_usage():
    """
    Example of how your Omni Agent would use async podcast generation
    """
    
    # Initialize the integration
    agent = OmniAgentPodcastIntegration()
    
    # Example 1: Start podcast generation
    print("🤖 Omni Agent: Starting podcast generation...")
    result = await agent.handle_podcast_request("topic: The Future of AI in Healthcare")
    print(f"Agent Response: {result['message']}")
    task_id = result['task_id']
    
    # Example 2: Check status periodically (non-blocking)
    print("\n🤖 Omni Agent: Checking status...")
    status = await agent.check_podcast_status(task_id)
    print(f"Status: {status['message']}")
    
    # Example 3: Wait for completion (if needed)
    print("\n🤖 Omni Agent: Waiting for completion...")
    final_task = await agent.podcast_client.wait_for_completion(task_id)
    if final_task.status == "completed":
        print(f"✅ Podcast ready!")
        print(f"🎵 Audio: {final_task.audio_url}")
        print(f"📝 Transcript: {final_task.transcript_url}")
    else:
        print(f"❌ Failed: {final_task.error}")


# Example for concurrent processing
async def example_batch_processing():
    """Example of processing multiple podcasts concurrently"""
    
    agent = OmniAgentPodcastIntegration()
    
    requests = [
        {"topic": "AI in Healthcare", "tts_model": "edge"},
        {"topic": "Climate Change Solutions", "tts_model": "edge"},
        {"topic": "Space Exploration", "tts_model": "edge"}
    ]
    
    print("🚀 Starting batch podcast generation...")
    tasks = await agent.handle_multiple_podcasts(requests)
    
    print(f"Started {len(tasks)} concurrent podcast generations!")
    
    # Wait for all to complete
    while True:
        completed = 0
        for task in tasks:
            current_task = await agent.podcast_client.poll_task(task.task_id)
            if current_task.status in ["completed", "failed"]:
                completed += 1
        
        if completed == len(tasks):
            break
        
        print(f"Progress: {completed}/{len(tasks)} completed")
        await asyncio.sleep(5)
    
    print("🎉 All podcasts completed!")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_omni_agent_usage())