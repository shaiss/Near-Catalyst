# AI Agent Implementation Guide: LiteLLM + Open Deep Research Migration

## Mission Overview

**Goal**: Replace direct OpenAI calls with LiteLLM while keeping the same models and business logic unchanged. Then prepare for easy local model switching.

**Success Criteria**: 
- Phase 1: Same OpenAI models through LiteLLM (no model changes)
- Phase 2: Easy switch to local models via configuration
- Zero changes to business logic and prompts
- Maintain existing interfaces and behaviors

## Phase 1: Direct OpenAI Replacement via LiteLLM

### 1. Replace OpenAI Import with LiteLLM

**Current Pattern**:
```python
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(model="gpt-4.1", messages=messages)
```

**Target Pattern (Direct Replacement)**:
```python
import litellm
response = litellm.completion(model="gpt-4.1", messages=messages)
```

**Your Task**: Update import statements across all agent files

**Input Requirements**:
- Find all `from openai import OpenAI` imports
- Find all `client.chat.completions.create()` calls
- Find all `client.responses.create()` calls (o-series models)

**Output Requirements**:
- Replace with `litellm.completion()` calls
- Same model names, same parameters
- Same response format (LiteLLM returns OpenAI-compatible responses)
- Keep existing error handling unchanged

**Key Changes**:
```python
# BEFORE
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4.1",
    messages=messages,
    temperature=0.1
)

# AFTER  
import litellm
response = litellm.completion(
    model="gpt-4.1",  # Same model name
    messages=messages,
    temperature=0.1
)
```

**Critical Requirements**:
- Keep exact same model names initially
- Keep exact same parameters
- Response format is identical (LiteLLM ensures this)
- Keep existing error handling patterns

---

### 2. Handle o-series Models (responses.create)

**Your Task**: Special handling for reasoning models

**Current Pattern**:
```python
response = client.responses.create(
    model="o4-mini-deep-research-2025-06-26",
    messages=[{"role": "user", "content": prompt}]
)
```

**Target Pattern**:
```python
# o-series models still use OpenAI directly (Phase 1)
# LiteLLM doesn't support responses.create() yet
import openai
response = openai.responses.create(
    model="o4-mini-deep-research-2025-06-26",
    messages=[{"role": "user", "content": prompt}]
)
```

**Why**: LiteLLM doesn't yet support OpenAI's responses API for reasoning models. Keep these calls unchanged for now.

---

### 3. Agent File Updates

**Your Task**: Update each agent file to use LiteLLM

**Target Files**:
- `agents/research_agent.py`
- `agents/deep_research_agent.py` 
- `agents/question_agent.py`
- `agents/summary_agent.py`

**Required Changes Per Agent**:

**Before**:
```python
from openai import OpenAI

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
import litellm

class ResearchAgent:
    def __init__(self, client=None):  # client parameter optional now
        pass  # No client needed for LiteLLM
    
    def research(self, project_name):
        response = litellm.completion(
            model="gpt-4.1",  # Same model name
            messages=messages
        )
```

**Key Point**: Same model names, same parameters, just different import and function call.

---

### 4. Main Orchestrator Update

**Your Task**: Update `analyze_projects_multi_agent_v2.py`

**Current Pattern**:
```python
from openai import OpenAI
from database.usage_tracker import APIUsageTracker

# Initialize OpenAI client
client = OpenAI()
usage_tracker = APIUsageTracker(client, db_manager)

# Initialize agents
research_agent = ResearchAgent(client)
deep_research_agent = DeepResearchAgent(client, db_manager, usage_tracker)
```

**Target Pattern**:
```python
import litellm
from database.usage_tracker import APIUsageTracker

# No OpenAI client needed for basic agents
# Keep usage tracker for compatibility
usage_tracker = APIUsageTracker(None, db_manager)  # Pass None for client

# Initialize agents (no client needed)
research_agent = ResearchAgent()
deep_research_agent = DeepResearchAgent(None, db_manager, usage_tracker)
```

**Why**: LiteLLM handles API calls directly, so most agents don't need a client object.

---

## Phase 2: Prepare for Local Models

### 5. Environment Configuration  

**Your Task**: Update `.env` and add configuration variables

**Add to `.env`**:
```bash
# Existing
OPENAI_API_KEY=your_openai_key

# New for LiteLLM (Phase 2 - LM Studio)
LM_STUDIO_API_BASE=http://localhost:1234/v1
LM_STUDIO_API_KEY=local-key

# Feature flags for future
USE_LOCAL_MODELS=false  # Set to true in Phase 2
USE_OPEN_DEEP_RESEARCH=false  # Optional enhancement
```

**Add to `config/config.py`**:
```python
# Add after existing configs
LITELLM_CONFIG = {
    'use_local_models': os.getenv('USE_LOCAL_MODELS', 'false').lower() == 'true',
    'lm_studio_base_url': os.getenv('LM_STUDIO_API_BASE', 'http://localhost:1234/v1'),
    'model_mapping': {
        # Phase 2: Map to local models when USE_LOCAL_MODELS=true
        'gpt-4.1': 'openai/qwen2.5-72b-instruct',
        'gpt-4.1-mini': 'openai/llama-3.3-70b-instruct',
        # o-series models stay on OpenAI for now
    }
}
```

