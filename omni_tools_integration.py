"""
OMNI TOOLS INTEGRATION FOR PODCASTFY
====================================

This integrates the async Podcastfy service into your Omni Tools framework,
following the existing tool patterns in your codebase.
"""

import asyncio
import aiohttp
import json
import uuid
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum


class PodcastStatus(str, Enum):
    """Podcast generation status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class OmniPodcastTask:
    """Task tracking for Omni Tools"""
    task_id: str
    status: PodcastStatus
    audio_url: Optional[str] = None
    transcript_url: Optional[str] = None
    error: Optional[str] = None
    created_at: float = None
    completed_at: Optional[float] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization"""
        return asdict(self)


class OmniPodcastfyTool:
    """
    OMNI TOOLS COMPATIBLE PODCASTFY INTEGRATION
    
    This follows the same pattern as your existing tools (DaytonaToolRegistry, OperatorPodcastfyTool)
    but adds async capability for your Omni agent.
    """
    
    def __init__(self, base_url: str = "https://varnica-dev-podcastfy.onrender.com"):
        self.name = "podcastfy"
        self.description = "Generate AI-powered podcasts asynchronously from various content sources"
        self.version = "1.0.0"
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=300)
        self.tasks = {}  # Task storage (use Redis in production)
        
    def get_schema(self) -> Dict[str, Any]:
        """
        OMNI TOOLS SCHEMA
        
        Standard schema format for tool registration in Omni Tools.
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": "content_generation",
            "tags": ["podcast", "ai", "audio", "async", "tts"],
            "icon": "🎙️",
            "functions": {
                "generate": {
                    "description": "Start async podcast generation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Topic to generate podcast about"
                            },
                            "urls": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of URLs to extract content from"
                            },
                            "text": {
                                "type": "string",
                                "description": "Direct text content to convert to podcast"
                            },
                            "tts_model": {
                                "type": "string",
                                "enum": ["edge", "azure", "openai", "elevenlabs", "gemini"],
                                "default": "edge",
                                "description": "Text-to-speech model to use"
                            },
                            "conversation_style": {
                                "type": "string",
                                "enum": ["casual", "formal", "educational", "interview"],
                                "default": "casual",
                                "description": "Conversation style"
                            },
                            "longform": {
                                "type": "boolean",
                                "default": False,
                                "description": "Generate long-form content"
                            }
                        },
                        "oneOf": [
                            {"required": ["topic"]},
                            {"required": ["urls"]}, 
                            {"required": ["text"]}
                        ]
                    }
                },
                "check_status": {
                    "description": "Check status of a podcast generation task",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "Task ID from generate function"
                            }
                        },
                        "required": ["task_id"]
                    }
                },
                "list_tasks": {
                    "description": "List all active tasks",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        }
    
    async def execute(self, function_name: str, **kwargs) -> Dict[str, Any]:
        """
        OMNI TOOLS EXECUTE INTERFACE
        
        Main execution entry point for Omni Tools.
        Supports: generate, check_status, list_tasks
        """
        try:
            if function_name == "generate":
                return await self._generate_podcast(**kwargs)
            elif function_name == "check_status":
                return await self._check_status(kwargs.get("task_id"))
            elif function_name == "list_tasks":
                return await self._list_tasks()
            else:
                return {
                    "success": False,
                    "error": f"Unknown function: {function_name}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}"
            }
    
    async def _generate_podcast(
        self,
        topic: Optional[str] = None,
        urls: Optional[List[str]] = None,
        text: Optional[str] = None,
        tts_model: str = "edge",
        conversation_style: str = "casual",
        longform: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Start async podcast generation"""
        
        # Validate input
        if not topic and not urls and not text:
            return {
                "success": False,
                "error": "Must provide either topic, urls, or text"
            }
        
        # Create task
        task_id = f"omni_{uuid.uuid4().hex[:8]}"
        task = OmniPodcastTask(task_id=task_id, status=PodcastStatus.PENDING)
        self.tasks[task_id] = task
        
        # Build payload
        payload = {
            "tts_model": tts_model,
            "conversation_style": conversation_style,
            "longform": longform
        }
        
        if topic:
            payload["topic"] = topic
        elif urls:
            payload["urls"] = urls
        elif text:
            payload["text"] = text
        
        # Start background generation
        asyncio.create_task(self._background_generation(task_id, payload))
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "started",
            "message": f"🎙️ Podcast generation started (Task: {task_id})",
            "estimated_time": "1-3 minutes"
        }
    
    async def _background_generation(self, task_id: str, payload: Dict[str, Any]):
        """Background podcast generation"""
        task = self.tasks[task_id]
        task.status = PodcastStatus.PROCESSING
        
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
                            task.status = PodcastStatus.COMPLETED
                            task.audio_url = data.get("audio_url")
                            task.transcript_url = data.get("transcript_url")
                            task.completed_at = time.time()
                        else:
                            task.status = PodcastStatus.FAILED
                            task.error = data.get("error", "API returned failure")
                    else:
                        task.status = PodcastStatus.FAILED
                        task.error = f"HTTP {resp.status}: {await resp.text()}"
                        
        except asyncio.TimeoutError:
            task.status = PodcastStatus.FAILED
            task.error = "Generation timeout (5+ minutes)"
        except Exception as e:
            task.status = PodcastStatus.FAILED
            task.error = str(e)
    
    async def _check_status(self, task_id: str) -> Dict[str, Any]:
        """Check task status"""
        if not task_id:
            return {"success": False, "error": "Task ID required"}
        
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        
        result = {
            "success": True,
            "task_id": task_id,
            "status": task.status.value,
            "created_at": task.created_at
        }
        
        if task.status == PodcastStatus.COMPLETED:
            result.update({
                "audio_url": task.audio_url,
                "transcript_url": task.transcript_url,
                "completed_at": task.completed_at,
                "duration": task.completed_at - task.created_at if task.completed_at else None,
                "message": "🎉 Podcast is ready!"
            })
        elif task.status == PodcastStatus.FAILED:
            result.update({
                "error": task.error,
                "message": f"❌ Generation failed: {task.error}"
            })
        elif task.status == PodcastStatus.PROCESSING:
            result["message"] = "⏳ Podcast generation in progress..."
        else:
            result["message"] = "📋 Task queued for processing"
        
        return result
    
    async def _list_tasks(self) -> Dict[str, Any]:
        """List all tasks"""
        tasks_summary = []
        
        for task_id, task in self.tasks.items():
            summary = {
                "task_id": task_id,
                "status": task.status.value,
                "created_at": task.created_at
            }
            
            if task.status == PodcastStatus.COMPLETED:
                summary["audio_url"] = task.audio_url
                summary["completed_at"] = task.completed_at
            elif task.status == PodcastStatus.FAILED:
                summary["error"] = task.error
            
            tasks_summary.append(summary)
        
        return {
            "success": True,
            "tasks": tasks_summary,
            "total": len(tasks_summary)
        }


