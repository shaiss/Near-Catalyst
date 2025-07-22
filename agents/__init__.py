# agents/__init__.py
"""
Multi-Agent System for NEAR Partnership Analysis

This package contains the specialized AI agents that work together to analyze
potential technical partners for NEAR Protocol hackathons and developer events.

Agents:
- ResearchAgent: Gathers comprehensive project information
- QuestionAgent: Analyzes specific diagnostic questions  
- SummaryAgent: Synthesizes results into final recommendations

The system implements a "Framework for Choosing Complementary Technical Partners"
to identify collaborators that create a "1 + 1 = 3" value proposition.
"""

from .research_agent import ResearchAgent
from .question_agent import QuestionAgent
from .summary_agent import SummaryAgent
from .config import (
    DIAGNOSTIC_QUESTIONS, 
    DATABASE_NAME, 
    NEAR_CATALOG_API,
    TIMEOUTS,
    PARALLEL_CONFIG,
    SCORE_THRESHOLDS,
    RECOMMENDATIONS
)

__all__ = [
    'ResearchAgent',
    'QuestionAgent', 
    'SummaryAgent',
    'DIAGNOSTIC_QUESTIONS',
    'DATABASE_NAME',
    'NEAR_CATALOG_API',
    'TIMEOUTS',
    'PARALLEL_CONFIG',
    'SCORE_THRESHOLDS',
    'RECOMMENDATIONS'
] 