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

# Phase 2: LM Studio Python SDK Configuration (programmatic model management)
LM_STUDIO_API_BASE=http://localhost:1234/v1      # LM Studio local API server
LM_STUDIO_API_KEY=local-key                      # Optional for local

# Feature flags for Phase 2
USE_LOCAL_MODELS=false  # Set to true to activate Phase 2
USE_LMSTUDIO_SDK=true   # Use Python SDK instead of Desktop GUI
ENABLE_WEB_SEARCH=false  # Optional web search capability

# Phase 3 preparation
USE_DEEP_RESEARCH_REPLACEMENT=false  # Phase 3: Replace o4-mini-deep-research
TAVILY_API_KEY=your_tavily_key  # For web search in Phase 3

# Simplified model deployment (Phase 2) - LM Studio SDK manages model loading/switching
# gpt-4.1 → qwen2.5-72b-instruct
# o3 → deepseek-r1-distill-qwen-32b
```

**Add to `config/config.py`**:
```python
# Add after existing configs
LITELLM_CONFIG = {
    'use_local_models': os.getenv('USE_LOCAL_MODELS', 'false').lower() == 'true',
    'use_lmstudio_sdk': os.getenv('USE_LMSTUDIO_SDK', 'true').lower() == 'true',
    'lm_studio_base_url': os.getenv('LM_STUDIO_API_BASE', 'http://localhost:1234/v1'),
    
    # Phase 2: Simplified OpenAI → Local OSS Model Mapping
    'model_mapping': {
        # Core models (via LM Studio Python SDK + local API)
        'gpt-4.1': 'qwen2.5-72b-instruct',                 # Research, Summary, Question agents
        'o3': 'deepseek-r1-distill-qwen-32b',              # Question agent reasoning (production)
        
        # Consolidate fallbacks to these two models
        'o4-mini': 'deepseek-r1-distill-qwen-32b',         # Use same reasoning model  
        'gpt-4': 'qwen2.5-72b-instruct',                   # General fallback
        'gpt-4.1-mini': 'qwen2.5-72b-instruct',            # General fallback
        'gpt-4.1-nano-2025-04-14': 'qwen2.5-72b-instruct', # Archive fallback
        
        # Deep research models - Phase 3 replacement targets
        'o4-mini-deep-research-2025-06-26': 'deepseek-r1-distill-qwen-32b',  # Phase 3: Multi-agent system
    },
    
    # Cost savings tracking
    'cost_comparison': {
        'gpt-4.1': {'openai': 0.00001, 'local': 0.0},      # $10/1M → Free
        'o3': {'openai': 0.00006, 'local': 0.0},           # $60/1M → Free
        'o4-mini-deep-research': {'openai': 0.0002, 'local': 0.0}  # $200/1M → Free (Phase 3)
    }
}

# LM Studio SDK Configuration
LMSTUDIO_CONFIG = {
    'use_sdk': os.getenv('USE_LMSTUDIO_SDK', 'true').lower() == 'true',
    'auto_load_models': True,  # Automatically load models when needed
    'model_load_timeout': 300,  # 5 minutes for model loading
    'default_generation_config': {
        'temperature': 0.1,
        'max_tokens': 2048,
        'top_p': 0.9
    }
}
```

**Purpose**: Ready for Phase 2 local model switching with programmatic model management via LM Studio Python SDK.

---

### 6. Enhanced Phase 2 Architecture: LiteLLM + LM Studio Python SDK

**Complementary Architecture Overview**:

```python
# Enhanced Phase 2 Integration: LiteLLM + LM Studio Python SDK
import litellm
import lmstudio as lms
from typing import Optional, Dict, Any

