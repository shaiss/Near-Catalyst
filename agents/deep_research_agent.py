# agents/deep_research_agent.py
"""
Deep Research Agent for NEAR Catalyst Framework

This agent conducts deep, analyst-level research on potential hackathon partners using
LiteLLM Router with automatic local model routing and fallbacks. It builds upon the general 
research to create comprehensive reports at the level of a research analyst.

Features:
- Uses o4-mini for cost-effective deep research
- GPT-4.1 priming to enhance research quality
- Background mode for long-running analysis
- Isolated functionality for future model expansion
- LiteLLM Router with automatic fallbacks
"""

import json
import time
from config.config import DEEP_RESEARCH_CONFIG, TIMEOUTS
from agents.litellm_router import completion


class DeepResearchAgent:
    """
    Agent that performs deep research analysis using LiteLLM Router with automatic fallbacks.
    
    This agent:
    1. Takes general research as input
    2. Uses GPT-4.1 priming to enhance context
    3. Conducts detailed analysis with o4-mini
    4. Returns comprehensive analyst-level research
    """
    
    def __init__(self, db_manager=None, usage_tracker=None):
        """Initialize the deep research agent."""
        self.config = DEEP_RESEARCH_CONFIG
        self.timeout = TIMEOUTS['deep_research_agent']
        self.db_manager = db_manager
        
    def is_enabled(self):
        """Check if deep research is enabled in configuration."""
        return self.config.get('enabled', False)
    
    def get_estimated_cost(self):
        """Get estimated cost per project for deep research."""
        return self.config.get('cost_per_input', 2.00)
    
    def analyze(self, project_name, general_research_content, context=None):
        """
        Conduct deep research analysis on a project.
        
        Args:
            project_name: Name of the project to analyze  
            general_research_content: Content from general research agent
            context: Additional context (optional)
            
        Returns:
            Dict with deep research results, sources, and cost information
        """
        
        if not self.is_enabled():
            return {
                "success": False,
                "content": "Deep research is disabled",
                "sources": [],
                "enabled": False,
                "cost": 0.0
            }
        
        print(f"      🔬 Conducting deep research on {project_name}...")
        
        try:
            return self._run_analysis_workflow(project_name, general_research_content, context)
                
        except Exception as e:
            error_msg = f"Deep research failed: {str(e)}"
            print(f"      ❌ {error_msg}")
            
            return {
                "success": False,
                "content": "",
                "sources": [],
                "enabled": True,
                "error": error_msg,
                "cost": 0.0
            }

    def _run_analysis_workflow(self, project_name, general_research_content, context=None):
        """
        Execute the deep research analysis workflow.
        
        Args:
            project_name: Name of the project to analyze
            general_research_content: Content from general research agent
            context: Additional context (optional)
            
        Returns:
            Dict with workflow results and cost information
        """
        total_cost = 0.0
        
        # Step 1: Prime with GPT-4.1 for enhanced context
        priming_model = self.config.get('priming_model', 'gpt-4.1')
        print(f"      📋 Priming analysis with {priming_model}...")
        priming_result = self._prime_analysis(project_name, general_research_content)
        total_cost += priming_result.get('cost', 0.0)
        
        if not priming_result['success']:
            return priming_result
        
        # Step 2: Conduct deep research with o4-mini
        analysis_model = self.config.get('model', 'o4-mini')
        print(f"      🧠 Deep analysis with {analysis_model}...")
        deep_analysis_result = self._conduct_deep_analysis(
            project_name, 
            general_research_content, 
            priming_result['content']
        )
        total_cost += deep_analysis_result.get('cost', 0.0)
        
        if deep_analysis_result['success']:
            print(f"      ✅ Deep research completed - Cost: ${total_cost:.4f}")
            
            # Format and return combined results
            return self._format_analysis_results(priming_result, deep_analysis_result, total_cost)
        else:
            return deep_analysis_result

    def _format_analysis_results(self, priming_result, deep_analysis_result, total_cost):
        """
        Format the final analysis results.
        
        Args:
            priming_result: Result from priming step
            deep_analysis_result: Result from deep analysis step
            total_cost: Combined cost of both steps
            
        Returns:
            Dict with formatted results
        """
        return {
            "success": True,
            "content": deep_analysis_result['content'],
            "sources": ["deep_research_analysis"],
            "enabled": True,
            "priming_cost": priming_result.get('cost', 0.0),
            "analysis_cost": deep_analysis_result.get('cost', 0.0),
            "total_cost": total_cost,
            "elapsed_time": deep_analysis_result.get('elapsed_time', 0),
            "enhanced_prompt": True
        }
    
    def _prime_analysis(self, project_name, general_research):
        """
        Prime the analysis using GPT-4.1 to enhance context and focus.
        
        Args:
            project_name: Name of the project
            general_research: General research content
            
        Returns:
            Dict with priming results and cost
        """
        
        priming_prompt = f"""You are a senior research analyst preparing context for deep analysis of "{project_name}" as a potential NEAR Protocol hackathon catalyst partner.

GENERAL RESEARCH CONTEXT:
{general_research[:3000]}

Your task is to enhance and structure this research for deep analysis. Focus on:

1. **Key Partnership Signals**: What stands out as most relevant for hackathon collaboration?
2. **Research Gaps**: What important questions remain unanswered?
3. **Analysis Focus Areas**: What aspects deserve deeper investigation?
4. **Developer Impact Potential**: How could this project amplify developer capabilities during hackathons?

Provide a structured enhancement of the research that will guide comprehensive analysis. Be specific about technical capabilities, developer tools, community engagement, and partnership readiness.

Output Format:
- Executive Summary: 2-3 sentences on partnership potential
- Key Strengths: Specific technical or community advantages
- Areas for Investigation: What needs deeper research
- Hackathon Relevance: How this could benefit time-constrained developers"""

        try:
            # Use LiteLLM Router for priming
            response = completion(
                model=self.config.get('priming_model', 'gpt-4.1'),
                messages=[{"role": "user", "content": priming_prompt}],
                temperature=0.1,
                max_tokens=1500,
                timeout=300  # 5 minutes for priming
            )
            
            # Safely extract content with validation
            if response.choices and len(response.choices) > 0 and hasattr(response.choices[0], 'message'):
                content = response.choices[0].message.content
            else:
                content = ""  # fallback for malformed response
            cost = 0.0
            
            # Extract cost and routing information
            if hasattr(response, '_hidden_params'):
                cost = response._hidden_params.get('response_cost', 0.0)
                local_used = response._hidden_params.get('local_model_used', False)
                router_tags = response._hidden_params.get('router_tags', [])
                
                if local_used:
                    print(f"      🆓 Priming with local model ({', '.join(router_tags)}) - Cost: Free")
                else:
                    print(f"      💰 Priming with OpenAI model ({', '.join(router_tags)}) - Cost: ${cost:.4f}")
            
            return {
                "success": True,
                "content": content,
                "cost": cost
            }
            
        except Exception as e:
            error_msg = f"Priming failed: {str(e)}"
            print(f"      ❌ {error_msg}")
            
            return {
                "success": False,
                "content": "",
                "error": error_msg,
                "cost": 0.0
            }
    
    def _conduct_deep_analysis(self, project_name, general_research, priming_content):
        """
        Conduct deep analysis using o4-mini with enhanced context.
        
        Args:
            project_name: Name of the project
            general_research: Original research content
            priming_content: Enhanced context from priming
            
        Returns:
            Dict with deep analysis results and cost
        """
        
        deep_analysis_prompt = f"""You are a senior partnership analyst conducting comprehensive research for NEAR Protocol's hackathon catalyst program.

PROJECT: {project_name}

ENHANCED CONTEXT FROM RESEARCH:
{priming_content}

ORIGINAL RESEARCH DATA:
{general_research[:4000]}

ANALYSIS MISSION:
Conduct analyst-level evaluation of this project's potential as a hackathon catalyst partner for NEAR Protocol. This analysis will inform strategic partnership decisions.

COMPREHENSIVE ANALYSIS REQUIREMENTS:

1. **TECHNOLOGY ASSESSMENT**
   - Core technical capabilities and unique value proposition
   - Integration complexity and developer experience
   - Compatibility with NEAR's technology stack
   - Speed of integration during hackathon timeframes

2. **DEVELOPER ECOSYSTEM ANALYSIS**
   - Target developer audience and overlap with NEAR community
   - Available tools, SDKs, documentation quality
   - Learning curve and onboarding experience
   - Community support and developer resources

3. **PARTNERSHIP READINESS EVALUATION**
   - Historical hackathon participation and support
   - Business development and partnership capabilities
   - Alignment with NEAR's developer-first philosophy
   - Capacity for hands-on mentorship and support

4. **STRATEGIC VALUE ASSESSMENT**
   - Unique capabilities that complement NEAR's offerings
   - Potential for "1 + 1 = 3" value creation
   - Market positioning and competitive landscape
   - Long-term strategic alignment potential

5. **IMPLEMENTATION ROADMAP**
   - Immediate hackathon collaboration opportunities
   - Technical integration requirements
   - Partnership structure recommendations
   - Risk factors and mitigation strategies

6. **QUANTITATIVE METRICS**
   - Developer adoption metrics and community size
   - Technical performance and reliability indicators
   - Partnership track record and success stories
   - Time-to-value for hackathon participants

Provide a comprehensive, analyst-level report that serves as the definitive assessment of this partnership opportunity. Focus on actionable insights and specific recommendations for NEAR's hackathon catalyst program."""

        start_time = time.time()
        
        try:
            # Use LiteLLM Router for deep analysis
            response = completion(
                model=self.config.get('model', 'o4-mini'),
                messages=[{"role": "user", "content": deep_analysis_prompt}],
                temperature=0.1,
                max_tokens=8000,  # Large output for comprehensive analysis
                timeout=self.timeout
            )
            
            elapsed_time = time.time() - start_time
            # Safely extract content with validation
            if response.choices and len(response.choices) > 0 and hasattr(response.choices[0], 'message'):
                content = response.choices[0].message.content
            else:
                content = ""  # fallback for malformed response
            cost = 0.0
            
            # Extract cost and routing information
            if hasattr(response, '_hidden_params'):
                cost = response._hidden_params.get('response_cost', 0.0)
                local_used = response._hidden_params.get('local_model_used', False)
                router_tags = response._hidden_params.get('router_tags', [])
                
                if local_used:
                    print(f"      🆓 Deep analysis with local model ({', '.join(router_tags)}) - Cost: Free")
                else:
                    print(f"      💰 Deep analysis with OpenAI model ({', '.join(router_tags)}) - Cost: ${cost:.4f}")
            
            return {
                "success": True,
                "content": content,
                "cost": cost,
                "elapsed_time": elapsed_time
            }
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"Deep analysis failed: {str(e)}"
            print(f"      ❌ {error_msg}")
            
            return {
                "success": False,
                "content": "",
                "error": error_msg,
                "cost": 0.0,
                "elapsed_time": elapsed_time
            } 