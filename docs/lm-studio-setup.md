# LM Studio Setup Guide: 3-Phase Local Model Migration with Python SDK

## Overview

This guide covers **Phase 2** and **Phase 3** of your migration to local models with deep research capabilities using the **LM Studio Python SDK** for programmatic model management.

**Migration Flow**:
- **Phase 1**: ✅ OpenAI → LiteLLM (completed first)
- **Phase 2**: 🎯 LiteLLM → Local Models via LM Studio Python SDK (this guide)
- **Phase 3**: 🚀 Multi-Agent Deep Research (advanced setup)

**Prerequisites**: Your AI agents should already be using `litellm.completion()` calls from Phase 1.

**Architecture Overview**:
```
Your Agents → LiteLLM (API abstraction) → LM Studio Python SDK (model management) → lms CLI (backend service) → Local Models
```

## Component Architecture

### The Three LM Studio Components

**1. `lms` CLI (Backend Service)** - ⚠️ **REQUIRED**
- Provides model execution infrastructure
- Handles GPU management and model loading
- Runs as background service
- Download and installation: Ships with LM Studio 0.2.22+

**2. LM Studio Python SDK** - ✅ **Primary Interface**
- Programmatic model management via `pip install lmstudio`
- Model loading, unloading, and configuration via Python code
- Agentic flows with `.act()` API for autonomous behavior
- Replaces Desktop GUI for programmatic control

**3. LM Studio Desktop** - ❌ **NOT NEEDED for your use case**
- GUI application for manual model management
- Useful for initial setup and testing
- NOT required when using Python SDK + CLI backend

**Confirmed**: You can skip LM Studio Desktop and use Python SDK + CLI backend for a more cohesive solution.

## Hardware Requirements

### Minimum Setup (Testing)
- **GPU**: RTX 4090 (24GB VRAM)
- **RAM**: 64GB system memory
- **Storage**: 1TB NVMe SSD
- **Models Supported**: Up to 70B parameters

### Recommended Setup (Production)
- **GPU**: 2x RTX 4090 or 2x A6000 (48GB total VRAM)
- **RAM**: 128GB system memory
- **Storage**: 4TB NVMe SSD
- **Models Supported**: Up to 405B parameters

## Installation & Setup

### Step 1: Install LM Studio CLI Backend
```bash
# Download LM Studio (includes lms CLI)
wget https://lmstudio.ai/download/linux
chmod +x lmstudio-*.AppImage

# Or on macOS
brew install --cask lm-studio

# Add lms CLI to PATH (if not automatically added)
npx lmstudio install-cli

# Verify CLI installation
lms --help
```

### Step 2: Install LM Studio Python SDK
```bash
# Install via pip (Python 3.10+ required)
pip install lmstudio

# Verify installation
python -c "import lmstudio as lms; print('LM Studio SDK installed successfully')"
```

### Step 3: Start Backend Service
```bash
# Check if LM Studio backend is running
lms status

# Start the local API server (if not running)
lms server start

# Verify server is running on default port
curl http://localhost:1234/v1/models
```

## Model Downloads by Phase

### Phase 2: Enhanced 2-Model Setup with Python SDK

**For your specific codebase** (programmatic approach):

```python
# Download and manage models via Python SDK
import lmstudio as lms

async def setup_phase2_models():
    client = lms.Client()
    
    # Model 1: General purpose (replaces gpt-4.1)
    print("Setting up general model...")
    await client.models.download("qwen2.5-72b-instruct-q4_k_m.gguf")
    
    # Model 2: Reasoning (replaces o3)  
    print("Setting up reasoning model...")
    await client.models.download("deepseek-r1-distill-qwen-32b-q4_k_m.gguf")
    
    print("✓ Phase 2 models ready")

# Or via CLI
# lms get qwen2.5-72b-instruct
# lms get deepseek-r1-distill-qwen-32b
```

