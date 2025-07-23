# AI Agent Implementation Guide: 3-Phase LiteLLM Migration

## Mission Overview

**Goal**: Migrate from native OpenAI calls to a complete local deep research system through three distinct phases.

**3-Phase Strategy**:
- **Phase 1**: OpenAI → LiteLLM (same models, zero code changes)
- **Phase 2**: LiteLLM → Local Models (via LM Studio, same interface)  
- **Phase 3**: Build Multi-Agent Deep Research (replace o3/o4 with local reasoning)

**Success Criteria**: 
- Minimize code and prompt changes across all phases
- Maintain existing interfaces and behaviors throughout
- Replace expensive OpenAI deep research with local multi-agent system
- Achieve cost savings while improving capabilities

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

### 2. Update o-series Models (LiteLLM DOES Support Them!)

**Your Task**: Replace o-series models with LiteLLM calls - they're fully supported!

**Current Pattern**:
```python
response = client.responses.create(
    model="o4-mini-deep-research-2025-06-26",
    messages=[{"role": "user", "content": prompt}]
)
```

**Target Pattern**:
```python
# o-series models work with litellm.completion()!
import litellm
response = litellm.completion(
    model="o4-mini",  # LiteLLM supports: o4-mini, o3-mini, o3
    messages=[{"role": "user", "content": prompt}]
)
```

**Available o-series Models in LiteLLM**:
- `o4-mini` 
- `o3-mini`
- `o3`

**Key Point**: No special handling needed - LiteLLM supports o-series models directly via `completion()`!

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

### 5. Environment Configuration & Multi-Model Setup

**Your Task**: Update `.env` for multi-model local deployment in Phase 2

**Add to `.env`**:
```bash
# Existing
OPENAI_API_KEY=your_openai_key

# Phase 2: Multi-Model LM Studio Configuration
LM_STUDIO_API_BASE=http://localhost:1234/v1      # General models (gpt-4.1)
REASONING_MODEL_BASE=http://localhost:1235/v1    # Reasoning models (o3, o4-mini)
LM_STUDIO_API_KEY=local-key

# Feature flags for Phase 2
USE_LOCAL_MODELS=false  # Set to true to activate Phase 2
USE_REASONING_MODELS=true  # Enable o3/o4-mini reasoning
ENABLE_WEB_SEARCH=false  # Optional web search capability

# Phase 3 preparation
USE_DEEP_RESEARCH_REPLACEMENT=false  # Phase 3: Replace o4-mini-deep-research
TAVILY_API_KEY=your_tavily_key  # For web search in Phase 3

# Model routing (Phase 2)
GENERAL_MODEL_PORT=1234      # For gpt-4.1 → Qwen2.5-72B  
REASONING_MODEL_PORT=1235    # For o3/o4-mini → QwQ-32B/DeepSeek-R1
```

**Add to `config/config.py`**:
```python
# Add after existing configs
LITELLM_CONFIG = {
    'use_local_models': os.getenv('USE_LOCAL_MODELS', 'false').lower() == 'true',
    'lm_studio_base_url': os.getenv('LM_STUDIO_API_BASE', 'http://localhost:1234/v1'),
    'reasoning_model_base_url': os.getenv('REASONING_MODEL_BASE', 'http://localhost:1235/v1'),
    
    # Phase 2: Current OpenAI → Local OSS Model Mapping
    'model_mapping': {
        # Core models found in codebase
        'gpt-4.1': 'openai/qwen2.5-72b-instruct',           # Research, Summary, Question agents
        'o4-mini': 'openai/qwq-32b-preview',                # Question agent reasoning (production fallback)
        'o3': 'openai/deepseek-r1-distill-qwen-32b',        # Question agent reasoning (production)
        
        # Deep research models - Phase 3 replacement targets
        'o4-mini-deep-research-2025-06-26': 'openai/qwq-32b-preview',  # Will become multi-agent system
        
        # Archive models (for completeness)
        'gpt-4.1-nano-2025-04-14': 'openai/llama-3.3-70b-instruct',   # From archive files
        
        # Fallback mappings
        'gpt-4': 'openai/qwen2.5-72b-instruct',            # General fallback
        'gpt-4.1-mini': 'openai/llama-3.3-70b-instruct',   # Smaller tasks
    },
    
    # Cost savings tracking
    'cost_comparison': {
        'gpt-4.1': {'openai': 0.00001, 'local': 0.0},      # $10/1M → Free
        'o4-mini': {'openai': 0.000015, 'local': 0.0},     # $15/1M → Free  
        'o3': {'openai': 0.00006, 'local': 0.0},           # $60/1M → Free
        'o4-mini-deep-research': {'openai': 0.0002, 'local': 0.0}  # $200/1M → Free
    }
}
```