**Purpose**: Ready for Phase 2 local model switching via environment variables.

---

### 6. Optional: Open Deep Research Integration

**Your Task**: (Optional) Create `agents/open_deep_research_agent.py`

**Purpose**: Alternative to current deep research using the open-deep-research package

**Only implement this if**:
- Current deep research isn't meeting needs
- You want enhanced web search capabilities  
- You want structured research workflows

**Basic Structure**:
```python
# agents/open_deep_research_agent.py
try:
    from open_deep_research import research_workflow
    OPEN_DEEP_RESEARCH_AVAILABLE = True
except ImportError:
    OPEN_DEEP_RESEARCH_AVAILABLE = False

class OpenDeepResearchAgent:
    def __init__(self, config=None):
        if not OPEN_DEEP_RESEARCH_AVAILABLE:
            raise ImportError("open_deep_research package not installed")
    
    async def conduct_deep_research(self, project_name: str, general_research: str) -> Dict:
        """Same interface as DeepResearchAgent for drop-in replacement"""
        # Implementation using open_deep_research package
        # Returns same format as existing agent
        pass
```

**Integration**:
```python
# In config/config.py
USE_OPEN_DEEP_RESEARCH = os.getenv('USE_OPEN_DEEP_RESEARCH', 'false').lower() == 'true'

# In main orchestrator - conditional usage
if USE_OPEN_DEEP_RESEARCH:
    deep_agent = OpenDeepResearchAgent()
else:
    deep_agent = DeepResearchAgent()  # Existing
```

---

## Testing & Validation

### 7. Create Test Scripts

**Your Task**: Create `test_litellm_migration.py`

**Purpose**: Validate that LiteLLM changes work correctly

**Basic Test Structure**:
```python
# test_litellm_migration.py
import litellm
from agents.research_agent import ResearchAgent

def test_basic_completion():
    """Test that LiteLLM completion works"""
    response = litellm.completion(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": "Test message"}]
    )
    assert response.choices[0].message.content
    print("✓ Basic completion test passed")

def test_agent_integration():
    """Test that agents work with LiteLLM"""
    agent = ResearchAgent()
    result = agent.research("test project")
    assert result is not None
    print("✓ Agent integration test passed")

if __name__ == "__main__":
    test_basic_completion()
    test_agent_integration()
    print("All tests passed!")
```

**Run tests**:
```bash
python test_litellm_migration.py
```

---

### 8. Requirements Update

**Your Task**: Update `requirements.txt`

**Add to requirements.txt**:
```bash
# Existing
openai>=1.57.0
requests>=2.31.0
python-dotenv>=1.0.0
flask>=3.0.0
flask-cors>=4.0.0

# New for LiteLLM
litellm>=1.74.0

# Optional for enhanced research
# open_deep_research>=0.0.16  # Uncomment if using
```

---

## Implementation Timeline

### Phase 1: LiteLLM Integration (Week 1)
1. **Day 1**: Update requirements.txt and install LiteLLM
2. **Day 2**: Replace OpenAI imports in all agent files
3. **Day 3**: Update main orchestrator file
4. **Day 4**: Test all agents with LiteLLM
5. **Day 5**: Handle any o-series model special cases

### Phase 2: Local Model Preparation (Week 2+)
1. **Week 2**: Set up LM Studio and download models
2. **Week 3**: Add configuration for local model switching
3. **Week 4**: Test local models with same interface
4. **Week 5**: Performance optimization and monitoring

**Note**: Phase 1 keeps using OpenAI models through LiteLLM. Phase 2 switches to local models.

---

## Critical Success Factors

### Phase 1 Complete When
- All agents work with `litellm.completion()` calls
- Same OpenAI models, same parameters, same responses
- Existing test suite passes unchanged
- Zero business logic changes required
- o-series models work with direct OpenAI (temporary)

### Phase 2 Complete When  
- LM Studio running with local models
- Configuration switches between OpenAI/local via env var
- Same agent interfaces work with local models
- Performance meets or exceeds OpenAI
- Cost tracking works with local inference

### Validation Checklist
- [ ] `litellm.completion()` returns same format as OpenAI
- [ ] All agent files updated (no more `from openai import OpenAI`)
- [ ] Main orchestrator doesn't create OpenAI client
- [ ] Test script runs successfully
- [ ] Environment variables configured for Phase 2
- [ ] Requirements.txt includes LiteLLM

---

## Key Implementation Notes

### Direct Replacement Strategy
1. **No wrappers**: Use LiteLLM directly, not through custom clients
2. **Same models**: Keep using OpenAI models initially (gpt-4.1, etc.)
3. **Same parameters**: All existing parameters work unchanged
4. **Same responses**: LiteLLM returns OpenAI-compatible responses

### Error Handling
- Keep existing try/catch blocks unchanged
- LiteLLM raises same exceptions as OpenAI
- Same timeout behaviors
- Same rate limiting responses

### Future-Proofing
- Phase 2 allows easy switching to local models
- Environment variable controls model source
- Same code works with any LiteLLM-supported provider
- Can add fallbacks, load balancing, etc. later

**Remember**: This is a simple import swap, not a major refactor. The point of LiteLLM is to make model switching transparent to your code.