**Model Mapping**:
```
1. Qwen/Qwen2.5-72B-Instruct-GGUF → Replaces ALL gpt-4.1 usage
   - File: qwen2.5-72b-instruct-q4_k_m.gguf
   - Size: ~42GB
   - Purpose: ResearchAgent, SummaryAgent, all general tasks
   - VRAM: ~24GB
   - Management: Auto-load via Python SDK

2. deepseek-ai/DeepSeek-R1-Distill-Qwen-32B-GGUF → Replaces ALL o3 reasoning
   - File: deepseek-r1-distill-qwen-32b-q4_k_m.gguf
   - Size: ~19GB  
   - Purpose: QuestionAgent reasoning (consolidates o3, o4-mini fallbacks)
   - VRAM: ~12GB
   - Management: Smart loading for reasoning tasks
```

### Phase 3: Deep Research Enhancement

```
3. Multi-Agent Deep Research System → Replaces o4-mini-deep-research
   - Purpose: Replace expensive $200/1M token deep research
   - Current usage: config/config.py DEEP_RESEARCH_CONFIG  
   - Implementation: Phase 3 supervisor + research agents
   - Models: Uses the same 2 models above in multi-agent coordination
   - Enhanced with: Web search, iterative research, thinking content
   - Orchestration: LM Studio SDK `.act()` API for autonomous agents
```

## Phase 2: Python SDK Model Management

### Step 1: Programmatic Model Loading
```python
# agents/model_manager.py
import lmstudio as lms
import asyncio
from typing import Dict, Optional

class LMStudioModelManager:
    def __init__(self):
        self.client = lms.Client()
        self.loaded_models = {}
        self.model_configs = {
            'qwen2.5-72b-instruct': {
                'gpu_layers': -1,
                'context_length': 32768,
                'batch_size': 512
            },
            'deepseek-r1-distill-qwen-32b': {
                'gpu_layers': -1,
                'context_length': 65536,  # Larger for reasoning
                'batch_size': 256
            }
        }
    
    async def ensure_model_loaded(self, model_name: str) -> bool:
        """Load model if not already loaded"""
        # For LM Studio setup, model_name is already the local model identifier
        # Check if already in cache
        if model_name in self.loaded_models:
            return True
            
        # Check if already loaded in backend
        loaded = await self.client.models.list_loaded()
        if any(m.identifier == model_name for m in loaded):
            # Model is loaded in backend but not in our cache, update cache
            self.loaded_models[model_name] = True
            return True
            
        # Load the model with configuration
        try:
            config = self.model_configs.get(model_name, {})
            model = await self.client.models.load(model_name, config=config)
            self.loaded_models[model_name] = model  # Cache using local model name
            print(f"✓ Loaded {model_name}")
            return True
        except Exception as e:
            print(f"✗ Failed to load {model_name}: {e}")
            return False
    
    async def smart_model_switching(self, task_type: str) -> str:
        """Switch models based on task requirements"""
        if task_type == 'reasoning':
            model_name = 'deepseek-r1-distill-qwen-32b'
            # Optionally unload general model to free memory
            await self.unload_model('qwen2.5-72b-instruct')
        else:
            model_name = 'qwen2.5-72b-instruct'
            
        await self.ensure_model_loaded(model_name)
        return model_name
    
    async def unload_model(self, model_name: str):
        """Unload model to free GPU memory"""
        if model_name in self.loaded_models:
            try:
                model = self.loaded_models[model_name]
                if hasattr(model, 'unload'):
                    await model.unload()
                del self.loaded_models[model_name]
                print(f"✓ Unloaded {model_name}")
            except Exception as e:
                print(f"✗ Failed to unload {model_name}: {e}")
```