**Purpose**: Ready for Phase 2 local model switching with your current model usage mapped to OSS equivalents.

---

### 6. Current Model Inventory & Phase 2 Mapping

**Your Current OpenAI Models** (found in codebase):

| Agent/Component | Current Model | Usage Location | Phase 2 Local Equivalent |
|---|---|---|---|
| **ResearchAgent** | `gpt-4.1` | `agents/research_agent.py:173` | `qwen2.5-72b-instruct` |
| **SummaryAgent** | `gpt-4.1` | `agents/summary_agent.py:84` | `qwen2.5-72b-instruct` |
| **QuestionAgent (Production)** | `o3` | `config/config.py:106` | `deepseek-r1-distill-qwen-32b` |
| **QuestionAgent (Dev)** | `o4-mini` | `config/config.py:107` | `qwq-32b-preview` |
| **QuestionAgent (Fallback)** | `gpt-4.1` | `config/config.py:115` | `qwen2.5-72b-instruct` |
| **DeepResearchAgent** | `o4-mini-deep-research-2025-06-26` | `config/config.py:91` | **Phase 3**: Multi-agent system |
| **DeepResearchAgent (Priming)** | `gpt-4.1` | `config/config.py:92` | `qwen2.5-72b-instruct` |

**Phase 2 Cost Savings**:
- **gpt-4.1**: $10/1M tokens → **FREE** (100% savings)
- **o3**: $60/1M tokens → **FREE** (100% savings)  
- **o4-mini**: $15/1M tokens → **FREE** (100% savings)
- **o4-mini-deep-research**: $200/1M tokens → **Phase 3** replacement target

**Required LM Studio Models for Phase 2**:
```bash
# Port 1234: General Purpose (gpt-4.1 replacement)
qwen2.5-72b-instruct-q4_k_m.gguf     # 42GB, ~24GB VRAM

# Port 1235: Reasoning Models (o3/o4-mini replacement)  
qwq-32b-preview-q4_k_m.gguf          # 19GB, ~12GB VRAM
deepseek-r1-distill-qwen-32b-q4_k_m.gguf  # 19GB, ~12GB VRAM (alternative)
```

---

### 7. Enhanced Capabilities for Phase 2

**Your Task**: Prepare for advanced features when using local models

#### A. Reasoning Content Support
LiteLLM supports `reasoning_content` and `thinking` for local reasoning models:

```python
# Phase 2: Local reasoning models with thinking content
response = litellm.completion(
    model="openai/qwq-32b-preview",  # Local reasoning model via LM Studio
    messages=[{"role": "user", "content": "Complex reasoning task"}],
    reasoning_effort="low",  # or "medium", "high"
    api_base="http://localhost:1234/v1"
)

# Access reasoning content
reasoning = response.choices[0].message.reasoning_content
thinking_blocks = response.choices[0].message.thinking_blocks
```

#### B. Web Search Integration
LiteLLM supports web search for enhanced research:

```python
# Phase 2: Web search capability
response = litellm.completion(
    model="openai/gpt-4o-search-preview",  
    messages=[{"role": "user", "content": "Research latest AI developments"}],
    web_search_options={
        "search_context_size": "medium"  # "low", "medium", "high"
    }
)
```

#### C. Optional: Open Deep Research Integration
```python
# agents/enhanced_research_agent.py
class EnhancedResearchAgent:
    def __init__(self, config=None):
        self.use_web_search = config.get('enable_web_search', False)
        self.use_reasoning = config.get('use_reasoning_models', True)
    
    async def conduct_research(self, project_name: str) -> Dict:
        # Use LiteLLM's built-in web search + reasoning
        if self.use_web_search:
            response = litellm.completion(
                model="gpt-4.1",
                messages=[{"role": "user", "content": f"Research {project_name}"}],
                web_search_options={"search_context_size": "high"}
            )
        else:
            response = litellm.completion(
                model="o4-mini" if self.use_reasoning else "gpt-4.1",
                messages=[{"role": "user", "content": f"Analyze {project_name}"}],
                reasoning_effort="medium" if self.use_reasoning else None
            )
```

**Key Benefits in Phase 2**:
- Enhanced reasoning via local models with thinking content
- Built-in web search without external dependencies  
- Better cost control with local inference
- Same interfaces as Phase 1

---

## Phase 3: Multi-Agent Deep Research System

### 7. Architecture Overview

**Goal**: Replace OpenAI o3/o4 deep research with local multi-agent system using LiteLLM + local reasoning models.

**Architecture Principles**:
- **No LangChain**: Direct LiteLLM calls only  
- **Borrows proven patterns**: From open-deep-research supervisor architecture
- **Local reasoning**: QwQ-32B/DeepSeek-R1 with thinking content
- **Same interface**: Drop-in replacement for existing DeepResearchAgent
- **Cost effective**: Eliminate OpenAI o3/o4 API costs

