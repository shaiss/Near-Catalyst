# LM Studio Setup Guide for LiteLLM Integration

## Overview

This guide will help you set up LM Studio to serve local models with OpenAI-compatible endpoints that work seamlessly with LiteLLM. Your AI agents will use these models through the unified client without knowing they're hitting local endpoints.

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

**Phase 2: Reasoning Models**
```
3. Qwen/QwQ-32B-Preview-GGUF
   - File: qwq-32b-preview-q4_k_m.gguf
   - Size: ~19GB
   - Purpose: Reasoning replacement for o-series
   - VRAM: ~12GB

4. deepseek-ai/DeepSeek-R1-Distill-Qwen-32B-GGUF
   - File: deepseek-r1-distill-qwen-32b-q4_k_m.gguf
   - Size: ~19GB
   - Purpose: Alternative reasoning model
   - VRAM: ~12GB
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

## LiteLLM Configuration for LM Studio

### Your LiteLLM Config File
Create `litellm_config.yaml`:

```yaml
model_list:
  # General Purpose Model
  - model_name: local-general
    litellm_params:
      model: openai/qwen2.5-72b-instruct
      api_base: http://localhost:1234/v1
      api_key: "local-key"  # LM Studio doesn't require real key
    model_info:
      max_tokens: 32768
      supports_function_calling: true
      mode: chat

  # Reasoning Model (when available)
  - model_name: local-reasoning
    litellm_params:
      model: openai/qwq-32b-preview
      api_base: http://localhost:1235/v1
      api_key: "local-key"
    model_info:
      max_tokens: 32768
      supports_reasoning: true
      mode: chat

  # Cloud Fallback (OpenAI)
  - model_name: cloud-general
    litellm_params:
      model: openai/gpt-4
      api_key: ${OPENAI_API_KEY}
    model_info:
      max_tokens: 128000

  # Cloud Reasoning Fallback
  - model_name: cloud-reasoning
    litellm_params:
      model: openai/o1-preview
      api_key: ${OPENAI_API_KEY}

# Router Settings
router_settings:
  routing_strategy: "least-busy"
  model_group_alias:
    general: ["local-general", "cloud-general"]
    reasoning: ["local-reasoning", "cloud-reasoning"]
  
  fallbacks:
    local-general: ["cloud-general"]
    local-reasoning: ["cloud-reasoning"]
    
  health_checks:
    enabled: true
    healthy_threshold: 3
    unhealthy_threshold: 5
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

# Test local model through LiteLLM
response = litellm.completion(
    model="openai/qwen2.5-72b-instruct",
    messages=[{"role": "user", "content": "Test local model"}],
    api_base="http://localhost:1234/v1",
    api_key="local-key"
)

print(f"Response: {response.choices[0].message.content}")
print(f"Model: {response.model}")
```

### Step 3: Verify Model Mapping
Your AI agents will use these model names in code:
- `gpt-4.1` → Maps to `local-general` → Routes to local Qwen2.5-72B
- `o4-mini-deep-research` → Maps to `local-reasoning` → Routes to local QwQ-32B

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

## Next Steps

1. **Start with Single Model**: Get Qwen2.5-72B working first
2. **Test Integration**: Verify your AI agents can connect
3. **Add Reasoning Model**: Set up QwQ-32B for complex tasks
4. **Optimize Performance**: Tune settings for your hardware
5. **Production Deploy**: Set up monitoring and auto-restart

Your LM Studio setup will provide the local model endpoints that LiteLLM routes to, giving your AI agents access to powerful local models while maintaining the same interface they're used to.

## Support

- **LM Studio Docs**: https://lmstudio.ai/docs
- **Model Hub**: https://huggingface.co/models
- **GPU Requirements**: Use HuggingFace model cards for VRAM estimates
- **Community**: LM Studio Discord for troubleshooting

Remember: Start simple with one model, then expand. Your AI agents don't need to know they're talking to local models instead of OpenAI!