### Step 2: Integration with LiteLLM
```python
# integration/enhanced_completion.py
import litellm
import lmstudio as lms
from typing import Dict, Any

class EnhancedCompletion:
    """
    Bridges LiteLLM's API abstraction with LM Studio SDK's model management
    """
    
    def __init__(self, model_manager: LMStudioModelManager):
        self.model_manager = model_manager
        self.model_mapping = {
            'gpt-4.1': 'qwen2.5-72b-instruct',
            'o3': 'deepseek-r1-distill-qwen-32b',
            'o4-mini': 'deepseek-r1-distill-qwen-32b',
        }
    
    async def completion(self, model: str, messages: list, **kwargs) -> Any:
        """
        Enhanced completion with automatic model management
        """
        # Map OpenAI model to local model
        local_model = self.model_mapping.get(model, model)
        
        # Ensure model is loaded via LM Studio SDK (using local model name)
        await self.model_manager.ensure_model_loaded(local_model)
        
        # Route through LiteLLM to LM Studio's OpenAI-compatible API using local model name
        return litellm.completion(
            model=f"lm_studio/{local_model}",  # Use local model name with LM Studio prefix
            messages=messages,
            api_base="http://localhost:1234/v1",
            api_key="local-key",  # Not validated by local server
            **kwargs
        )

# Usage in your agents
async def enhanced_agent_example():
    model_manager = LMStudioModelManager()
    completion_handler = EnhancedCompletion(model_manager)
    
    # This will auto-load qwen2.5-72b-instruct and route through LiteLLM
    response = await completion_handler.completion(
        model="gpt-4.1",
        messages=[{"role": "user", "content": "Analyze this project"}]
    )
    
    return response.choices[0].message.content
```

## Phase 2: Agentic Capabilities

### LM Studio SDK's `.act()` API
```python
# agents/autonomous_agent.py
import lmstudio as lms
from typing import List, Callable

class AutonomousResearchAgent:
    def __init__(self):
        # Auto-loads model if not already loaded
        self.model = lms.llm("qwen2.5-72b-instruct")
    
    async def autonomous_research(self, topic: str) -> Dict:
        """
        Use LM Studio's .act() API for multi-step autonomous research
        """
        
        def search_web(query: str) -> str:
            """Tool: Web search functionality"""
            # Integrate with your search implementation
            return f"Search results for: {query}"
        
        def analyze_data(data: str) -> str:
            """Tool: Data analysis functionality"""
            # Your analysis logic
            return f"Analysis: {data}"
        
        def save_findings(findings: str) -> str:
            """Tool: Save research findings"""
            # Save to database or file
            return f"Saved: {findings}"
        
        # Multi-round autonomous execution
        result = await self.model.act(
            prompt=f"Research {topic} comprehensively. Use available tools to gather information, analyze it, and save your findings.",
            tools=[search_web, analyze_data, save_findings],
            max_rounds=10,  # Allow up to 10 autonomous steps
            on_message=lambda msg: print(f"🤖 Agent: {msg}")
        )
        
        return {
            "topic": topic,
            "result": result,
            "methodology": "autonomous-lmstudio-sdk"
        }
```

## Testing by Phase

### Phase 2: Verify Python SDK Integration
```python
# test_lmstudio_sdk.py
import lmstudio as lms
import litellm
import asyncio

async def test_sdk_integration():
    """Test LM Studio Python SDK + LiteLLM integration"""
    
    print("1. Testing LM Studio SDK connection...")
    client = lms.Client()
    
    # Test model loading
    print("2. Loading test model...")
    try:
        model = await client.models.load("qwen2.5-72b-instruct")
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"✗ Model loading failed: {e}")
        return
    
    # Test direct SDK usage
    print("3. Testing direct SDK completion...")
    llm = lms.llm("qwen2.5-72b-instruct")
    sdk_result = llm.respond("Hello, test message")
    print(f"✓ SDK Response: {sdk_result}")
    
    # Test LiteLLM integration
    print("4. Testing LiteLLM integration...")
    litellm_result = litellm.completion(
        model="lm_studio/qwen2.5-72b-instruct",
        messages=[{"role": "user", "content": "Hello from LiteLLM"}],
        api_base="http://localhost:1234/v1"
    )
    print(f"✓ LiteLLM Response: {litellm_result.choices[0].message.content}")
    
    print("5. Testing autonomous agent (.act() API)...")
    def simple_tool(input_text: str) -> str:
        return f"Tool processed: {input_text}"
    
    act_result = await llm.act(
        prompt="Use the tool to process 'test data'",
        tools=[simple_tool],
        max_rounds=2
    )
    print(f"✓ Autonomous result: {act_result}")
    
    print("\n🎉 All tests passed! LM Studio SDK + LiteLLM integration working.")

# Run tests
if __name__ == "__main__":
    asyncio.run(test_sdk_integration())
```