#### A. Core Supervisor Pattern (Inspired by open-deep-research)

```python
# agents/deep_research_supervisor.py
import litellm
from typing import List, Dict, Any

class DeepResearchSupervisor:
    def __init__(self, local_model_base_url: str = "http://localhost:1234/v1"):
        self.local_base_url = local_model_base_url
    
    async def conduct_deep_research(self, research_brief: str) -> Dict[str, Any]:
        """
        Supervisor coordinates multiple research agents using LiteLLM
        Architecture borrowed from open-deep-research but LiteLLM-native
        """
        # Step 1: Break down research into sub-topics
        sub_topics = await self._generate_research_plan(research_brief)
        
        # Step 2: Coordinate parallel research (like open-deep-research)
        research_results = await self._coordinate_research_agents(sub_topics)
        
        # Step 3: Synthesize final report
        final_report = await self._synthesize_report(research_brief, research_results)
        
        return {
            "report": final_report,
            "sources": research_results,
            "methodology": "multi-agent-litellm"
        }
```

#### B. Individual Research Agents

```python
# agents/research_agent.py
import litellm
import asyncio

class LiteLLMResearchAgent:
    def __init__(self, agent_id: str, reasoning_model: str = "openai/qwq-32b-preview"):
        self.agent_id = agent_id
        self.reasoning_model = reasoning_model
    
    async def research_subtopic(self, subtopic: str, search_engines: List[str]) -> Dict:
        """
        Individual research agent using local reasoning models
        """
        # Use reasoning model for research planning
        research_plan = await self._plan_research(subtopic)
        
        # Execute searches across multiple engines
        search_results = await self._execute_searches(research_plan, search_engines)
        
        # Use reasoning content for analysis
        analysis = await self._analyze_with_reasoning(search_results, subtopic)
        
        return {
            "subtopic": subtopic,
            "findings": analysis,
            "sources": search_results,
            "reasoning_trace": analysis.get("reasoning_content", "")
        }
    
    async def _analyze_with_reasoning(self, search_results: List, subtopic: str) -> Dict:
        """Use local reasoning model with thinking content"""
        response = litellm.completion(
            model=self.reasoning_model,
            messages=[{
                "role": "user", 
                "content": f"Analyze search results for {subtopic}: {search_results}"
            }],
            reasoning_effort="medium",  # Access thinking process
            api_base="http://localhost:1234/v1"
        )
        
        return {
            "analysis": response.choices[0].message.content,
            "reasoning_content": response.choices[0].message.reasoning_content,
            "thinking_blocks": response.choices[0].message.thinking_blocks
        }
```

#### C. Drop-in Replacement Integration

```python
# Update agents/deep_research_agent.py to use LiteLLM supervisor
from agents.deep_research_supervisor import DeepResearchSupervisor

class DeepResearchAgent:
    def __init__(self):
        self.supervisor = DeepResearchSupervisor()
    
    async def conduct_deep_research(self, project_name: str, general_research: str) -> Dict:
        """
        Replace OpenAI o3/o4 calls with local reasoning model system
        """
        research_brief = f"Deep research on {project_name}: {general_research}"
        
        # Use supervisor to coordinate local reasoning models
        result = await self.supervisor.conduct_deep_research(research_brief)
        
        return {
            "project_name": project_name,
            "analysis": result["report"],
            "sources": result["sources"],
            "methodology": "local-deep-research-litellm"
        }
```

### 8. Search Engine Integration

**Your Task**: Configure multiple search engines for comprehensive research

```python
# agents/search_coordinator.py
import litellm
from typing import List, Dict

class SearchCoordinator:
    def __init__(self):
        self.search_engines = {
            'tavily': self._tavily_search,
            'searxng': self._searxng_search,
            'brave': self._brave_search,
            'academic': self._academic_search  # arXiv, PubMed
        }
    
    async def multi_engine_search(self, query: str, engines: List[str] = None) -> Dict:
        """Search across multiple engines for comprehensive results"""
        engines = engines or ['tavily', 'searxng']
        
        search_tasks = [
            self.search_engines[engine](query) 
            for engine in engines 
            if engine in self.search_engines
        ]
        
        results = await asyncio.gather(*search_tasks)
        return self._merge_search_results(results)
```

### 9. Web Search with LiteLLM

**Your Task**: Leverage LiteLLM's built-in web search capabilities

