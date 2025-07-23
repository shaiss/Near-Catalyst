# LM Studio Setup Guide: 3-Phase Local Model Migration

## Overview

This guide covers **Phase 2** and **Phase 3** of your migration to local models with deep research capabilities.

**Migration Flow**:
- **Phase 1**: ✅ OpenAI → LiteLLM (completed first)
- **Phase 2**: 🎯 LiteLLM → Local Models (this guide)
- **Phase 3**: 🚀 Multi-Agent Deep Research (advanced setup)

**Prerequisites**: Your AI agents should already be using `litellm.completion()` calls from Phase 1.

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

## LM Studio Installation

### Step 1: Download and Install
```bash
# Download LM Studio
wget https://lmstudio.ai/download/linux
chmod +x lmstudio-*.AppImage

# Or on macOS
brew install --cask lm-studio

# Launch LM Studio
./lmstudio-*.AppImage
```

### Step 2: GPU Configuration
1. Open LM Studio
2. Go to Settings → GPU Acceleration
3. Enable CUDA (for NVIDIA) or Metal (for Apple Silicon)
4. Set GPU memory allocation to 90-95%
5. Verify GPU detection shows your hardware

## Model Downloads by Phase

### Phase 2: Your Current Model Replacements

**For your specific codebase** (based on analysis of current usage):

```
1. Qwen/Qwen2.5-72B-Instruct-GGUF → Replaces gpt-4.1
   - File: qwen2.5-72b-instruct-q4_k_m.gguf
   - Size: ~42GB
   - Purpose: ResearchAgent, SummaryAgent, QuestionAgent fallback
   - VRAM: ~24GB
   - Current usage: agents/research_agent.py, agents/summary_agent.py
   - Port: 1234

2. Qwen/QwQ-32B-Preview-GGUF → Replaces o4-mini (reasoning)
   - File: qwq-32b-preview-q4_k_m.gguf  
   - Size: ~19GB
   - Purpose: QuestionAgent development/fallback reasoning
   - VRAM: ~12GB
   - Current usage: config/config.py QUESTION_AGENT_CONFIG
   - Port: 1235
```

### Phase 3: Advanced Reasoning for Production

```
3. deepseek-ai/DeepSeek-R1-Distill-Qwen-32B-GGUF → Replaces o3 (production reasoning)
   - File: deepseek-r1-distill-qwen-32b-q4_k_m.gguf
   - Size: ~19GB
   - Purpose: QuestionAgent production reasoning analysis
   - VRAM: ~12GB
   - Current usage: config/config.py production reasoning model
   - Supports: reasoning_content and thinking_blocks
   - Port: 1235 (can alternate with QwQ-32B)

4. Multi-Agent Deep Research System → Replaces o4-mini-deep-research
   - Purpose: Replace expensive $200/1M token deep research
   - Current usage: config/config.py DEEP_RESEARCH_CONFIG
   - Implementation: Phase 3 supervisor + research agents
   - Models: Combination of general + reasoning models above
```

### Phase 3: Specialized & Support Models
```
5. deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct-GGUF
   - File: deepseek-coder-v2-lite-instruct-q4_k_m.gguf
   - Size: ~9GB
   - Purpose: Code analysis and generation
   - VRAM: ~6GB

6. BAAI/bge-m3-GGUF
   - File: bge-m3-q4_k_m.gguf
   - Size: ~2GB
   - Purpose: Embeddings (handled separately)
   - VRAM: ~1GB
```

### Phase 2 Priority Download Order

**Start with these models based on your current usage**:

1. **FIRST: Qwen2.5-72B-Instruct** (replaces gpt-4.1)
   - Most used model in your codebase
   - Used by: ResearchAgent, SummaryAgent, QuestionAgent fallback
   - Cost savings: $10/1M tokens → FREE

2. **SECOND: QwQ-32B-Preview** (replaces o4-mini reasoning)  
   - QuestionAgent development/testing reasoning
   - Cost savings: $15/1M tokens → FREE

3. **THIRD: DeepSeek-R1-Distill** (replaces o3 reasoning)
   - QuestionAgent production reasoning  
   - Cost savings: $60/1M tokens → FREE

### Download Instructions
1. Open LM Studio
2. Go to "Browse" tab
3. Search for each model name **in priority order above**
4. Click download for the Q4_K_M quantized version
5. Models will download to `~/.cache/lm-studio/models/`

### Expected Cost Savings
**Your current monthly OpenAI spend reduction**:
- gpt-4.1 usage → 100% savings (most frequent)
- o4-mini reasoning → 100% savings  
- o3 reasoning → 100% savings
- **Total Phase 2 savings**: Majority of your API costs

## Phase 2: Basic API Server Configuration