### Phase 2: Test Your Existing Agents
```python
# test_agent_integration.py
from agents.research_agent import ResearchAgent
from agents.model_manager import LMStudioModelManager
from integration.enhanced_completion import EnhancedCompletion
import asyncio

async def test_agent_integration():
    """Test that your existing agents work with enhanced local setup"""
    
    # Initialize enhanced components
    model_manager = LMStudioModelManager()
    completion_handler = EnhancedCompletion(model_manager)
    
    # Test research agent with local models
    print("Testing ResearchAgent with local models...")
    
    # Modify your agent to use enhanced completion
    class EnhancedResearchAgent(ResearchAgent):
        def __init__(self):
            super().__init__()
            self.completion_handler = completion_handler
        
        async def research(self, project_name: str):
            # Use enhanced completion instead of direct OpenAI/LiteLLM
            response = await self.completion_handler.completion(
                model="gpt-4.1",  # Will auto-load qwen2.5-72b-instruct
                messages=[{
                    "role": "user", 
                    "content": f"Research project: {project_name}"
                }]
            )
            return {"analysis": response.choices[0].message.content}
    
    # Test the enhanced agent
    agent = EnhancedResearchAgent()
    result = await agent.research("test project")
    print(f"✓ Agent Result: {result['analysis'][:100]}...")
    
    print("🎉 Agent integration test passed!")

if __name__ == "__main__":
    asyncio.run(test_agent_integration())
```

## Performance Optimization

### Memory Management with Python SDK
```python
# performance/memory_optimizer.py
import lmstudio as lms
from typing import Dict
import psutil

class MemoryOptimizer:
    def __init__(self, client: lms.Client):
        self.client = client
        self.memory_threshold = 0.85  # 85% VRAM usage threshold
    
    async def optimize_model_loading(self, required_model: str):
        """Smart model loading with memory optimization"""
        
        # Check current GPU memory usage
        gpu_usage = self.get_gpu_memory_usage()
        
        if gpu_usage > self.memory_threshold:
            print(f"GPU memory at {gpu_usage:.1%}, optimizing...")
            await self.unload_least_used_models()
        
        # Load required model
        await self.client.models.load(required_model)
    
    def get_gpu_memory_usage(self) -> float:
        """Get current GPU memory usage percentage"""
        # Implementation depends on your GPU monitoring setup
        # This is a placeholder
        return 0.5  # 50% usage
    
    async def unload_least_used_models(self):
        """Unload models that haven't been used recently"""
        loaded_models = await self.client.models.list_loaded()
        
        # Implement LRU-based unloading
        for model in loaded_models[:-1]:  # Keep the most recent one
            await model.unload()
            print(f"Unloaded {model.identifier} to free memory")
```

### Request Optimization
```python
# performance/request_optimizer.py
import lmstudio as lms

class RequestOptimizer:
    def __init__(self):
        self.default_config = {
            'temperature': 0.1,      # Deterministic outputs
            'top_p': 0.9,           # Nucleus sampling
            'max_tokens': 2048,     # Reasonable limit
            'stream': False,        # Disable if not needed
            'batch_size': 512,      # Optimize for throughput
        }
    
    async def optimized_completion(self, model_name: str, messages: list, **kwargs):
        """Completion with optimized parameters"""
        # Merge default config with custom parameters
        config = {**self.default_config, **kwargs}
        
        model = lms.llm(model_name)
        return model.respond(messages, **config)
```

## Monitoring and Health Checks

