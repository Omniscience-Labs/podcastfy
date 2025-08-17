"""
QUICK START: OMNI TOOLS + PODCASTFY INTEGRATION
===============================================

This shows exactly how to integrate Podcastfy into your Omni Tools framework.
Copy and adapt this for your specific Omni Agent setup.
"""

import asyncio
from omni_tools_integration import OmniAgentPodcastInterface, OmniToolsRegistry, get_omni_tools_config


class YourOmniAgent:
    """
    EXAMPLE: Your Omni Agent with Podcastfy Integration
    
    This shows how to integrate the Podcastfy tool into your existing Omni Agent.
    """
    
    def __init__(self):
        self.podcast_interface = OmniAgentPodcastInterface()
        self.tools = self._setup_tools()
    
    def _setup_tools(self):
        """Setup all your Omni Tools"""
        # Get Podcastfy tool configuration
        config = get_omni_tools_config()
        
        return {
            "podcastfy": {
                "interface": self.podcast_interface,
                "schema": config["tools"]["podcastfy"],
                "examples": config["examples"]
            }
            # Add your other tools here...
        }
    
    async def handle_user_command(self, command: str) -> str:
        """
        MAIN COMMAND HANDLER
        
        This is how your Omni Agent would process user commands.
        """
        
        command_lower = command.lower()
        
        # Podcast generation commands
        if "podcast" in command_lower or "audio" in command_lower:
            return await self._handle_podcast_command(command)
        
        # Status check commands  
        elif "status" in command_lower and "task" in command_lower:
            return await self._handle_status_command(command)
        
        # List tasks commands
        elif "list" in command_lower and "task" in command_lower:
            return await self._handle_list_command()
        
        else:
            return "I can help you generate podcasts! Try: 'Create a podcast about AI ethics'"
    
    async def _handle_podcast_command(self, command: str) -> str:
        """Handle podcast generation commands"""
        
        # Simple command parsing (customize for your needs)
        if "about" in command:
            topic = command.split("about")[1].strip()
            result = await self.podcast_interface.generate_podcast(topic=topic)
        elif "http" in command:
            urls = [url.strip() for url in command.split() if url.startswith("http")]
            result = await self.podcast_interface.generate_podcast(urls=urls)
        else:
            # Treat entire command as topic
            topic = command.replace("podcast", "").replace("create", "").strip()
            result = await self.podcast_interface.generate_podcast(topic=topic)
        
        if result["success"]:
            return f"🎙️ {result['message']}\\nTask ID: {result['task_id']}\\nEstimated time: {result.get('estimated_time', '1-3 minutes')}"
        else:
            return f"❌ Failed to start podcast: {result['error']}"
    
    async def _handle_status_command(self, command: str) -> str:
        """Handle status check commands"""
        
        # Extract task ID (simple parsing)
        words = command.split()
        task_id = None
        for word in words:
            if word.startswith("omni_"):
                task_id = word
                break
        
        if not task_id:
            return "Please provide a task ID. Example: 'Check status of task omni_abc12345'"
        
        result = await self.podcast_interface.check_status(task_id)
        
        if result["success"]:
            return result["message"]
        else:
            return f"❌ {result['error']}"
    
    async def _handle_list_command(self) -> str:
        """Handle list tasks commands"""
        
        result = await self.podcast_interface.list_tasks()
        
        if result["success"] and result["tasks"]:
            tasks_info = []
            for task in result["tasks"]:
                info = f"📋 {task['task_id']}: {task['status']}"
                if task['status'] == 'completed':
                    info += " ✅"
                elif task['status'] == 'failed':
                    info += " ❌"
                elif task['status'] == 'processing':
                    info += " ⏳"
                tasks_info.append(info)
            
            return f"Active Tasks ({result['total']}):\\n" + "\\n".join(tasks_info)
        else:
            return "No active tasks found."


# ============================================================================
# INTEGRATION EXAMPLES
# ============================================================================

async def example_1_basic_usage():
    """Example 1: Basic Omni Agent Usage"""
    
    print("=== Example 1: Basic Usage ===")
    agent = YourOmniAgent()
    
    # User command examples
    commands = [
        "Create a podcast about artificial intelligence in healthcare",
        "Generate podcast from https://www.example.com/ai-news", 
        "Make a podcast about climate change solutions"
    ]
    
    for command in commands:
        print(f"\\n👤 User: {command}")
        response = await agent.handle_user_command(command)
        print(f"🤖 Agent: {response}")


