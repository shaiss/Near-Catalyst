# config/config.py
"""
Configuration module for NEAR Catalyst Framework Multi-Agent System.

Defines the diagnostic questions, scoring thresholds, timeouts, and database settings
for discovering hackathon co-creation partners that unlock developer potential.

Features:
- Six-question catalyst discovery survey
- Hackathon catalyst benchmarks loader
- Multi-agent coordination timeouts
- Database configuration for analysis persistence
- Phase 2: LM Studio Python SDK configuration for local models
"""

import json
import os

# Define the 6 diagnostic questions from the framework
DIAGNOSTIC_QUESTIONS = [
    {
        "id": 1,
        "key": "gap_filler",
        "question": "Gap-Filler?",
        "description": "Does the partner's tech fill a strategic gap rather than overlap NEAR's core blockchain functionality?",
        "search_focus": "technical capabilities that complement (not compete with) NEAR Protocol, strategic gaps in NEAR's developer stack, unique infrastructure NEAR doesn't provide natively"
    },
    {
        "id": 2,
        "key": "new_proof_points",
        "question": "New Proof-Points?",
        "description": "Will the combo unlock use-cases that neither NEAR nor the partner can deliver alone?",
        "search_focus": "novel use cases enabled by combining NEAR + partner technology, hackathon demos that showcase joint capabilities, applications impossible on either platform alone"
    },
    {
        "id": 3,
        "key": "clear_story",
        "question": "Clear Story?",
        "description": "Can you state the joint value in one sentence—your 'Better Together' pitch—without diagrams?",
        "search_focus": "simple value proposition, clear integration benefits, one-sentence explanation of NEAR + partner value, 'Better Together' narrative"
    },
    {
        "id": 4,
        "key": "shared_audience_different_function",
        "question": "Shared Audience, Different Function?",
        "description": "Do both parties serve the same developers while handling different steps in their workflow?",
        "search_focus": "developer audience overlap with NEAR, different workflow functions, complementary developer tools, non-competitive positioning in developer journey"
    },
    {
        "id": 5,
        "key": "low_friction_integration",
        "question": "Low-Friction Integration?",
        "description": "Can builders wire the two stacks together in hours with docs, SDKs, and sample repos ready?",
        "search_focus": "integration documentation, SDK availability, sample repositories, developer onboarding speed, hackathon-ready tools and tutorials"
    },
    {
        "id": 6,
        "key": "hands_on_support",
        "question": "Hands-On Support?",
        "description": "Will the partner supply mentors, bounties, or tooling that directly helps hackathon teams?",
        "search_focus": "hackathon mentorship, bounty programs, technical support, hands-on developer assistance, partnership event participation"
    }
]

# Database configuration
DATABASE_NAME = 'project_analyses_multi_agent.db'
DATABASE_PRAGMAS = [
    'PRAGMA journal_mode=WAL;',
    'PRAGMA synchronous=NORMAL;',
    'PRAGMA cache_size=10000;',
    'PRAGMA temp_store=memory;'
]

# API endpoints and timeouts
NEAR_CATALOG_API = {
    'projects': 'https://api.nearcatalog.org/projects',
    'project_detail': 'https://api.nearcatalog.org/project?pid={slug}',
    'timeout': 30
}

# Agent timeouts (in seconds)
TIMEOUTS = {
    'research_agent': 120,
    'question_agent': 180,
    'analysis_agent': 60,
    'summary_agent': 90,
    'deep_research_agent': 1800  # 30 minutes for deep research (can take a long time)
}

# Deep Research Configuration
DEEP_RESEARCH_CONFIG = {
    'enabled': False,  # Off by default due to cost ($2 per input)
    'model': 'o4-mini',  # Use standard LiteLLM model name directly
    'priming_model': 'gpt-4.1',  # Model to prime the deep research agent
    'use_cached_input': True,  # Use cached input to reduce costs
    'max_tool_calls': 50,  # Limit tool calls to control cost and latency
    'timeout': 1800,  # 30 minutes timeout
    'background_mode': True,  # Use background mode for long-running tasks (required for reliability)
    'cost_per_input': 2.00,  # Cost tracking for budgeting
    'tools': [
        {"type": "web_search_preview"},
        {"type": "code_interpreter", "container": {"type": "auto"}}
    ]
}