### Step 1: Single Model Setup (Phase 2)
1. In LM Studio, go to "Local Server" tab
2. Load your primary model (start with Qwen2.5-72B-Instruct)
3. Click "Start Server"
4. Default endpoint: `http://localhost:1234`

### Step 2: OpenAI Compatibility
LM Studio automatically provides OpenAI-compatible endpoints:
- **Chat Completions**: `POST /v1/chat/completions`
- **Models List**: `GET /v1/models`
- **Health Check**: `GET /v1/models`

## Phase 3: Multi-Model Setup for Deep Research

For deep research capabilities, you'll need multiple specialized models running simultaneously:

**Option A: Multiple Ports**
```bash
# Terminal 1: General purpose model
lms server start qwen2.5-72b-instruct-q4_k_m.gguf --port 1234

# Terminal 2: Reasoning model  
lms server start qwq-32b-preview-q4_k_m.gguf --port 1235

# Terminal 3: Fast model
lms server start qwen2.5-32b-instruct-q4_k_m.gguf --port 1236
```

**Option B: Dynamic Model Loading (Phase 2 Approach)**
- Use single port (1234) for Phase 2
- Switch models as needed through LM Studio UI
- Upgrade to Option A when implementing Phase 3 deep research

## Phase 2: Simple LiteLLM Configuration

### Option 1: Direct API Base (Phase 2 - Simplest)
No config file needed! Just set environment variables:

```bash
# In your .env file
OPENAI_API_BASE=http://localhost:1234/v1
OPENAI_API_KEY=local-key  # LM Studio doesn't validate this
```

Your existing code works unchanged:
```python
import litellm
response = litellm.completion(
    model="gpt-4.1",  # Will route to your local model
    messages=messages
)
```

### Option 2: LiteLLM Config File (Phase 3 Preparation)
Create `litellm_config.yaml` for model mapping:

```yaml
model_list:
  - model_name: gpt-4.1
    litellm_params:
      model: openai/qwen2.5-72b-instruct
      api_base: http://localhost:1234/v1
      api_key: "local-key"
      
  - model_name: gpt-4.1-mini  
    litellm_params:
      model: openai/llama-3.3-70b-instruct
      api_base: http://localhost:1234/v1
      api_key: "local-key"

# Optional: Fallbacks to OpenAI if local fails
router_settings:
  fallbacks:
    - "gpt-4.1": ["openai/gpt-4"]
    - "gpt-4.1-mini": ["openai/gpt-4o-mini"]
```

Start LiteLLM with config:
```bash
litellm --config litellm_config.yaml --port 8000
```

Then point your app to LiteLLM proxy:
```bash
export OPENAI_API_BASE=http://localhost:8000
```

## Testing by Phase

### Phase 2: Verify Basic Local Model Setup
```bash
# Test model availability
curl http://localhost:1234/v1/models

# Test chat completion
curl -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-72b-instruct",
    "messages": [{"role": "user", "content": "Hello, test message"}],
    "max_tokens": 100
  }'
```

### Phase 2: Test LiteLLM Integration
```python
# test_local_models.py
import litellm
import os

# Option 1: Direct API base
os.environ["OPENAI_API_BASE"] = "http://localhost:1234/v1"
response = litellm.completion(
    model="gpt-4.1",  # Your existing model name
    messages=[{"role": "user", "content": "Test local model"}]
)

print(f"Response: {response.choices[0].message.content}")
print(f"Model: {response.model}")
```

### Phase 2: Verify Your Agents Work
Run your existing agent test:
```python
from agents.research_agent import ResearchAgent

agent = ResearchAgent()
result = agent.research("test project")
print("✓ Agent working with local models!")
```

### Phase 3: Test Reasoning Content & Deep Research
Test reasoning models with thinking content:
```python
import litellm
import os

os.environ["OPENAI_API_BASE"] = "http://localhost:1234/v1"

# Test reasoning model with thinking content
response = litellm.completion(
    model="o4-mini",  # Will route to local QwQ-32B
    messages=[{"role": "user", "content": "Solve this complex reasoning task step by step"}],
    reasoning_effort="medium"
)

# Access reasoning content
print("Response:", response.choices[0].message.content)
print("Reasoning:", response.choices[0].message.reasoning_content)
if hasattr(response.choices[0].message, 'thinking_blocks'):
    print("Thinking blocks:", response.choices[0].message.thinking_blocks)
```

### Phase 3: Test Multi-Agent Deep Research