### LM Studio SDK Health Monitoring
```python
# monitoring/health_checker.py
import lmstudio as lms
import asyncio
from datetime import datetime

class LMStudioHealthChecker:
    def __init__(self):
        self.client = lms.Client()
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for LM Studio setup"""
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'backend_service': await self.check_backend_service(),
            'python_sdk': await self.check_python_sdk(),
            'model_loading': await self.check_model_loading(),
            'api_endpoints': await self.check_api_endpoints(),
            'memory_usage': await self.check_memory_usage()
        }
        
        return health_status
    
    async def check_backend_service(self) -> Dict[str, Any]:
        """Check if lms CLI backend is running"""
        try:
            # Try to connect to the client
            models = await self.client.models.list_loaded()
            return {'status': 'healthy', 'loaded_models': len(models)}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def check_python_sdk(self) -> Dict[str, Any]:
        """Check Python SDK functionality"""
        try:
            # Test basic SDK operations
            available_models = await self.client.models.list_downloaded()
            return {'status': 'healthy', 'available_models': len(available_models)}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def check_model_loading(self) -> Dict[str, Any]:
        """Test model loading capability"""
        try:
            # Try to load a small test model
            test_model = "llama-3.2-1b-instruct"  # Small model for testing
            model = await self.client.models.load(test_model)
            await model.unload()  # Clean up
            return {'status': 'healthy', 'test_model': test_model}
        except Exception as e:
            return {'status': 'warning', 'message': 'Model loading test failed', 'error': str(e)}
    
    async def check_api_endpoints(self) -> Dict[str, Any]:
        """Check OpenAI-compatible API endpoints"""
        import requests
        try:
            response = requests.get("http://localhost:1234/v1/models", timeout=5)
            return {'status': 'healthy', 'http_status': response.status_code}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def check_memory_usage(self) -> Dict[str, Any]:
        """Check system and GPU memory usage"""
        import psutil
        
        return {
            'system_memory': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            # Add GPU memory checking based on your setup
        }

# Continuous monitoring
async def continuous_monitoring(interval_seconds: int = 30):
    """Run continuous health monitoring"""
    checker = LMStudioHealthChecker()
    
    while True:
        try:
            health = await checker.comprehensive_health_check()
            print(f"Health Check: {health['backend_service']['status']}")
            
            # Alert on issues
            if health['backend_service']['status'] != 'healthy':
                print(f"⚠️ Backend service issue: {health['backend_service']}")
            
            await asyncio.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("Monitoring stopped")
            break
        except Exception as e:
            print(f"Monitoring error: {e}")
            await asyncio.sleep(interval_seconds)
```

## Troubleshooting

### Common Issues with Python SDK

**1. SDK Connection Failed**
```bash
Error: Cannot connect to LM Studio
Solution: 
- Ensure lms CLI backend is running: `lms status`
- Start backend if needed: `lms server start`
- Check Python SDK installation: `pip list | grep lmstudio`
```

**2. Model Loading Fails**
```python
# Debug model loading
import lmstudio as lms

async def debug_model_loading():
    client = lms.Client()
    
    # Check available models
    downloaded = await client.models.list_downloaded()
    print("Downloaded models:", [m.identifier for m in downloaded])
    
    # Check loaded models
    loaded = await client.models.list_loaded()
    print("Loaded models:", [m.identifier for m in loaded])
    
    # Try loading with error handling
    try:
        model = await client.models.load("your-model-name")
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"✗ Loading failed: {e}")
        # Check specific error types and solutions
```

**3. Memory Issues**
```python
# Memory optimization strategies
async def handle_memory_issues():
    client = lms.Client()
    
    # Unload all models to free memory
    loaded = await client.models.list_loaded()
    for model in loaded:
        await model.unload()
        print(f"Unloaded {model.identifier}")
    
    # Load model with smaller configuration
    model = await client.models.load(
        "your-model",
        config={
            'gpu_layers': 20,  # Reduce GPU layers
            'context_length': 16384,  # Smaller context
            'batch_size': 256  # Smaller batch
        }
    )
```

**4. LiteLLM Integration Issues**
```python
# Test LiteLLM + LM Studio integration
import litellm
import requests

def test_integration():
    # Check if LM Studio API is accessible
    try:
        response = requests.get("http://localhost:1234/v1/models")
        print(f"API Status: {response.status_code}")
        print(f"Available models: {response.json()}")
    except Exception as e:
        print(f"API Error: {e}")
    
    # Test LiteLLM routing
    try:
        result = litellm.completion(
            model="lm_studio/your-model",
            messages=[{"role": "user", "content": "test"}],
            api_base="http://localhost:1234/v1"
        )
        print(f"✓ LiteLLM integration working")
    except Exception as e:
        print(f"✗ LiteLLM error: {e}")
```