class EnhancedLocalModelManager:
    """
    Combines LiteLLM's unified API with LM Studio Python SDK's model management
    
    Architecture:
    - LiteLLM: Handles API abstraction and routing
    - LM Studio SDK: Handles model loading, unloading, and direct management
    - Backend: lms CLI service provides model execution infrastructure
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.lms_client = None
        self.loaded_models = {}
        
        if config.get('use_lmstudio_sdk', False):
            # Initialize LM Studio SDK client
            self.lms_client = lms.Client()
    
    async def ensure_model_loaded(self, model_name: str) -> bool:
        """
        Use LM Studio SDK to programmatically load models as needed
        """
        if not self.lms_client:
            return True  # Fallback to manual model management
            
        # Map OpenAI model to local model
        local_model = self.config['model_mapping'].get(model_name, model_name)
        
        # Check if model is already loaded (check both cache and backend)
        if local_model in self.loaded_models:
            return True
            
        loaded_models = await self.lms_client.models.list_loaded()
        if any(m.identifier == local_model for m in loaded_models):
            # Model is loaded in backend but not in our cache, update cache
            self.loaded_models[local_model] = True
            return True
            
        # Load model programmatically
        try:
            model = await self.lms_client.models.load(local_model)
            self.loaded_models[local_model] = model  # Cache using local model name
            print(f"✓ Loaded local model: {local_model} for {model_name}")
            return True
        except Exception as e:
            print(f"✗ Failed to load {local_model}: {e}")
            return False
    
    async def completion_with_auto_load(self, model: str, messages: list, **kwargs) -> Any:
        """
        LiteLLM completion with automatic model loading via LM Studio SDK
        """
        # Step 1: Ensure model is loaded (LM Studio SDK)
        if self.config.get('use_local_models', False):
            await self.ensure_model_loaded(model)
            
            # Step 2: Route through LiteLLM to local endpoint
            return litellm.completion(
                model=f"lm_studio/{model}",  # LiteLLM's LM Studio provider prefix
                messages=messages,
                api_base=self.config['lm_studio_base_url'],
                **kwargs
            )
        else:
            # Step 2: Use OpenAI via LiteLLM (Phase 1)
            return litellm.completion(
                model=model,
                messages=messages,
                **kwargs
            )

# Usage in your agents
class EnhancedResearchAgent:
    def __init__(self):
        self.model_manager = EnhancedLocalModelManager(LITELLM_CONFIG)
    
    async def research(self, project_name: str) -> Dict:
        response = await self.model_manager.completion_with_auto_load(
            model="gpt-4.1",  # Will auto-load qwen2.5-72b-instruct locally
            messages=[{"role": "user", "content": f"Research {project_name}"}]
        )
        return {"analysis": response.choices[0].message.content}
```

**Key Benefits of This Architecture**:
1. **Programmatic Control**: No GUI needed, all model management via Python
2. **Auto-Loading**: Models loaded automatically when needed
3. **Unified Interface**: Same LiteLLM calls work for OpenAI or local models
4. **Resource Management**: Models can be unloaded when not needed
5. **Easy Switching**: Environment variable controls OpenAI vs local

---

### 7. Current Model Inventory & Enhanced Phase 2 Mapping

**Your Current OpenAI Models** → **Enhanced Phase 2 Mapping**:

| Agent/Component | Current Model | Usage Location | Phase 2 Local Equivalent | LM Studio SDK Action |
|---|---|---|---|---|
| **ResearchAgent** | `gpt-4.1` | `agents/research_agent.py:173` | `qwen2.5-72b-instruct` | Auto-load on first use |
| **SummaryAgent** | `gpt-4.1` | `agents/summary_agent.py:84` | `qwen2.5-72b-instruct` | Share loaded instance |
| **QuestionAgent (All modes)** | `o3` | `config/config.py:106` | `deepseek-r1-distill-qwen-32b` | Auto-load on reasoning tasks |
| **All Fallbacks** | Various | Multiple locations | Consolidated to above 2 models | Dynamic loading |
| **DeepResearchAgent** | `o4-mini-deep-research-2025-06-26` | `config/config.py:91` | **Phase 3**: Multi-agent system | Advanced orchestration |

**Enhanced Model Management Strategy**:
```python
# agents/model_orchestrator.py
import lmstudio as lms
import asyncio

class ModelOrchestrator:
    """
    Manages multiple models efficiently with LM Studio Python SDK
    """
    
    def __init__(self):
        self.client = lms.Client()
        self.model_usage_map = {
            'general': 'qwen2.5-72b-instruct',
            'reasoning': 'deepseek-r1-distill-qwen-32b'
        }
        self.active_models = {}
    
    async def load_for_workload(self, workload_type: str) -> str:
        """Load appropriate model for workload type"""
        model_id = self.model_usage_map[workload_type]
        
        if model_id not in self.active_models:
            print(f"Loading {model_id} for {workload_type} workload...")
            model = await self.client.models.load(model_id)
            self.active_models[model_id] = model
            
        return model_id
    
    async def optimize_memory(self):
        """Unload unused models to free GPU memory"""
        # Smart unloading based on usage patterns
        # Keep most recently used models loaded
        pass
```

**Required LM Studio Models for Enhanced Phase 2** (Only 2 models needed):
```bash
# Models managed programmatically via LM Studio Python SDK
1. qwen2.5-72b-instruct-q4_k_m.gguf           # 42GB, replaces gpt-4.1
2. deepseek-r1-distill-qwen-32b-q4_k_m.gguf   # 19GB, replaces o3 reasoning

# Total: ~61GB download, smart loading/unloading for memory management
# LM Studio Python SDK handles: loading, unloading, model switching, resource optimization
```

---

### 8. Enhanced Capabilities for Phase 2 with LM Studio SDK

**Your Task**: Prepare for advanced features with programmatic model control

#### A. Advanced Model Management
```python
# Enhanced model management with LM Studio Python SDK
import lmstudio as lms
from typing import Dict, List

class AdvancedModelManager:
    def __init__(self):
        self.client = lms.Client()
    
    async def load_model_with_config(self, model_path: str, config: Dict) -> Any:
        """Load model with specific configuration"""
        return await self.client.models.load(
            model_path,
            config={
                'gpu_layers': config.get('gpu_layers', -1),
                'context_length': config.get('context_length', 32768),
                'batch_size': config.get('batch_size', 512)
            }
        )
    
    async def smart_model_switching(self, task_type: str) -> str:
        """Switch models based on task requirements"""
        current_models = await self.client.models.list_loaded()
        
        if task_type == 'reasoning':
            # Unload general model, load reasoning model
            for model in current_models:
                if 'qwen2.5' in model.identifier:
                    await model.unload()
            return await self.load_model_with_config(
                'deepseek-r1-distill-qwen-32b',
                {'context_length': 65536}  # Larger context for reasoning
            )
        else:
            # Standard general purpose model
            return await self.load_model_with_config(
                'qwen2.5-72b-instruct',
                {'context_length': 32768}
            )
```

#### B. Agentic Flows with LM Studio SDK
The LM Studio SDK provides an `.act()` API for autonomous agent behavior:

```python
# agents/enhanced_agent.py  
import lmstudio as lms

class EnhancedAgent:
    def __init__(self):
        self.model = lms.llm("qwen2.5-72b-instruct")  # Auto-loads if needed
    
    async def autonomous_research(self, topic: str, tools: List):
        """Use LM Studio's .act() API for multi-step autonomous research"""
        
        def search_web(query: str) -> str:
            """Tool for web searching"""
            # Your web search implementation
            return f"Search results for: {query}"
        
        def analyze_data(data: str) -> str:
            """Tool for data analysis"""
            # Your analysis implementation
            return f"Analysis of: {data}"
        
        # Autonomous multi-step execution
        result = await self.model.act(
            prompt=f"Research {topic} comprehensively using available tools",
            tools=[search_web, analyze_data],
            max_rounds=5,  # Allow up to 5 tool-use rounds
            on_message=lambda msg: print(f"Agent: {msg}")
        )
        
        return result