```python
# test_deep_research.py
from agents.deep_research_supervisor import DeepResearchSupervisor
import asyncio

async def test_deep_research():
    supervisor = DeepResearchSupervisor()
    
    # Test multi-agent deep research
    result = await supervisor.conduct_deep_research(
        "Analyze the impact of AI on healthcare innovation"
    )
    
    print("Deep Research Results:")
    print(f"Report: {result['report'][:200]}...")
    print(f"Sources: {len(result['sources'])} research agents used")
    print(f"Methodology: {result['methodology']}")
    
if __name__ == "__main__":
    asyncio.run(test_deep_research())
```

Your agents don't know they're using local models - the API calls are identical, but now with enhanced reasoning and multi-agent coordination!

## Performance Optimization

### Model Loading Optimization
```yaml
# LM Studio settings for optimal performance
gpu_layers: -1          # Use all GPU layers
context_length: 32768   # Maximum context
batch_size: 512         # Batch size for parallel requests
threads: 8              # CPU threads for non-GPU ops
```

### Memory Management
- **Single Model**: Load one model at a time, switch as needed
- **Multi-Model**: Use multiple ports if you have sufficient VRAM
- **Memory Mapping**: Enable memory mapping for faster model loading

### Request Optimization
```yaml
# Optimize for your use case
temperature: 0.1        # Deterministic outputs
top_p: 0.9             # Nucleus sampling
max_tokens: 2048       # Reasonable limit
stream: false          # Disable if not needed
```

## Monitoring and Health Checks

### LM Studio Monitoring
1. **GPU Usage**: Monitor VRAM usage in LM Studio
2. **Request Queue**: Watch for request backlog
3. **Response Times**: Track inference speed
4. **Error Rates**: Monitor failed requests

### Health Check Endpoint
```python
# health_check.py
import requests
import time

def check_lm_studio_health():
    try:
        response = requests.get("http://localhost:1234/v1/models", timeout=5)
        if response.status_code == 200:
            return {"status": "healthy", "models": response.json()}
        return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# Run every 30 seconds
while True:
    health = check_lm_studio_health()
    print(f"LM Studio Health: {health}")
    time.sleep(30)
```

## Troubleshooting

### Common Issues

**1. Model Loading Fails**
```
Error: Out of memory
Solution: Reduce batch size or use smaller quantization (Q4_K_S instead of Q4_K_M)
```

**2. Slow Response Times**
```
Issue: High latency
Solutions:
- Increase GPU memory allocation
- Reduce context length
- Use smaller model for non-critical tasks
```

**3. Connection Refused**
```
Error: Connection to localhost:1234 refused
Solutions:
- Verify LM Studio server is running
- Check port isn't blocked by firewall
- Confirm model is loaded in LM Studio
```

**4. LiteLLM Mapping Issues**
```
Error: Model not found
Solutions:
- Verify model name in litellm_config.yaml
- Check api_base URL is correct
- Confirm LM Studio model matches config
```

### Debug Commands
```bash
# Check GPU usage
nvidia-smi

# Monitor LM Studio logs
tail -f ~/.lm-studio/logs/server.log

# Test API endpoints
curl -v http://localhost:1234/v1/models

# Check process
ps aux | grep lm-studio
```

## Production Deployment

### Systemd Service (Linux)
```ini
# /etc/systemd/system/lm-studio.service
[Unit]
Description=LM Studio Model Server
After=network.target

[Service]
Type=simple
User=your-username
ExecStart=/path/to/lm-studio server start qwen2.5-72b-instruct-q4_k_m.gguf --port 1234
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable lm-studio
sudo systemctl start lm-studio
sudo systemctl status lm-studio
```

### Docker Deployment (Advanced)
```dockerfile
# Dockerfile for LM Studio
FROM nvidia/cuda:12.1-runtime-ubuntu22.04

# Install LM Studio and dependencies
RUN apt-get update && apt-get install -y wget
RUN wget https://lmstudio.ai/download/linux -O lmstudio.AppImage
RUN chmod +x lmstudio.AppImage

# Copy models and config
COPY models/ /app/models/
COPY config/ /app/config/

# Expose API port
EXPOSE 1234

# Start LM Studio server
CMD ["./lmstudio.AppImage", "server", "start", "--port", "1234"]
```

## 3-Phase Quick Start Checklist

### Phase 1: Prerequisites ✅
- **✓ Complete First**: AI agents using `litellm.completion()` calls
- **✓ Working Setup**: OpenAI models through LiteLLM

### Phase 2: Local Models 🎯
1. **📋 Install LM Studio**: Download and set up on your machine
2. **📦 Download Basic Models**: 
   - General: Qwen2.5-72B-Instruct (42GB)
   - Alternative: Llama-3.3-70B-Instruct (40GB)
3. **🚀 Start Single Server**: Load model and start local server on port 1234
4. **⚙️ Set Environment**: `export OPENAI_API_BASE=http://localhost:1234/v1`
5. **🧪 Test Basic Local**: Run your existing agents - they'll use local models automatically
6. **📊 Monitor Usage**: LiteLLM automatically tracks costs and usage