# Question Agent Two-Step Configuration
# Step 1: Research with web search, Step 2: Analysis with reasoning
QUESTION_AGENT_CONFIG = {
    # Research Step: Web search for gathering information
    'research_model': {
        'production': 'gpt-4o-search-preview',      # Web search enabled for data gathering
        'development': 'gpt-4o-search-preview',     # Consistent across environments
        'max_output_tokens': 4000,   # Standard output tokens for search model
        'use_reasoning': False,      # Research step doesn't need reasoning
        'enable_web_search': True    # REQUIRED for information gathering
    },
    
    # Analysis Step: Reasoning model for deep analysis of research
    'reasoning_model': {
        'production': 'o4-mini',    # Cost-effective reasoning model for production
        'development': 'o4-mini',   # Same model for dev/testing (consistent & affordable)
        'effort': 'medium',         # Balance between speed and reasoning quality
        'max_output_tokens': 8000,  # Higher tokens for reasoning analysis
        'use_reasoning': True,      # Enable reasoning tokens extraction
        'include_reasoning_summary': True,  # Include reasoning summary in response
        'reasoning_effort': 'medium'  # Reasoning effort level
    },
    
    # Fallback configuration
    'fallback_research_model': 'gpt-4o',           # Fallback if search model unavailable
    'fallback_reasoning_model': 'o3-mini',         # Fallback reasoning model (cheaper than o1)
    'use_web_search': True,       # Enable web search for data enrichment (REQUIRED)
    
    # Context optimization for two-step process
    'context_optimization': {
        'max_research_context': 12000,  # Max context for research step
        'max_analysis_context': 15000,  # Max context for analysis step (includes research)
        'preserve_sections': ['general_research', 'deep_research', 'question_focus', 'research_results']
    },
    
    # Two-step workflow settings
    'workflow': {
        'enable_two_step': True,    # Enable research -> analysis workflow
        'research_timeout': 120,    # Timeout for research step (seconds)
        'analysis_timeout': 180,    # Timeout for analysis step (seconds)
        'combine_results': True     # Combine research and analysis in final output
    }
}

# Parallel execution settings for question agents (within a single project)
PARALLEL_CONFIG = {
    'max_workers': 6,  # One per question
    'retry_attempts': 3,
    'retry_backoff': 0.1  # Base delay for exponential backoff
}

# Batch processing configuration for multiple projects
BATCH_PROCESSING_CONFIG = {
    'default_batch_size': 5,  # Process 5 projects concurrently by default
    'max_batch_size': 10,     # Maximum allowed batch size to prevent API rate limiting
    'inter_batch_delay': 2.0, # Seconds to wait between batches
    'project_delay': 0.5      # Seconds to wait between individual projects in a batch
}

# Benchmark format configuration
BENCHMARK_CONFIG = {
    'default_format': 'json',  # 'auto', 'json', or 'csv'
    'auto_detect': False,       # Whether to auto-detect preferred format
    'csv_priority': False       # Prioritize CSV files when both formats exist
}

# Score thresholds for recommendations (from "1+1=3" Partnership Framework)
SCORE_THRESHOLDS = {
    'strong_candidate': 4,     # +4 to +6: Strong candidate; explore MoU/co-marketing
    'mixed_fit': 0,            # 0 to +3: Mixed; negotiate scope
    'decline': None            # < 0: Decline or redesign the collaboration
}

RECOMMENDATIONS = {
    'strong_candidate': "Strong candidate; explore MoU/co-marketing",
    'mixed_fit': "Mixed; negotiate scope",
    'decline': "Decline or redesign the collaboration"
}

