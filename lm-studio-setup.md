# LM Studio Setup Guide for LiteLLM Integration

## Overview

This guide will help you set up LM Studio to serve local models with OpenAI-compatible endpoints that work seamlessly with LiteLLM. This is **Phase 2** of the migration - after you've already replaced OpenAI imports with LiteLLM.

**Prerequisites**: Your AI agents should already be using `litellm.completion()` calls instead of OpenAI client calls.

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

## Model Downloads

### Priority Models for Your System

**Phase 1: Basic Functionality**
```
1. Qwen/Qwen2.5-72B-Instruct-GGUF
   - File: qwen2.5-72b-instruct-q4_k_m.gguf
   - Size: ~42GB
   - Purpose: General purpose replacement for GPT-4.1
   - VRAM: ~24GB

2. microsoft/Llama-3.3-70B-Instruct-GGUF  
   - File: llama-3.3-70b-instruct-q4_k_m.gguf
   - Size: ~40GB
   - Purpose: Alternative general model
   - VRAM: ~22GB
```

**Phase 2: Reasoning Models with Thinking Content**
```
3. Qwen/QwQ-32B-Preview-GGUF
   - File: qwq-32b-preview-q4_k_m.gguf
   - Size: ~19GB
   - Purpose: Local reasoning with thinking/reasoning content
   - VRAM: ~12GB
   - Supports: reasoning_content and thinking_blocks

4. deepseek-ai/DeepSeek-R1-Distill-Qwen-32B-GGUF
   - File: deepseek-r1-distill-qwen-32b-q4_k_m.gguf
   - Size: ~19GB
   - Purpose: Alternative reasoning model with thinking
   - VRAM: ~12GB
   - Supports: reasoning_content and thinking_blocks
```

**Phase 3: Specialized Models**
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

### Download Instructions
1. Open LM Studio
2. Go to "Browse" tab
3. Search for each model name
4. Click download for the Q4_K_M quantized version
5. Models will download to `~/.cache/lm-studio/models/`

## API Server Configuration

### Step 1: Enable Server Mode
1. In LM Studio, go to "Local Server" tab
2. Load your primary model (start with Qwen2.5-72B-Instruct)
3. Click "Start Server"
4. Default endpoint: `http://localhost:1234`

### Step 2: OpenAI Compatibility
LM Studio automatically provides OpenAI-compatible endpoints:
- **Chat Completions**: `POST /v1/chat/completions`
- **Models List**: `GET /v1/models`
- **Health Check**: `GET /v1/models`

### Step 3: Multi-Model Setup
For production, you'll want multiple model instances:

**Option A: Multiple Ports**
```bash
# Terminal 1: General purpose model
lms server start qwen2.5-72b-instruct-q4_k_m.gguf --port 1234

# Terminal 2: Reasoning model  
lms server start qwq-32b-preview-q4_k_m.gguf --port 1235

# Terminal 3: Fast model
lms server start qwen2.5-32b-instruct-q4_k_m.gguf --port 1236
```

**Option B: Model Switching (Simpler)**
- Use single port (1234)
- Switch models as needed through LM Studio UI
- LiteLLM will handle model routing

## Simple LiteLLM Configuration

### Option 1: Direct API Base (Simplest)
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

### Option 2: LiteLLM Config File (Advanced)
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

## Testing Your Setup

### Step 1: Verify LM Studio API
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

### Step 2: Test LiteLLM Integration
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

### Step 3: Verify Your Agents Work
Run your existing agent test:
```python
from agents.research_agent import ResearchAgent

agent = ResearchAgent()
result = agent.research("test project")
print("✓ Agent working with local models!")
```

### Step 4: Test Reasoning Content (Phase 2)
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

Your agents don't know they're using local models - the API calls are identical, but now with enhanced reasoning!

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

## Quick Start Checklist

1. **✓ Phase 1 Complete**: AI agents using `litellm.completion()` 
2. **📋 Install LM Studio**: Download and set up on your machine
3. **📦 Download Models**: 
   - General: Qwen2.5-72B-Instruct (42GB)
   - Reasoning: QwQ-32B-Preview (19GB) for thinking content
4. **🚀 Start Server**: Load model and start local server on port 1234
5. **⚙️ Set Environment**: `export OPENAI_API_BASE=http://localhost:1234/v1`
6. **🧪 Test**: Run your existing agents - they'll use local models automatically
7. **🧠 Test Reasoning**: Verify reasoning content with o-series models  
8. **📊 Monitor Usage**: LiteLLM automatically tracks costs and usage

### Phase 3: Deep Research Setup
9. **🏗️ Multi-Model Setup**: Run both general and reasoning models simultaneously
10. **🔧 Deep Research Architecture**: Implement supervisor + research agent pattern
11. **🌐 Search Integration**: Configure Tavily, SearXNG, or other search engines
12. **🔄 Replace o3/o4 Deep Research**: Use local reasoning models instead of OpenAI
13. **🧪 Test Deep Research**: Verify multi-agent coordination works locally

## Expected Results

- **Same Code**: Your agents use `litellm.completion()` unchanged
- **Local Models**: Inference happens on your hardware  
- **Same Interface**: OpenAI-compatible responses
- **Enhanced Reasoning**: Access to `reasoning_content` and `thinking_blocks`
- **Better Performance**: Potentially faster and always available
- **No API Costs**: No charges for local inference
- **Built-in Cost Tracking**: LiteLLM automatically tracks usage and costs

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

Your AI agents won't know they switched from OpenAI to local models - that's the power of LiteLLM's unified interface!

## Support

- **LM Studio Docs**: https://lmstudio.ai/docs
- **Model Hub**: https://huggingface.co/models
- **GPU Requirements**: Use HuggingFace model cards for VRAM estimates
- **Community**: LM Studio Discord for troubleshooting

Remember: Start simple with one model, then expand. Your AI agents don't need to know they're talking to local models instead of OpenAI!