class OmniToolsRegistry:
    """
    OMNI TOOLS REGISTRY
    
    Registry that manages all Omni Tools, including the async Podcastfy tool.
    Similar to DaytonaToolRegistry but for Omni Tools framework.
    """
    
    def __init__(self):
        self.podcastfy_tool = OmniPodcastfyTool()
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, Any]:
        """Register all tools in the Omni Tools registry"""
        return {
            "podcastfy": {
                "tool": self.podcastfy_tool,
                "schema": self.podcastfy_tool.get_schema(),
                "examples": self._get_examples()
            }
        }
    
    def _get_examples(self) -> List[Dict[str, Any]]:
        """Get usage examples for Omni Tools"""
        return [
            {
                "name": "Generate from Topic",
                "description": "Create podcast about a specific topic",
                "function": "generate",
                "parameters": {
                    "topic": "The future of artificial intelligence",
                    "tts_model": "edge",
                    "conversation_style": "educational"
                },
                "expected_result": {
                    "success": True,
                    "task_id": "omni_abc12345",
                    "message": "🎙️ Podcast generation started"
                }
            },
            {
                "name": "Generate from URLs",
                "description": "Create podcast from web articles",
                "function": "generate", 
                "parameters": {
                    "urls": ["https://www.example.com/ai-news"],
                    "tts_model": "openai",
                    "conversation_style": "casual"
                }
            },
            {
                "name": "Check Status",
                "description": "Check podcast generation status",
                "function": "check_status",
                "parameters": {
                    "task_id": "omni_abc12345"
                },
                "expected_result": {
                    "success": True,
                    "status": "completed",
                    "audio_url": "https://...",
                    "message": "🎉 Podcast is ready!"
                }
            }
        ]
    
    def get_tool(self, tool_name: str) -> Optional[OmniPodcastfyTool]:
        """Get a tool from the registry"""
        tool_info = self.tools.get(tool_name)
        return tool_info["tool"] if tool_info else None
    
    def list_tools(self) -> List[str]:
        """List all available tools"""
        return list(self.tools.keys())
    
    async def execute_tool(self, tool_name: str, function_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool function"""
        tool = self.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool {tool_name} not found"}
        
        return await tool.execute(function_name, **kwargs)


# ============================================================================
# OMNI AGENT INTEGRATION LAYER
# ============================================================================

class OmniAgentPodcastInterface:
    """
    HIGH-LEVEL INTERFACE FOR YOUR OMNI AGENT
    
    This is the main class your Omni Agent should use.
    It provides a simple, clean interface for podcast generation.
    """
    
    def __init__(self):
        self.registry = OmniToolsRegistry()
        self.tool = self.registry.get_tool("podcastfy")
    
    async def generate_podcast(self, **kwargs) -> Dict[str, Any]:
        """Generate podcast - main entry point"""
        return await self.tool.execute("generate", **kwargs)
    
    async def check_status(self, task_id: str) -> Dict[str, Any]:
        """Check podcast status"""
        return await self.tool.execute("check_status", task_id=task_id)
    
    async def list_tasks(self) -> Dict[str, Any]:
        """List all tasks"""
        return await self.tool.execute("list_tasks")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for Omni Tools"""
        return self.tool.get_schema()


# ============================================================================
# USAGE EXAMPLES FOR YOUR OMNI AGENT
# ============================================================================

async def example_omni_agent_usage():
    """
    EXAMPLE: How your Omni Agent would use this
    """
    
    # Initialize the interface
    omni_agent = OmniAgentPodcastInterface()
    
    print("🤖 Omni Agent: Starting podcast generation...")
    
    # Generate podcast
    result = await omni_agent.generate_podcast(
        topic="The impact of AI on healthcare",
        tts_model="edge",
        conversation_style="educational"
    )
    
    print(f"📋 Result: {result}")
    
    if result["success"]:
        task_id = result["task_id"]
        print(f"✅ Started task: {task_id}")
        
        # Check status every 10 seconds
        while True:
            await asyncio.sleep(10)
            status = await omni_agent.check_status(task_id)
            print(f"📊 Status: {status['message']}")
            
            if status["status"] in ["completed", "failed"]:
                break
        
        if status["status"] == "completed":
            print(f"🎵 Audio URL: {status['audio_url']}")
            print(f"📝 Transcript: {status['transcript_url']}")
    else:
        print(f"❌ Error: {result['error']}")


# ============================================================================
# OMNI TOOLS CONFIGURATION
# ============================================================================

def get_omni_tools_config() -> Dict[str, Any]:
    """
    CONFIGURATION FOR OMNI TOOLS FRAMEWORK
    
    Return this configuration to register Podcastfy in your Omni Tools.
    """
    registry = OmniToolsRegistry()
    return {
        "tools": {
            "podcastfy": registry.tools["podcastfy"]["schema"]
        },
        "examples": registry.tools["podcastfy"]["examples"]
    }


# ============================================================================
# PRODUCTION USAGE NOTES
# ============================================================================

"""
INTEGRATION WITH YOUR OMNI AGENT:

1. **Basic Usage**:
   ```python
   from omni_tools_integration import OmniAgentPodcastInterface
   
   agent = OmniAgentPodcastInterface()
   result = await agent.generate_podcast(topic="AI Ethics")
   ```

2. **Register in Omni Tools**:
   ```python
   config = get_omni_tools_config()
   # Pass this config to your Omni Tools framework
   ```

3. **Handle in Agent Workflow**:
   ```python
   # In your agent's tool handler:
   if tool_name == "podcastfy":
       interface = OmniAgentPodcastInterface()
       return await interface.generate_podcast(**parameters)
   ```

4. **Status Management**:
   - Tasks are tracked automatically
   - Status updates happen in background
   - Use task_id to check progress
   - Clean up completed tasks periodically

5. **Error Handling**:
   - All methods return {"success": bool, ...}
   - Check "success" field before processing
   - Errors include descriptive messages
   - Timeouts are handled gracefully

6. **Production Considerations**:
   - Replace self.tasks with Redis for persistence
   - Add authentication if needed
   - Monitor API rate limits
   - Implement webhooks for real-time updates
"""

if __name__ == "__main__":
    # Test the integration
    asyncio.run(example_omni_agent_usage())