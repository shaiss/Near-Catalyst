# agents/config.py
"""
Configuration module for NEAR Partnership Analysis Multi-Agent System.

This module contains:
- Diagnostic questions framework
- Database configuration
- API endpoints and timeouts
"""

# Define the 6 diagnostic questions from the framework
DIAGNOSTIC_QUESTIONS = [
    {
        "id": 1,
        "key": "gap_filler",
        "question": "Gap-Filler?",
        "description": "Does the partner fill a technology gap NEAR lacks?",
        "search_focus": "technical capabilities, infrastructure, services that NEAR doesn't provide natively"
    },
    {
        "id": 2,
        "key": "new_proof_points", 
        "question": "New Proof-Points?",
        "description": "Does it enable new use cases/demos?",
        "search_focus": "use cases, applications, demos, innovative implementations"
    },
    {
        "id": 3,
        "key": "clear_story",
        "question": "One-Sentence Story?",
        "description": "Is there a clear value proposition?",
        "search_focus": "value proposition, messaging, developer experience, integration benefits"
    },
    {
        "id": 4,
        "key": "developer_friendly",
        "question": "Developer-Friendly?",
        "description": "Easy integration and learning curve?",
        "search_focus": "documentation, APIs, SDKs, developer tools, integration guides, tutorials"
    },
    {
        "id": 5,
        "key": "aligned_incentives",
        "question": "Aligned Incentives?",
        "description": "Mutual benefit and non-competitive?",
        "search_focus": "business model, partnerships, competition analysis, ecosystem positioning"
    },
    {
        "id": 6,
        "key": "ecosystem_fit",
        "question": "Ecosystem Fit?",
        "description": "Does it match NEAR's target audience?",
        "search_focus": "target audience, developer community, use cases that overlap with NEAR ecosystem"
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

# Score thresholds for recommendations
SCORE_THRESHOLDS = {
    'green_light': 4,      # +4 to +6: Strong partnership candidate
    'mid_tier': 0,         # 0 to +3: Solid fit, worth pursuing
    'decline': None        # < 0: Likely misaligned
}

RECOMMENDATIONS = {
    'green_light': "Green-light partnership. Strong candidate for strategic collaboration.",
    'mid_tier': "Solid mid-tier fit. Worth pursuing, but may require integration polish or focused support.",
    'decline': "Likely misaligned. Proceed with caution or decline, as it may create friction."
} 