```

#### C. Enhanced Integration with LiteLLM
```python
# integration/litellm_lmstudio_bridge.py
import litellm
import lmstudio as lms
from typing import Union

class LiteLLMLMStudioBridge:
    """
    Bridge that combines LiteLLM's API abstraction with LM Studio SDK's model management
    """
    
    def __init__(self):
        self.lms_client = lms.Client()
        self.model_cache = {}
    
    async def smart_completion(self, model: str, messages: list, **kwargs) -> Union[str, dict]:
        """
        Smart completion that:
        1. Uses LM Studio SDK for model management
        2. Routes through LiteLLM for API consistency
        3. Handles fallbacks automatically
        """
        
        # Step 1: Ensure model is available via LM Studio SDK
        local_model = await self._ensure_local_model(model)
        
        if local_model:
            # Step 2: Use LiteLLM with LM Studio provider
            return litellm.completion(
                model=f"lm_studio/{local_model}",
                messages=messages,
                api_base="http://localhost:1234/v1",
                **kwargs
            )
        else:
            # Step 3: Fallback to OpenAI via LiteLLM
            return litellm.completion(
                model=model,
                messages=messages,
                **kwargs
            )
    
    async def _ensure_local_model(self, openai_model: str) -> str:
        """Use LM Studio SDK to ensure model is loaded"""
        mapping = {
            'gpt-4.1': 'qwen2.5-72b-instruct',
            'o3': 'deepseek-r1-distill-qwen-32b'
        }
        
        local_model = mapping.get(openai_model)
        if not local_model:
            return None
            
        # Check if already loaded
        loaded = await self.lms_client.models.list_loaded()
        if any(m.identifier == local_model for m in loaded):
            return local_model
            
        # Load the model
        try:
            await self.lms_client.models.load(local_model)
            return local_model
        except Exception as e:
            print(f"Failed to load {local_model}: {e}")
            return None
```

**Key Benefits of Enhanced Phase 2**:
- **No GUI Dependency**: All model management via Python code
- **Automatic Model Loading**: Models loaded on-demand
- **Resource Optimization**: Smart loading/unloading based on usage
- **Agentic Capabilities**: Use `.act()` API for autonomous behavior
- **Unified Interface**: LiteLLM + LM Studio SDK work together seamlessly

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

# Phase 1: LiteLLM for unified API
litellm>=1.74.0

# Phase 2: LM Studio Python SDK for programmatic model management
lmstudio>=1.4.1

# Phase 3: Search engines and coordination
tavily-python>=0.3.0
requests>=2.31.0
aiohttp>=3.8.0

# Optional for enhanced research
# open_deep_research>=0.0.16  # For reference patterns only
```

**Installation Notes**:
```bash
# Install all requirements
pip install -r requirements.txt

# LM Studio CLI backend (required for SDK to work)
# Download LM Studio from https://lmstudio.ai/download
# CLI ships with LM Studio 0.2.22+, or install separately:
npx lmstudio install-cli

# Verify complete installation
lms --help                    # CLI backend
python -c "import lmstudio"   # Python SDK
python -c "import litellm"    # LiteLLM
```

**Component Relationship**:
- **LiteLLM**: API abstraction layer (Phase 1)
- **LM Studio Python SDK**: Model management and agentic capabilities (Phase 2+)
- **LM Studio CLI**: Backend service that SDK communicates with (required)
- **Architecture**: `Your Code → LiteLLM → LM Studio SDK → lms CLI → Local Models`

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