### Phase 3: Multi-Agent Deep Research 🚀
7. **📦 Download Reasoning Models**: 
   - QwQ-32B-Preview (19GB) for thinking content
   - DeepSeek-R1-Distill-Qwen-32B (19GB) alternative
8. **🏗️ Multi-Model Setup**: Run general + reasoning models simultaneously (ports 1234 + 1235)
9. **🔧 Implement Deep Research**: Build supervisor + research agent pattern
10. **🌐 Configure Search Engines**: Set up Tavily, SearXNG, academic search
11. **🔄 Replace o3/o4 Deep Research**: Use local reasoning models instead of OpenAI
12. **🧠 Test Reasoning Content**: Verify access to thinking/reasoning traces
13. **🧪 Test Multi-Agent**: Verify deep research coordination works locally

## Expected Results by Phase

### Phase 2 Results: Local Models
- **Same Code**: Your agents use `litellm.completion()` unchanged
- **Local Models**: Inference happens on your hardware  
- **Same Interface**: OpenAI-compatible responses
- **No API Costs**: No charges for local inference
- **Built-in Cost Tracking**: LiteLLM automatically tracks usage and costs

### Phase 3 Results: Deep Research System
- **Enhanced Reasoning**: Access to `reasoning_content` and `thinking_blocks`
- **Multi-Agent Coordination**: Supervisor orchestrates multiple research agents
- **Comprehensive Search**: Multiple search engines for complete coverage
- **Cost Elimination**: No more OpenAI o3/o4 deep research costs
- **Privacy**: Complete local processing for sensitive research

### Advanced Features Available
- **Reasoning Models**: QwQ-32B and DeepSeek-R1 with thinking content
- **Web Search**: Built-in web search capabilities via LiteLLM
- **Native Usage Tracking**: Automatic cost and usage monitoring
- **Easy Scaling**: Add multiple models or fallbacks via config

### Phase 3: Deep Research Multi-Model Setup

**Running Multiple Models Simultaneously for Deep Research**:

1. **General Model** (Port 1234): Qwen2.5-72B for general tasks
2. **Reasoning Model** (Port 1235): QwQ-32B for deep research with thinking content

```bash
# Terminal 1: Start general model
cd /path/to/lmstudio
./bin/lms load qwen2.5-72b-instruct --port 1234

# Terminal 2: Start reasoning model  
./bin/lms load qwq-32b-preview --port 1235
```

**Configuration for Multi-Agent Deep Research**:
```python
# Configure different endpoints for different tasks
GENERAL_MODEL_BASE = "http://localhost:1234/v1"
REASONING_MODEL_BASE = "http://localhost:1235/v1"

# Deep research supervisor can route to appropriate models
general_response = litellm.completion(
    model="qwen2.5-72b-instruct",
    api_base=GENERAL_MODEL_BASE,
    messages=[{"role": "user", "content": "Generate research plan"}]
)

reasoning_response = litellm.completion(
    model="qwq-32b-preview", 
    api_base=REASONING_MODEL_BASE,
    messages=[{"role": "user", "content": "Analyze complex data"}],
    reasoning_effort="high"  # Access thinking content
)
```

**Benefits of Multi-Model Setup**:
- **Specialization**: Each model optimized for specific tasks
- **Performance**: Parallel processing of general and reasoning tasks
- **Cost-effective**: No OpenAI o3/o4 API costs
- **Local**: Complete privacy and control over deep research process

## Migration Success

Your AI agents won't know they've gone through this complete transformation:
1. **Phase 1**: OpenAI → LiteLLM (same models, zero changes)
2. **Phase 2**: LiteLLM → Local Models (same interface, local processing)  
3. **Phase 3**: Local Models → Multi-Agent Deep Research (enhanced capabilities)

**The power of LiteLLM's unified interface**: Your business logic and prompts never changed, but you now have a complete local deep research system!

## Support & Resources

- **LM Studio Docs**: https://lmstudio.ai/docs
- **LiteLLM Docs**: https://docs.litellm.ai/
- **Model Hub**: https://huggingface.co/models
- **GPU Requirements**: Use HuggingFace model cards for VRAM estimates
- **Community**: LM Studio Discord + LiteLLM GitHub for troubleshooting

## Migration Philosophy

**Start Simple, Scale Smart**: 
- Phase 2: One model, basic local processing
- Phase 3: Multi-model, advanced deep research
- Your code adapts automatically to increased capabilities!

**Cost & Privacy Benefits**:
- Phase 2: Eliminate standard API costs  
- Phase 3: Eliminate expensive o3/o4 deep research costs
- All processing stays local for complete privacy