```python
# Enhanced research with built-in web search
async def enhanced_research(self, query: str) -> Dict:
    """Use LiteLLM's native web search for research"""
    
    # Option 1: Direct web search via LiteLLM
    response = litellm.completion(
        model="gpt-4o-search-preview",  # OpenAI search model
        messages=[{"role": "user", "content": f"Research: {query}"}],
        web_search_options={
            "search_context_size": "high",
            "max_search_results": 10
        }
    )
    
    # Option 2: Local reasoning model + external search
    search_results = await self.search_coordinator.multi_engine_search(query)
    
    reasoning_response = litellm.completion(
        model="openai/qwq-32b-preview",  # Local reasoning model
        messages=[{
            "role": "user", 
            "content": f"Analyze search results for {query}: {search_results}"
        }],
        reasoning_effort="high",
        api_base="http://localhost:1235/v1"  # Local reasoning model port
    )
    
    return {
        "analysis": reasoning_response.choices[0].message.content,
        "reasoning_trace": reasoning_response.choices[0].message.reasoning_content,
        "sources": search_results
    }
```

**Key Benefits of Phase 3**:
- **Cost Elimination**: No more OpenAI o3/o4 deep research costs
- **Enhanced Privacy**: All deep research happens locally
- **Thinking Content**: Access to model reasoning process
- **Multi-Engine Search**: Comprehensive source coverage
- **Same Interface**: Existing agents work unchanged

---

## Testing & Validation

### 10. Create Test Scripts

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

### 11. Requirements Update

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

# Phase 3: Search engines and coordination
tavily-python>=0.3.0
requests>=2.31.0
aiohttp>=3.8.0

# Optional for enhanced research
# open_deep_research>=0.0.16  # For reference patterns only
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

### Phase 3: Deep Research Architecture (Week 6-8)
1. **Week 6**: Design LiteLLM-compatible deep research system
2. **Week 7**: Build supervisor + research agent pattern (no LangChain)
3. **Week 8**: Replace OpenAI o3/o4 deep research with local reasoning models

**Note**: 
- Phase 1: OpenAI models through LiteLLM
- Phase 2: Local models via LM Studio  
- Phase 3: Deep research replacement using open-deep-research patterns

---

## Critical Success Factors

### Phase 1 Complete When
- All agents work with `litellm.completion()` calls
- Same OpenAI models, same parameters, same responses  
- Existing test suite passes unchanged
- Zero business logic changes required
- **o-series models work with LiteLLM** (they're fully supported!)

### Phase 2 Complete When  
- LM Studio running with local models
- Configuration switches between OpenAI/local via env var
- Same agent interfaces work with local models
- **Reasoning content** accessible via `response.choices[0].message.reasoning_content`
- **Web search** integrated for enhanced research capabilities
- **Native cost tracking** via LiteLLM (replaces custom tracking)
- Performance meets or exceeds OpenAI

### Phase 3 Complete When
- **Deep research system** built using LiteLLM (no LangChain abstractions)
- **Supervisor architecture** coordinates multiple research agents via `litellm.completion()`
- **Local reasoning models** (QwQ-32B, DeepSeek-R1) replace OpenAI o3/o4 deep research
- **Multi-agent coordination** using direct LiteLLM calls and simple orchestration
- **Web search integration** with multiple engines (Tavily, SearXNG, etc.)
- **Iterative research loops** with thinking content from local models

### Validation Checklist
- [ ] `litellm.completion()` returns same format as OpenAI
- [ ] All agent files updated (no more `from openai import OpenAI`)
- [ ] **o-series models** use `litellm.completion()` (not separate handling)
- [ ] Main orchestrator doesn't create OpenAI client
- [ ] Test script runs successfully  
- [ ] Environment variables configured for Phase 2
- [ ] Requirements.txt includes LiteLLM
- [ ] **Phase 2**: Reasoning content and web search ready
- [ ] **Phase 2**: Custom usage tracking replaced with LiteLLM native tracking
- [ ] **Phase 3**: Deep research supervisor coordinates research agents
- [ ] **Phase 3**: Local reasoning models replace OpenAI o3/o4 deep research
- [ ] **Phase 3**: Multi-agent system uses only LiteLLM (no LangChain)

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
- Phase 2 allows easy switching to local models with reasoning
- **LiteLLM native cost tracking** replaces custom implementations  
- **Web search and reasoning content** built-in for enhanced capabilities
- Environment variable controls model source
- Same code works with any LiteLLM-supported provider
- Can add fallbacks, load balancing, etc. later

**Key Advantages of LiteLLM Approach**:
1. **o-series models fully supported** - no special handling needed
2. **Built-in cost tracking** - automatic for 17k+ models 
3. **Reasoning content access** - `response.choices[0].message.reasoning_content`
4. **Web search integration** - no external dependencies needed
5. **Local model support** - same interface for OpenAI or local models

**Remember**: This is a simple import swap that unlocks powerful capabilities. LiteLLM makes model switching and advanced features transparent to your code.