# AI Agent Implementation Guide: LiteLLM + Open Deep Research Migration

## Mission Overview

**Goal**: Migrate from native OpenAI calls to LiteLLM with minimal code changes, while integrating open-deep-research as an alternative research capability.

**Success Criteria**: 
- Swap models/endpoints without touching business logic
- Maintain existing interfaces and behaviors
- Add enhanced research capabilities as optional features

## Phase 1: Drop-in LiteLLM Replacement

### 1. Client Wrapper Replacement

**Current Pattern**:
```python
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(model="gpt-4.1", messages=messages)
```

**Target Pattern**:
```python
from litellm import completion
response = completion(model="openai/gpt-4.1", messages=messages)
```

**Your Task**: Create `llm_client.py`

**Input Requirements**:
- Existing OpenAI client usage patterns
- Environment variables for API keys
- Current model names used in system

**Output Requirements**:
- Drop-in replacement class that works with existing code
- Zero changes to agent business logic
- Automatic fallback capabilities
- Usage tracking compatibility

**Key Interface**:
```python
class UnifiedLLMClient:
    def chat_completion(self, model: str, messages: List[Dict], **kwargs) -> Dict
    def reasoning_completion(self, model: str, messages: List[Dict], **kwargs) -> Dict  # For o-series
    def get_usage_stats(self) -> Dict
```

**Critical Requirements**:
- Preserve exact response format structure
- Handle both sync and async calls
- Maintain error handling patterns
- Keep existing timeout behaviors

---

### 2. Configuration Management

**Your Task**: Update `config/config.py`

**Input**: Current model configuration structure

**Output**: Enhanced config supporting multiple providers

**Required Updates**:
```python
# Add to existing config
LITELLM_CONFIG = {
    'enabled': True,
    'default_provider': 'openai',
    'model_mapping': {
        'gpt-4.1': 'openai/gpt-4.1',
        'o4-mini-deep-research-2025-06-26': 'openai/o1-preview',  # Map to available model
        'gpt-4.1-mini': 'openai/gpt-4o-mini'
    },
    'fallback_enabled': True,
    'local_models': {
        'reasoning': 'openai/qwen2.5-72b-instruct',  # LM Studio endpoint
        'general': 'openai/llama-3.3-70b-instruct'   # LM Studio endpoint
    }
}
```

**Why This Matters**: Model switching without code changes throughout the system.

---

### 3. Agent Integration Updates

**Your Task**: Minimal updates to each agent class

**Target Agents**:
- `ResearchAgent`
- `DeepResearchAgent`
- `QuestionAgent` (all 6 instances)
- `SummaryAgent`

**Required Changes Per Agent**:

**Before**:
```python
class ResearchAgent:
    def __init__(self, client):
        self.client = client  # OpenAI client
    
    def research(self, project_name):
        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=messages
        )
```

**After**:
```python
class ResearchAgent:
    def __init__(self, client):
        self.client = client  # UnifiedLLMClient
    
    def research(self, project_name):
        response = self.client.chat_completion(
            model="gpt-4.1",  # Will be mapped automatically
            messages=messages
        )
```

**Key Point**: Only change the method call, not the model names or business logic.

---

### 4. Usage Tracking Integration

**Your Task**: Update `database/usage_tracker.py`

**Input**: Current OpenAI usage tracking logic

**Output**: Enhanced tracker supporting LiteLLM

**Required Interface**:
```python
class EnhancedUsageTracker:
    def track_completion(self, model: str, response: Dict, operation_type: str) -> None
    def get_cost_breakdown(self) -> Dict
    def get_provider_stats(self) -> Dict  # New: per-provider usage
```

**Why**: LiteLLM automatically tracks costs for 17k+ models, leverage this instead of custom calculation.

---

## Phase 2: Open Deep Research Integration

### 5. Alternative Research Agent

**Your Task**: Create `agents/open_deep_research_agent.py`

**Input Requirements**:
- Current `DeepResearchAgent` interface
- Project research data structure
- Expected output format

**Output Requirements**:
- Drop-in alternative to existing deep research
- Same interface, enhanced capabilities
- Optional usage (feature flag controlled)

**Required Interface**:
```python
class OpenDeepResearchAgent:
    def __init__(self, config: Dict):
        # Initialize open_deep_research components
        
    async def conduct_deep_research(self, project_name: str, general_research: str) -> Dict:
        """
        Same interface as existing DeepResearchAgent.conduct_deep_research()
        
        Returns:
        {
            "project_name": str,
            "analysis": str,
            "metadata": {
                "model_used": str,
                "elapsed_time": float,
                "cost": float,
                "sources": List[str]  # Enhanced: actual source tracking
            }
        }
        """
```

**Integration Point**:
```python
# In main orchestrator
if DEEP_RESEARCH_CONFIG.get('use_open_deep_research', False):
    deep_agent = OpenDeepResearchAgent(config)
else:
    deep_agent = DeepResearchAgent(client)  # Existing
```

---

