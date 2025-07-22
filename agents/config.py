# agents/config.py
"""
Configuration module for NEAR Partnership Analysis Multi-Agent System.

This module contains:
- Diagnostic questions framework
- Database configuration
- API endpoints and timeouts
- Partnership framework benchmarks loader
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
    'summary_agent': 90
}

# Parallel execution settings
PARALLEL_CONFIG = {
    'max_workers': 6,  # One per question
    'retry_attempts': 3,
    'retry_backoff': 0.1  # Base delay for exponential backoff
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

# Partnership Framework Benchmarks
def load_partnership_benchmarks():
    """Load partnership benchmarks from external JSON file."""
    benchmarks_path = os.path.join(os.path.dirname(__file__), 'partnership_benchmarks.json')
    
    # Default benchmarks if file doesn't exist - using generic examples, not real evaluations
    default_benchmarks = {
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

    try:
        if os.path.exists(benchmarks_path):
            with open(benchmarks_path, 'r') as f:
                return json.load(f)
        else:
            # Create default file if it doesn't exist
            with open(benchmarks_path, 'w') as f:
                json.dump(default_benchmarks, f, indent=2)
            return default_benchmarks
    except Exception as e:
        print(f"Warning: Could not load partnership benchmarks: {e}")
        return default_benchmarks

def format_benchmark_examples_for_prompt():
    """Format benchmark examples for use in analysis prompts."""
    benchmarks = load_partnership_benchmarks()

    examples_text = "FRAMEWORK BENCHMARKS (for scoring reference):\n"

    # Add complementary examples
    for example in benchmarks["framework_benchmarks"]["complementary_examples"]:
        examples_text += f"• {example['partner']} ({example['type']}): {example['score']:+d} total ({example['description']})\n"

    # Add competitive examples
    for example in benchmarks["framework_benchmarks"]["competitive_examples"]:
        examples_text += f"• {example['partner']} ({example['type']}): {example['score']:+d} total ({example['description']})\n"

    return examples_text

def get_framework_principles():
    """Get framework principles for complementary vs competitive evaluation."""
    benchmarks = load_partnership_benchmarks()
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