## 3-Phase Quick Start Checklist

### Phase 1: Prerequisites ✅
- **✓ Complete First**: AI agents using `litellm.completion()` calls
- **✓ Working Setup**: OpenAI models through LiteLLM

### Phase 2: Enhanced Local Models with Python SDK 🎯
1. **📋 Install Components**: 
   - LM Studio (includes lms CLI backend)
   - LM Studio Python SDK via `pip install lmstudio`
2. **🚀 Start Backend Service**: `lms server start`
3. **📦 Download Models via SDK**: 
   - General: `await client.models.download("qwen2.5-72b-instruct")`
   - Reasoning: `await client.models.download("deepseek-r1-distill-qwen-32b")`
4. **🔧 Implement Enhanced Integration**: LiteLLM + LM Studio SDK bridge
5. **🧪 Test Programmatic Control**: Verify auto-loading and model switching
6. **📊 Monitor Performance**: SDK-based health checking and optimization

### Phase 3: Autonomous Multi-Agent Deep Research 🚀
7. **🤖 Implement Agentic Flows**: Use LM Studio SDK's `.act()` API
8. **🏗️ Build Deep Research Supervisor**: Multi-agent coordination with SDK
9. **🌐 Configure Enhanced Search**: Integrate web search with autonomous agents
10. **🔄 Replace o3/o4 Deep Research**: Local reasoning models + autonomous behavior
11. **🧠 Test Autonomous Capabilities**: Verify multi-step tool usage
12. **🚀 Deploy Production System**: Complete local deep research pipeline

## Expected Results by Phase

### Phase 2 Results: Enhanced Local Models with Python SDK
- **Programmatic Control**: Complete model management via Python code
- **Auto-Loading**: Models loaded automatically when needed
- **Smart Resource Management**: Memory optimization and model switching
- **Unified Interface**: LiteLLM + LM Studio SDK seamless integration
- **No GUI Dependency**: CLI backend + Python SDK only

### Phase 3 Results: Autonomous Deep Research System
- **Autonomous Agents**: Multi-step research using `.act()` API
- **Tool Integration**: Agents can use web search, analysis, and data tools
- **Multi-Agent Coordination**: Supervisor orchestrates research tasks
- **Cost Elimination**: No more OpenAI o3/o4 deep research costs
- **Enhanced Capabilities**: Local reasoning with autonomous behavior

### Advanced Features Available
- **Agentic Flows**: `.act()` API for autonomous multi-step execution
- **Model Management**: Programmatic loading, unloading, and configuration
- **Resource Optimization**: Smart memory management and model switching
- **Easy Scaling**: Add multiple models or advanced orchestration
- **Complete Privacy**: All processing stays local

## Migration Success

Your AI agents experience a seamless transformation:
1. **Phase 1**: OpenAI → LiteLLM (same models, zero changes)
2. **Phase 2**: LiteLLM → LM Studio SDK (programmatic local models)  
3. **Phase 3**: Local Models → Autonomous Agents (enhanced capabilities)

**The power of the enhanced architecture**: Your business logic never changed, but you now have autonomous local agents with programmatic control!

## Support & Resources

- **LM Studio Python SDK Docs**: https://lmstudio.ai/docs/python
- **LM Studio CLI Docs**: https://lmstudio.ai/docs/cli  
- **LiteLLM + LM Studio**: https://docs.litellm.ai/docs/providers/lm_studio
- **GitHub**: https://github.com/lmstudio-ai/lmstudio-python
- **Model Hub**: https://huggingface.co/models
- **Community**: LM Studio Discord for troubleshooting

## Migration Philosophy

**Programmatic First**: 
- Phase 2: Python SDK for complete programmatic control
- Phase 3: Autonomous agents with `.act()` API
- Your code gains advanced capabilities automatically!

**Enhanced Benefits**:
- Phase 2: Eliminate API costs + gain programmatic control
- Phase 3: Eliminate expensive deep research + gain autonomous capabilities
- Complete local processing with enhanced agent behaviors