async def example_2_full_workflow():
    """Example 2: Complete Workflow"""
    
    print("\\n=== Example 2: Full Workflow ===")
    agent = YourOmniAgent()
    
    # Start podcast generation
    print("👤 User: Create a podcast about the future of space exploration")
    response = await agent.handle_user_command("Create a podcast about the future of space exploration")
    print(f"🤖 Agent: {response}")
    
    # Extract task ID (in real implementation, store this)
    task_id = None
    if "omni_" in response:
        start = response.find("omni_")
        end = start + 12  # omni_ + 8 chars
        task_id = response[start:end]
    
    if task_id:
        # Check status periodically
        for i in range(3):
            await asyncio.sleep(10)  # Wait 10 seconds
            print(f"\\n👤 User: Check status of task {task_id}")
            status_response = await agent.handle_user_command(f"Check status of task {task_id}")
            print(f"🤖 Agent: {status_response}")
            
            if "ready" in status_response.lower() or "failed" in status_response.lower():
                break


async def example_3_tool_registration():
    """Example 3: Tool Registration in Omni Framework"""
    
    print("\\n=== Example 3: Tool Registration ===")
    
    # Get tool configuration for registration
    config = get_omni_tools_config()
    
    print("📋 Podcastfy Tool Schema:")
    print(f"Name: {config['tools']['podcastfy']['name']}")
    print(f"Description: {config['tools']['podcastfy']['description']}")
    print(f"Functions: {list(config['tools']['podcastfy']['functions'].keys())}")
    
    print("\\n📚 Available Examples:")
    for i, example in enumerate(config['examples'], 1):
        print(f"{i}. {example['name']}: {example['description']}")


# ============================================================================
# QUICK INTEGRATION GUIDE
# ============================================================================

"""
STEP-BY-STEP INTEGRATION FOR YOUR OMNI AGENT:

1. **Install Dependencies**:
   ```bash
   pip install aiohttp
   ```

2. **Import the Integration**:
   ```python
   from omni_tools_integration import OmniAgentPodcastInterface
   ```

3. **Add to Your Agent**:
   ```python
   class YourAgent:
       def __init__(self):
           self.podcast_tool = OmniAgentPodcastInterface()
   
       async def handle_command(self, command):
           if "podcast" in command:
               result = await self.podcast_tool.generate_podcast(topic=command)
               return result["message"] if result["success"] else result["error"]
   ```

4. **Register in Omni Tools Framework**:
   ```python
   from omni_tools_integration import get_omni_tools_config
   
   config = get_omni_tools_config()
   # Pass config to your Omni Tools registry
   your_omni_framework.register_tool("podcastfy", config["tools"]["podcastfy"])
   ```

5. **Handle Async Responses**:
   - Always check result["success"] 
   - Store task_id for status checking
   - Poll status until completion
   - Handle errors gracefully

6. **Production Setup**:
   - Replace in-memory task storage with Redis
   - Add authentication if needed
   - Set up monitoring and logging
   - Consider webhooks for real-time updates
"""


# ============================================================================
# TESTING YOUR INTEGRATION
# ============================================================================

async def test_integration():
    """Test your Omni Tools integration"""
    
    print("🧪 Testing Omni Tools Integration...")
    
    try:
        # Test 1: Tool initialization
        agent = YourOmniAgent()
        print("✅ Agent initialized successfully")
        
        # Test 2: Schema retrieval
        schema = agent.podcast_interface.get_schema()
        assert schema["name"] == "podcastfy"
        print("✅ Schema validation passed")
        
        # Test 3: Command handling (without actual generation)
        response = await agent.handle_user_command("help")
        assert "podcast" in response.lower()
        print("✅ Command handling works")
        
        print("🎉 All tests passed! Integration is ready.")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")


if __name__ == "__main__":
    print("🚀 OMNI TOOLS + PODCASTFY INTEGRATION EXAMPLES\\n")
    
    # Run all examples
    asyncio.run(example_1_basic_usage())
    asyncio.run(example_2_full_workflow()) 
    asyncio.run(example_3_tool_registration())
    asyncio.run(test_integration())