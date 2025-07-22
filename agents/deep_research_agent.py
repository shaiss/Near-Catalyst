# agents/deep_research_agent.py
"""
Deep Research Agent for NEAR Catalyst Framework

This agent conducts deep, analyst-level research on potential hackathon partners using
OpenAI's deep research models. It builds upon the general research to create comprehensive
reports at the level of a research analyst.

Features:
- Uses o4-mini-deep-research-2025-06-26 for cost-effective deep research
- GPT-4.1 priming to enhance research quality
- Background mode for long-running analysis
- Isolated functionality for future model expansion
"""

import json
import time
from config.config import DEEP_RESEARCH_CONFIG, TIMEOUTS


class DeepResearchAgent:
    """
    Agent that performs deep research analysis using OpenAI's deep research models.
    
    This agent:
    1. Takes general research from ResearchAgent
    2. Uses GPT-4.1 to create an enhanced research prompt
    3. Executes deep research using o4-mini-deep-research model
    4. Returns comprehensive analyst-level findings
    """
    
    def __init__(self, client):
        """Initialize the deep research agent with OpenAI client."""
        self.client = client
        self.config = DEEP_RESEARCH_CONFIG
        self.timeout = TIMEOUTS['deep_research_agent']
    
    def is_enabled(self):
        """Check if deep research is enabled in configuration."""
        return self.config['enabled']
    
    def get_estimated_cost(self):
        """Return estimated cost per analysis."""
        return self.config['cost_per_input']
    
    def create_enhanced_prompt(self, project_name, general_research):
        """
        Use GPT-4.1 to create an enhanced prompt for deep research.
        
        Args:
            project_name (str): Name of the project
            general_research (str): General research content
            
        Returns:
            str: Enhanced prompt for deep research
        """
        priming_prompt = f"""
You are a partnership research strategist preparing a comprehensive research brief for a deep research analyst.

Based on the general research provided below about "{project_name}", create detailed research instructions that will enable a research analyst to conduct a thorough partnership evaluation for NEAR Protocol's hackathon program.

GENERAL RESEARCH TO BUILD UPON:
{general_research[:3000]}  # Truncate to avoid token limits

CREATE RESEARCH INSTRUCTIONS THAT:

1. **Maximize Specificity and Detail**
   - Build upon all details from the general research
   - Identify specific technical integration patterns to investigate
   - List key partnership evaluation criteria from NEAR's perspective

2. **Target Partnership-Specific Analysis**
   - Focus on "1+1=3" value creation potential
   - Investigate complementary technology capabilities
   - Analyze developer ecosystem fit and integration complexity
   - Research hackathon and developer community engagement history

3. **Request Structured Analysis Format**
   - Ask for analysis organized by the six diagnostic questions:
     * Gap-Filler? (Technology gaps NEAR lacks)
     * New Proof-Points? (Novel use cases enabled by combination)
     * Clear Story? (One-sentence value proposition)
     * Shared Audience, Different Function? (Same developers, different workflow steps)
     * Low-Friction Integration? (Hours to integrate with docs/SDKs)
     * Hands-On Support? (Hackathon mentors, bounties, tooling)

4. **Prioritize Reliable Sources**
   - Prefer official documentation, GitHub repositories, and verified technical resources
   - Include developer community feedback and integration examples
   - Focus on factual, measurable partnership indicators

5. **Include Tables and Structured Data**
   - Request comparison tables where relevant
   - Ask for structured scoring based on partnership criteria
   - Include source citations and links for verification

Format your response as clear, actionable research instructions that will enable deep analysis of this project's partnership potential with NEAR Protocol.
"""
        
        try:
            priming_response = self.client.responses.create(
                model=self.config['priming_model'],
                input=priming_prompt,
                timeout=60  # Short timeout for priming
            )
            
            enhanced_prompt = ""
            for item in priming_response.output:
                if item.type == "message" and item.role == "assistant":
                    enhanced_prompt = item.content[0].text
                    break
            
            return enhanced_prompt
            
        except Exception as e:
            print(f"  WARNING: Prompt enhancement failed, using fallback: {e}")
            return self._get_fallback_prompt(project_name, general_research)
    
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
            
            # Build request parameters
            request_params = {
                "model": self.config['model'],
                "input": enhanced_prompt,
                "tools": self.config['tools'],
                "timeout": self.config['timeout'],
                "store": True  # Required for background mode
            }
            
            # Add optional parameters
            if self.config['background_mode']:
                request_params["background"] = True
            
            if self.config.get('max_tool_calls'):
                request_params["max_tool_calls"] = self.config['max_tool_calls']
            
            # Execute deep research
            deep_research_response = self.client.responses.create(**request_params)
            
            # Handle background mode polling if enabled
            if self.config['background_mode']:
                print(f"  ⏳ Deep research running in background (ID: {deep_research_response.id})")
                
                # Poll until completion
                while deep_research_response.status in {"queued", "in_progress"}:
                    print(f"      Status: {deep_research_response.status}")
                    time.sleep(5)  # Wait 5 seconds between polls
                    deep_research_response = self.client.responses.retrieve(deep_research_response.id)
                
                print(f"      Final status: {deep_research_response.status}")
                
                # Check if completed successfully
                if deep_research_response.status != "completed":
                    raise Exception(f"Deep research failed with status: {deep_research_response.status}")
            
            # Extract content and sources
            deep_research_content = ""
            sources = []
            tool_calls_made = 0
            
            for item in deep_research_response.output:
                if item.type == "message":
                    # Look for output_text content according to OpenAI docs
                    for content_item in item.content:
                        if content_item.type == "output_text":
                            deep_research_content = content_item.text
                            # Extract sources/citations if available
                            if hasattr(content_item, 'annotations'):
                                for annotation in content_item.annotations:
                                    sources.append({
                                        "url": annotation.url,
                                        "title": getattr(annotation, 'title', 'No title'),
                                        "start_index": annotation.start_index,
                                        "end_index": annotation.end_index
                                    })
                            break
                elif item.type == "web_search_call":
                    tool_calls_made += 1
                elif item.type == "code_interpreter_call":
                    tool_calls_made += 1
            
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