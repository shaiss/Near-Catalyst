# agents/research_agent.py
"""
Research Agent for NEAR Catalyst Framework

This agent conducts comprehensive research on potential hackathon partners to discover
collaborators that can unlock developer potential and create "1 + 1 = 3" value propositions.
"""

import json
from config.config import TIMEOUTS
from database.usage_tracker import APIUsageTracker
from database.database_manager import DatabaseManager


class ResearchAgent:
    """
    Agent 1: Research agent that gathers comprehensive information about projects
    using LiteLLM's web search capabilities with cost tracking.
    """
    
    def __init__(self, client=None, db_manager=None, usage_tracker=None):
        """Initialize the research agent with usage tracking."""
        self.timeout = TIMEOUTS['research_agent']
        
        # Initialize usage tracking
        self.db_manager = db_manager or DatabaseManager()
        self.usage_tracker = usage_tracker or APIUsageTracker(None, self.db_manager)
    
    def analyze(self, project_name, enriched_context):
        """
        Conduct comprehensive research about a project using enriched context from NEAR catalog.
        
        Args:
            project_name (str): Name of the project
            enriched_context (dict): Full project context including NEAR catalog data
            
        Returns:
            dict: Research results with content, sources, and success status
        """
        # Set context for usage tracking
        self.usage_tracker.set_context(project_name, "research_agent")
        
        # Extract data from enriched context
        basic_profile = enriched_context.get('basic_profile', {})
        catalog_data = enriched_context.get('catalog_data', {})
        
        # Build comprehensive context string for research prompt
        context_parts = []
        
        # Basic profile data
        if basic_profile.get('tagline'):
            context_parts.append(f"Tagline: {basic_profile['tagline']}")
        if basic_profile.get('tags'):
            tags = ', '.join(basic_profile['tags'].values()) if isinstance(basic_profile['tags'], dict) else str(basic_profile['tags'])
            context_parts.append(f"Tags: {tags}")
        if basic_profile.get('description'):
            context_parts.append(f"Description: {basic_profile['description']}")
        
        # NEAR catalog data
        if catalog_data:
            if catalog_data.get('description'):
                context_parts.append(f"Catalog Description: {catalog_data['description']}")
            if catalog_data.get('category'):
                context_parts.append(f"Category: {catalog_data['category']}")
            if catalog_data.get('stage'):
                context_parts.append(f"Development Stage: {catalog_data['stage']}")
            if catalog_data.get('tech_stack'):
                context_parts.append(f"Tech Stack: {catalog_data['tech_stack']}")
            if catalog_data.get('website'):
                context_parts.append(f"Website: {catalog_data['website']}")
            if catalog_data.get('github'):
                context_parts.append(f"GitHub: {catalog_data['github']}")
        
        context_string = "\n".join(context_parts) if context_parts else f"Limited information available about {project_name}"
        
        # Build comprehensive research prompt
        research_prompt = f"""
As a NEAR Protocol Partnership Scout, conduct comprehensive research on "{project_name}" to evaluate its potential as a hackathon catalyst partner.

Known Information:
{context_string}

Your goal is to discover if this project can enable "1 + 1 = 3" value propositions for NEAR hackathon developers. 

Focus your research on:
1. **Technology Complementarity**: How does this technology fill gaps or enhance NEAR's capabilities?
2. **Developer Experience**: What tools, SDKs, or resources do they provide for developers?
3. **Hackathon Readiness**: Can this be integrated quickly during a 48-72 hour hackathon?
4. **Community & Support**: What kind of developer support and mentorship do they offer?
5. **Past Collaborations**: Any history of successful hackathon partnerships or developer programs?
6. **Innovation Potential**: What new use cases or proof-points could this enable for NEAR?

Research using web search to find documentation, developer guides, GitHub repositories, 
blog posts, and other official sources wherever possible.

Since I already have some project details from NEAR catalog, use web search to find additional 
technical details, developer resources, community engagement, and hackathon participation history 
that would help evaluate this as a NEAR catalyst partner.
"""
        
        try:
            # Use LiteLLM through usage tracker for cost tracking
            research_response = self.usage_tracker.track_chat_completions_create(
                model="gpt-4.1",
                operation_type="research",
                messages=[{"role": "user", "content": research_prompt}],
                timeout=self.timeout
            )
            
            # Extract response content (LiteLLM returns OpenAI-compatible format)
            research_content = research_response.choices[0].message.content
            sources = []  # Web search sources will be handled in future phases
                    
            return {
                "content": research_content,
                "sources": sources,
                "success": True
            }
            
        except Exception as e:
            print(f"      ❌ Research failed: {str(e)}")
            return {
                "content": f"Research failed: {str(e)}",
                "sources": [],
                "success": False,
                "error": str(e)
            } 