# Phase 2: LiteLLM + LM Studio SDK Configuration
LITELLM_CONFIG = {
    'use_local_models': os.getenv('USE_LOCAL_MODELS', 'false').lower() == 'true',
    'use_lmstudio_sdk': os.getenv('USE_LMSTUDIO_SDK', 'true').lower() == 'true',
    
    # LM Studio Server Configuration (Local vs Remote)
    'use_remote_lmstudio': os.getenv('USE_REMOTE_LMSTUDIO', 'false').lower() == 'true',
    'lm_studio_base_url': os.getenv('LM_STUDIO_API_BASE', 'http://localhost:1234/v1'),
    'lm_studio_api_key': os.getenv('LM_STUDIO_API_KEY', ''),  # Usually not needed
    
    # Remote LM Studio Configuration (when USE_REMOTE_LMSTUDIO=true)
    'remote_lmstudio_url': os.getenv('REMOTE_LMSTUDIO_URL', 'http://your-server:1234/v1'),
    'remote_lmstudio_api_key': os.getenv('REMOTE_LMSTUDIO_API_KEY', ''),  # Usually not needed
    
    # Phase 2: OpenAI → Local OSS Model Mapping
    'model_mapping': {
        # Core models (via LM Studio Python SDK + local API)
        'gpt-4.1': 'qwen2.5-72b-instruct',                 # Research, Summary, Question agents
        'o3': 'deepseek-r1-distill-qwen-32b',              # Question agent reasoning (production)
        'o4-mini': 'deepseek-r1-distill-qwen-32b',         # Use same reasoning model  
        'gpt-4': 'qwen2.5-72b-instruct',                   # General fallback
        'gpt-4.1-mini': 'qwen2.5-72b-instruct',            # General fallback
        'gpt-4o-search-preview': 'qwen2.5-72b-instruct',   # Research fallback (will add search later)
        
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
    'auto_load_models': True,  # Automatically load models when needed (local only)
    'model_load_timeout': 300,  # 5 minutes for model loading
    'local_models_path': os.getenv('LOCAL_MODELS_PATH'),  # Path to pre-downloaded models
    'default_generation_config': {
        'temperature': 0.1,
        'max_tokens': 2048,
        'top_p': 0.9
    },
    # Required models for Phase 2
    'required_models': [
        'qwen2.5-72b-instruct',      # General purpose model
        'deepseek-r1-distill-qwen-32b'  # Reasoning model
    ],
    
    # Remote LM Studio specific settings
    'remote_model_management': os.getenv('USE_REMOTE_LMSTUDIO', 'false').lower() == 'true',
    'disable_sdk_for_remote': True,  # Don't use Python SDK for remote servers
}


def get_lmstudio_endpoint():
    """
    Get the appropriate LM Studio endpoint based on local vs remote configuration.
    
    Returns:
        dict: Dictionary with 'url' and 'api_key' for the LM Studio endpoint
    """
    if LITELLM_CONFIG['use_remote_lmstudio']:
        return {
            'url': LITELLM_CONFIG['remote_lmstudio_url'],
            'api_key': LITELLM_CONFIG['remote_lmstudio_api_key'],
            'is_remote': True
        }
    else:
        return {
            'url': LITELLM_CONFIG['lm_studio_base_url'],
            'api_key': LITELLM_CONFIG['lm_studio_api_key'],
            'is_remote': False
        }

# Partnership Framework Benchmarks
def load_partnership_benchmarks(format_preference: str = 'auto'):
    """
    Load partnership benchmarks with automatic CSV-to-JSON synchronization.
    
    Behavior:
    - Default format is JSON (for tech users)
    - If CSV files are newer than JSON, auto-convert CSV to JSON (for non-tech users)
    - If JSON is newer than CSV, use JSON and ignore CSV files
    
    Args:
        format_preference: 'auto', 'json', or 'csv'
        
    Returns:
        dict: Partnership benchmarks data
    """
    try:
        from .benchmark_converter import BenchmarkConverter
        
        converter = BenchmarkConverter(os.path.dirname(__file__))
        
        # Handle format preference
        if format_preference == 'auto':
            if BENCHMARK_CONFIG['auto_detect']:
                # Check if CSV files are newer and auto-sync if needed
                preferred_format = converter.detect_preferred_format()
                if preferred_format == 'csv':
                    print("📝 CSV files are newer than JSON - auto-syncing to JSON...")
                    converter.csv_to_json()  # Auto-convert CSV to JSON
                    preferred_format = 'json'  # Use the updated JSON
                format_preference = preferred_format
            else:
                # Use default format but still check for auto-sync
                if _should_auto_sync_csv_to_json(converter):
                    print("📝 CSV files are newer than JSON - auto-syncing to JSON...")
                    converter.csv_to_json()
                format_preference = BENCHMARK_CONFIG['default_format']
        elif format_preference == 'json':
            # Even when explicitly requesting JSON, check for auto-sync
            if _should_auto_sync_csv_to_json(converter):
                print("📝 CSV files are newer than JSON - auto-syncing to JSON...")
                converter.csv_to_json()
        
        # Load benchmark data
        return converter.get_benchmark_data(format_preference)
        
    except ImportError:
        print("Warning: BenchmarkConverter not available, using default benchmarks")
        return _get_default_benchmarks()
    except Exception as e:
        print(f"Warning: Could not load partnership benchmarks: {e}")
        return _get_default_benchmarks()


def _should_auto_sync_csv_to_json(converter):
    """
    Check if CSV files should auto-sync to JSON.
    
    Args:
        converter: BenchmarkConverter instance
        
    Returns:
        bool: True if CSV files are newer and should trigger auto-sync
    """
    try:
        csv_files = [
            converter.csv_examples_file,
            converter.csv_principles_file, 
            converter.csv_scoring_file
        ]
        
        # Check if all CSV files exist
        csv_exist = all(os.path.exists(f) for f in csv_files)
        json_exists = os.path.exists(converter.json_file)
        
        if not csv_exist or not json_exists:
            return False
            
        # Check if any CSV file is newer than JSON
        json_mtime = os.path.getmtime(converter.json_file)
        csv_mtimes = [os.path.getmtime(f) for f in csv_files]
        newest_csv_mtime = max(csv_mtimes)
        
        # Auto-sync if any CSV is newer than JSON
        return newest_csv_mtime > json_mtime
        
    except Exception:
        return False

def _get_default_benchmarks():
    """Fallback default benchmarks if loading fails."""
    return {
        "framework_benchmarks": {
            "complementary_examples": [
                {"partner": "NEAR + [Confidential Computing Partner]", "score": 6, "type": "privacy/compute layer", "description": "perfect complementary partner"},
                {"partner": "NEAR + [Storage Solution]", "score": 6, "type": "decentralized storage", "description": "strategic gap filler"},
                {"partner": "NEAR + [Oracle Provider]", "score": 3, "type": "data feeds", "description": "solid but needs integration work"}
            ],
            "competitive_examples": [
                {"partner": "NEAR + [Competing L1-A]", "score": -4, "type": "competing blockchain", "description": "competitive overlap, misaligned"},
                {"partner": "NEAR + [Competing L1-B]", "score": -3, "type": "competing platform", "description": "either/or confusion"},
                {"partner": "NEAR + [Overlapping Service]", "score": -1, "type": "feature overlap", "description": "competes for same developers"}
            ]
        },
        "framework_principles": {
            "complementary_signs": [
                "Fills a strategic gap rather than overlap NEAR's core",
                "Unlocks use-cases that neither side can deliver alone", 
                "Clear 'Better Together' story (one sentence, no diagrams)",
                "Same developers, different workflow functions",
                "Low-friction integration (wire together in hours)",
                "Hands-on support (mentors, bounties, tooling)"
            ],
            "competitive_red_flags": [
                "Direct product overlap with NEAR's core functionality",
                "Creates 'either/or' dilemma for developers",
                "Vague or irrelevant value proposition",
                "Conflicting technical standards or philosophies", 
                "Integration friction (complex workarounds required)",
                "'Logo on a slide' partnerships (purely transactional)"
            ]
        }
    }

def format_benchmark_examples_for_prompt(format_preference: str = 'auto'):
    """Format benchmark examples for use in analysis prompts."""
    benchmarks = load_partnership_benchmarks(format_preference)

    examples_text = "FRAMEWORK BENCHMARKS (for scoring reference):\n"

    # Add complementary examples
    for example in benchmarks["framework_benchmarks"]["complementary_examples"]:
        examples_text += f"• {example['partner']} ({example['type']}): {example['score']:+d} total ({example['description']})\n"

    # Add competitive examples
    for example in benchmarks["framework_benchmarks"]["competitive_examples"]:
        examples_text += f"• {example['partner']} ({example['type']}): {example['score']:+d} total ({example['description']})\n"

    return examples_text

def get_framework_principles(format_preference: str = 'auto'):
    """Get framework principles for complementary vs competitive evaluation."""
    benchmarks = load_partnership_benchmarks(format_preference)
    principles = benchmarks.get("framework_principles", {})

    complementary_signs = "\n".join([f"  - {sign}" for sign in principles.get("complementary_signs", [])])
    competitive_flags = "\n".join([f"  - {flag}" for flag in principles.get("competitive_red_flags", [])])

    return f"""
Apply the Partnership Framework Principles:
✅ COMPLEMENTARY SIGNS:
{complementary_signs}

❌ COMPETITIVE RED FLAGS:
{competitive_flags}
""" 