# agents/deep_research_agent.py
"""
Deep Research Agent for NEAR Catalyst Framework

This agent conducts deep, analyst-level research on potential hackathon partners using
LiteLLM with cost tracking. It builds upon the general research to create comprehensive
reports at the level of a research analyst.

Features:
- Uses o4-mini-deep-research converted to o4-mini for cost-effective deep research
- GPT-4.1 priming to enhance research quality
- Background mode for long-running analysis
- Isolated functionality for future model expansion
- LiteLLM native cost tracking
"""

import json
import time
import litellm
from config.config import DEEP_RESEARCH_CONFIG, TIMEOUTS
from database.usage_tracker import APIUsageTracker
from database.database_manager import DatabaseManager


class DeepResearchAgent:
    """
    Agent that performs deep research analysis using LiteLLM with cost tracking.
    
    This agent:
    1. Takes general research from ResearchAgent
    2. Uses GPT-4.1 to create an enhanced research prompt
    3. Executes deep research using o4-mini model
    4. Returns comprehensive analyst-level findings
    """
    
    def __init__(self, client=None, db_manager=None, usage_tracker=None):
        """Initialize the deep research agent with usage tracking."""
        self.config = DEEP_RESEARCH_CONFIG
        self.timeout = TIMEOUTS['deep_research_agent']
        
        # Initialize usage tracking
        self.db_manager = db_manager or DatabaseManager()
        self.usage_tracker = usage_tracker or APIUsageTracker(None, self.db_manager)
    
    def is_enabled(self):
        """Check if deep research is enabled in configuration."""
        return self.config['enabled']
    
    def get_estimated_cost(self):
        """Return estimated cost per analysis."""
        return self.config['cost_per_input']
    
    def create_enhanced_prompt(self, project_name, general_research):
        """
        Create an enhanced research prompt using GPT-4.1 priming.
        
        Args:
            project_name (str): Name of the project to research
            general_research (str): Initial research findings
            
        Returns:
            str: Enhanced research prompt for deep analysis
        """
        # Set context for usage tracking
        self.usage_tracker.set_context(project_name, "deep_research_agent")
        
        priming_prompt = f"""You are a senior research analyst creating a deep research prompt for "{project_name}".

Based on this initial research:
{general_research}

Create a comprehensive research prompt that would guide a deep research analysis to uncover:
1. Technical architecture and integration capabilities
2. Developer ecosystem and community engagement
3. Partnership history and collaboration patterns
4. Market positioning and competitive advantages
5. Hackathon readiness and developer support quality

The prompt should be specific, actionable, and designed to produce analyst-level insights about hackathon catalyst potential.

Return only the research prompt, no additional commentary."""

        try:
            priming_response = self.usage_tracker.track_chat_completions_create(
                model="gpt-4.1",
                operation_type="priming",
                messages=[{"role": "user", "content": priming_prompt}],
                max_tokens=800,
                timeout=self.timeout
            )
            
            enhanced_prompt = priming_response.choices[0].message.content.strip()
            return enhanced_prompt
            
        except Exception as e:
            print(f"      ⚠️ Enhanced prompt creation failed: {e}")
            # Return fallback prompt
            return f"Conduct deep research analysis on {project_name} focusing on hackathon catalyst potential, technical capabilities, developer ecosystem, and partnership opportunities."
    
    def _get_fallback_prompt(self, project_name, general_research):
        """Fallback prompt if GPT-4.1 priming fails."""
        return f"""
Conduct comprehensive research on "{project_name}" as a potential partnership for NEAR Protocol's hackathon and developer ecosystem.

BACKGROUND CONTEXT:
{general_research[:2000]}

RESEARCH OBJECTIVES:
Analyze this project's potential as a hackathon co-creation partner that can create "1+1=3" value for NEAR developers.

ANALYSIS FRAMEWORK:
Evaluate against six partnership criteria:
1. Gap-Filler: Does it fill technology gaps NEAR lacks?
2. New Proof-Points: Does it enable novel use cases with NEAR?
3. Clear Story: Is there a simple value proposition?
4. Shared Audience: Same developers, different workflow functions?
5. Low-Friction Integration: Can developers integrate in hours?
6. Hands-On Support: Will they provide hackathon mentors/bounties/tooling?

REQUIRED OUTPUT:
- Comprehensive analysis organized by the six criteria
- Score each criterion: Positive (+1), Neutral (0), Negative (-1)
- Include evidence, examples, and source citations
- Provide overall partnership recommendation

Focus on factual, verifiable information from official sources, documentation, and developer community feedback.
"""
    
    def analyze(self, project_name, general_research):
        """
        Conduct deep research analysis on a project.
        
        Args:
            project_name (str): Name of the project
            general_research (str): General research content from ResearchAgent
            
        Returns:
            dict: Deep research results with comprehensive analysis
        """
        if not self.is_enabled():
            return {
                "content": "Deep research is disabled in configuration",
                "sources": [],
                "success": False,
                "enabled": False,
                "estimated_cost": self.get_estimated_cost()
            }
        
        print(f"  🔬 Running deep research analysis (estimated cost: ${self.get_estimated_cost():.2f})...")
        start_time = time.time()
        
        try:
            # Step 1: Create enhanced prompt using GPT-4.1
            print(f"  📝 Creating enhanced research prompt...")
            enhanced_prompt = self.create_enhanced_prompt(project_name, general_research)
            
            # Step 2: Execute deep research
            print(f"  🌐 Executing deep research (this may take several minutes)...")
            
            # Convert o4-mini-deep-research to o4-mini for LiteLLM compatibility
            model_name = self.config['model']
            if model_name == 'o4-mini-deep-research-2025-06-26':
                model_name = 'o4-mini'
            
            # Execute deep research using LiteLLM with usage tracking
            print(f"  🔬 Executing deep research with {model_name}...")
            deep_research_response = self.usage_tracker.track_chat_completions_create(
                model=model_name,
                operation_type="deep_research",
                messages=[{"role": "user", "content": enhanced_prompt}],
                timeout=self.config['timeout']
            )
            
            # Extract response content (LiteLLM returns OpenAI-compatible format)
            deep_research_content = deep_research_response.choices[0].message.content
            sources = []  # Web search and tool usage will be handled in future phases
            tool_calls_made = 0
            
            elapsed_time = time.time() - start_time
            print(f"  ✓ Deep research completed in {elapsed_time:.1f} seconds ({tool_calls_made} tool calls)")
            
            return {
                "content": deep_research_content,
                "sources": sources,
                "success": True,
                "enabled": True,
                "elapsed_time": elapsed_time,
                "tool_calls_made": tool_calls_made,
                "estimated_cost": self.get_estimated_cost(),
                "enhanced_prompt": enhanced_prompt[:500] + "..." if len(enhanced_prompt) > 500 else enhanced_prompt
            }
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"  ❌ Deep research failed after {elapsed_time:.1f} seconds: {e}")
            return {
                "content": f"Deep research failed for {project_name}: {str(e)}",
                "sources": [],
                "success": False,
                "enabled": True,
                "error": str(e),
                "elapsed_time": elapsed_time,
                "estimated_cost": self.get_estimated_cost()
            }
    
    def get_config_status(self):
        """Get current configuration status for debugging."""
        return {
            "enabled": self.config['enabled'],
            "model": self.config['model'],
            "priming_model": self.config['priming_model'],
            "estimated_cost_per_analysis": self.config['cost_per_input'],
            "timeout_seconds": self.config['timeout'],
            "background_mode": self.config['background_mode'],
            "max_tool_calls": self.config.get('max_tool_calls', 'unlimited')
        } 