### 6. Enhanced Research Orchestrator

**Your Task**: Update `analyze_projects_multi_agent_v2.py`

**Input**: Current orchestration logic

**Output**: Support for both research systems

**Required Changes**:
1. **Model Client Swap**:
```python
# Replace this:
client = OpenAI()

# With this:
from llm_client import UnifiedLLMClient
client = UnifiedLLMClient()
```

2. **Research Agent Selection**:
```python
def create_research_agents(config):
    if config.get('use_open_deep_research', False):
        return {
            'research': ResearchAgent(client),
            'deep_research': OpenDeepResearchAgent(config),
            'questions': [QuestionAgent(client) for _ in range(6)],
            'summary': SummaryAgent(client)
        }
    else:
        # Existing agent creation
```

3. **Results Harmonization**:
```python
def normalize_research_results(results: Dict, agent_type: str) -> Dict:
    """Ensure consistent output format regardless of research agent used"""
    # Handle differences between traditional and open-deep-research outputs
```

---

## Phase 3: Configuration & Feature Flags

### 7. Feature Flag System

**Your Task**: Create `config/feature_flags.py`

**Purpose**: Control migration rollout and A/B testing

**Required Structure**:
```python
FEATURE_FLAGS = {
    'use_litellm': True,                    # Phase 1
    'use_local_models': False,              # Phase 2 (LM Studio)
    'use_open_deep_research': False,        # Phase 2
    'enable_parallel_research': False,      # Phase 3 (run both systems)
    'auto_model_selection': False,          # Phase 3 (smart routing)
}

def is_enabled(flag_name: str) -> bool:
    return FEATURE_FLAGS.get(flag_name, False)

def get_model_for_task(task_type: str) -> str:
    """Smart model selection based on task and availability"""
    if is_enabled('use_local_models'):
        return LOCAL_MODEL_MAPPING.get(task_type, DEFAULT_MODEL)
    return CLOUD_MODEL_MAPPING.get(task_type, DEFAULT_MODEL)
```

---

### 8. Environment Configuration

**Your Task**: Update `.env` handling

**Required Variables**:
```bash
# Existing
OPENAI_API_KEY=your_key

# New LiteLLM support
LITELLM_LOG_LEVEL=INFO
LITELLM_DROP_PARAMS=True

# LM Studio endpoints (when ready)
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_API_KEY=local-key

# Open Deep Research
TAVILY_API_KEY=your_tavily_key  # For web search
LANGSMITH_API_KEY=your_key      # For tracing (optional)

# Feature flags
USE_LITELLM=true
USE_OPEN_DEEP_RESEARCH=false
USE_LOCAL_MODELS=false
```

---

## Implementation Priority & Dependencies

### Week 1: Core Migration
1. **`llm_client.py`** - Unified client wrapper
2. **`config/config.py`** - Enhanced configuration
3. **Agent updates** - Method call changes only
4. **Testing** - Verify existing functionality works

### Week 2: Enhanced Features
1. **`usage_tracker.py`** - LiteLLM integration
2. **`open_deep_research_agent.py`** - Alternative research
3. **Feature flags** - Controlled rollout system
4. **Integration testing** - Both systems working

### Week 3: Production Ready
1. **Error handling** - Robust fallback systems
2. **Performance optimization** - Async improvements
3. **Monitoring** - Enhanced observability
4. **Documentation** - Usage guides

---

## Testing Requirements

### Unit Tests Required
- `test_unified_llm_client.py` - Client wrapper functionality
- `test_model_mapping.py` - Configuration mapping logic
- `test_usage_tracking.py` - Cost and usage calculations

### Integration Tests Required
- `test_agent_compatibility.py` - Existing agents work unchanged
- `test_research_parity.py` - Output format consistency
- `test_fallback_systems.py` - Error handling and recovery

### Performance Tests Required
- `test_response_times.py` - Latency comparison
- `test_concurrent_requests.py` - Multi-agent performance
- `test_cost_optimization.py` - Usage and cost tracking

---

## Success Metrics

**Phase 1 Complete When**:
- All agents work with LiteLLM client
- Zero business logic changes required
- Existing test suite passes unchanged
- Can switch between OpenAI and other providers via config

**Phase 2 Complete When**:
- Open deep research available as alternative
- Feature flags control all new capabilities
- A/B testing possible between research systems
- Enhanced source tracking and citations working

**Phase 3 Complete When**:
- Local models integrated via LM Studio
- Smart model routing based on task type
- Cost reduced by 70%+ through local inference
- Performance improved 2x+ through local models

---

## Critical Implementation Notes

1. **Preserve Interfaces**: Existing code should work without changes
2. **Gradual Migration**: Feature flags enable safe rollout
3. **Fallback Systems**: Always have OpenAI as backup during transition
4. **Monitoring**: Track performance and quality metrics throughout
5. **Testing**: Comprehensive testing at each phase

**Remember**: You're building bridges, not burning them. The existing system should continue working while new capabilities are added incrementally.