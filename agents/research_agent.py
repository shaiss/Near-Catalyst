# agents/research_agent.py
"""
Research Agent for NEAR Catalyst Framework

This agent conducts comprehensive research on potential hackathon partners to discover
collaborators that can unlock developer potential and create "1 + 1 = 3" value propositions.
"""

import json
from config.config import TIMEOUTS
from agents.litellm_router import completion


class ResearchAgent:
    """
    Agent 1: Research agent that gathers comprehensive information about projects
    using LiteLLM Router with automatic local model routing and fallbacks.
    """
    
    def __init__(self, client=None, db_manager=None, usage_tracker=None):
        """Initialize the research agent."""
        self.timeout = TIMEOUTS['research_agent']
        self.db_manager = db_manager
        
    def analyze(self, project_name, context):
        """
        Conduct comprehensive research on a project to assess hackathon catalyst potential.
        
        Args:
            project_name: Name of the project to research
            context: Additional context from NEAR catalog
            
        Returns:
            Dict with research results, sources, and cost information
        """
        
        # Truncate context to manageable size
        if len(context) > 2000:
            context = context[:2000] + "... [truncated]"
        
        prompt = f"""You are an expert research analyst focused on discovering hackathon catalyst partners for NEAR Protocol. Your mission is to identify collaborators that can unlock developer potential and create "1 + 1 = 3" value propositions.

RESEARCH TARGET: {project_name}

CONTEXT FROM NEAR CATALOG:
{context}

RESEARCH MISSION:
Conduct comprehensive analysis to determine if this project could be a valuable hackathon catalyst partner for NEAR Protocol. Focus on discovering collaborative opportunities that unlock developer potential during hackathons.

Your research should cover:

1. **Core Technology & Capabilities**
   - What unique technical capabilities does this project offer?
   - How could these capabilities complement NEAR's blockchain infrastructure?
   - What gaps in NEAR's developer stack could this fill?

2. **Hackathon Collaboration Potential**
   - How could developers combine NEAR + this project during hackathons?
   - What novel use cases become possible with both technologies together?
   - Are there existing integrations or would new ones need to be built?

3. **Developer Experience & Integration**
   - How developer-friendly is this project's tooling and documentation?
   - What's the learning curve for developers new to this technology?
   - Are there SDKs, APIs, or other developer tools available?

4. **Community & Ecosystem Alignment**
   - Who is the target developer audience for this project?
   - Is there overlap with NEAR's developer community?
   - Does this project actively participate in hackathons?

5. **Partnership History & Support**
   - Has this project collaborated with other blockchain protocols?
   - Do they provide mentorship, bounties, or technical support for hackathons?
   - What level of partnership engagement might be realistic?

Provide comprehensive, factual analysis based on available information. Be specific about capabilities, integration potential, and collaboration opportunities. If information is limited, note what additional research would be valuable.

Focus on discovering whether this could unlock new possibilities for NEAR developers during hackathons."""

        try:
            print(f"      🔍 Researching {project_name} with LiteLLM Router...")
            
            # Use LiteLLM Router for automatic local model routing and fallbacks
            response = completion(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000,
                timeout=self.timeout
            )
            
            content = response.choices[0].message.content
            cost = 0.0
            
            # Extract cost and routing information from Router
            if hasattr(response, '_hidden_params'):
                cost = response._hidden_params.get('response_cost', 0.0)
                cost_source = response._hidden_params.get('cost_source', 'openai')
                local_used = response._hidden_params.get('local_model_used', False)
                router_tags = response._hidden_params.get('router_tags', [])
                
                if local_used:
                    print(f"      🆓 Using local model ({', '.join(router_tags)}) - Cost: Free")
                else:
                    print(f"      💰 Using OpenAI model ({', '.join(router_tags)}) - Cost: ${cost:.4f}")
            
            return {
                "success": True,
                "content": content,
                "sources": ["comprehensive_analysis"],
                "cost": cost
            }
            
        except Exception as e:
            error_msg = f"Research agent error: {str(e)}"
            print(f"❌ {error_msg}")
            
            return {
                "success": False,
                "content": "",
                "sources": [],
                "error": error_msg,
                "cost": 0.0
            } 