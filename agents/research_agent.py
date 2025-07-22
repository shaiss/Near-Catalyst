# agents/research_agent.py
"""
Research Agent for NEAR Catalyst Framework

This agent conducts comprehensive research on potential hackathon partners to discover
collaborators that can unlock developer potential and create "1 + 1 = 3" value propositions.
"""

import json
from config.config import TIMEOUTS


class ResearchAgent:
    """
    Agent 1: Research agent that gathers comprehensive information about projects
    using OpenAI's web search capabilities.
    """
    
    def __init__(self, client):
        """Initialize the research agent with OpenAI client."""
        self.client = client
        self.timeout = TIMEOUTS['research_agent']
    
    def analyze(self, project_name, enriched_context):
        """
        Conduct comprehensive research about a project using enriched context from NEAR catalog.
        
        Args:
            project_name (str): Name of the project
            enriched_context (dict): Full project context including NEAR catalog data
            
        Returns:
            dict: Research results with content, sources, and success status
        """
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
        if basic_profile.get('phase'):
            context_parts.append(f"Phase: {basic_profile['phase']}")
        
        # Rich catalog data
        if catalog_data:
            if catalog_data.get('description'):
                context_parts.append(f"Description: {catalog_data['description']}")
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
            if catalog_data.get('blockchain_networks'):
                context_parts.append(f"Blockchain Networks: {catalog_data['blockchain_networks']}")
            if catalog_data.get('team_size'):
                context_parts.append(f"Team Size: {catalog_data['team_size']}")
            if catalog_data.get('founded'):
                context_parts.append(f"Founded: {catalog_data['founded']}")
        
        known_context = '\n'.join(context_parts) if context_parts else "Limited project information available"
        
        research_prompt = f"""
Research the project "{project_name}" for NEAR Catalyst Framework evaluation using the "1+1=3" discovery methodology.

KNOWN PROJECT INFORMATION FROM NEAR CATALOG:
{known_context}

Your research should focus on identifying hackathon co-creation partners that can unlock developer potential 
and create exponential value during NEAR hackathons and developer events.

Key Research Areas:
1. Core technology and unique capabilities that complement NEAR's strengths
2. Developer tools, SDKs, and integration resources for hackathon participants
3. Target developer audience and technical complexity for rapid prototyping
4. Previous blockchain integrations or Web3 hackathon participation examples
5. Technical integration patterns with blockchain/Web3 (APIs, SDKs, libraries)
6. Ease of developer onboarding and learning curve for hackathon timeframes
7. Documentation quality and availability of tutorials/sample code
8. Community engagement with developers (Discord, forums, GitHub activity)
9. Track record of supporting developer events, hackathons, or educational initiatives
10. Alignment with NEAR's target audience (Web3 developers, dApp builders)
11. Hackathon support history - mentors, bounties, hands-on participation

Focus your research on hackathon catalyst potential as a force multiplier for NEAR developers:
- Can this technology unlock new use cases when combined with NEAR?
- Does it fill capability gaps that NEAR developers commonly face?
- Is there clear documentation and tooling for hackathon-speed integration?
- What is the learning curve for developers new to this technology?

RED FLAGS to identify and report:
- Complex enterprise-only solutions that don't fit hackathon timeframes
- Poor developer experience or lack of self-service onboarding
- "Logo on a slide" partnerships with no technical substance
- Technologies that compete directly with NEAR's core capabilities
- Lack of developer-facing resources or community engagement

Focus on factual, verifiable information. Provide links to documentation, GitHub repos, 
blog posts, and other official sources wherever possible.

Since I already have some project details from NEAR catalog, use web search to find additional 
technical details, developer resources, community engagement, and hackathon participation history 
that would help evaluate this as a NEAR catalyst partner.
"""
        
        try:
            research_response = self.client.responses.create(
                model="gpt-4.1",
                tools=[{
                    "type": "web_search_preview",
                    "search_context_size": "high"
                }],
                input=research_prompt,
                timeout=self.timeout
            )
            
            research_content = ""
            sources = []
            
            for item in research_response.output:
                if item.type == "message":
                    # Look for output_text content according to OpenAI docs
                    for content_item in item.content:
                        if content_item.type == "output_text":
                            research_content = content_item.text
                            # Extract sources/citations if available
                            if hasattr(content_item, 'annotations'):
                                for annotation in content_item.annotations:
                                    if annotation.type == "url_citation":
                                        sources.append({
                                            "url": annotation.url,
                                            "title": getattr(annotation, 'title', 'No title'),
                                            "start_index": annotation.start_index,
                                            "end_index": annotation.end_index
                                        })
                            break
                    break
                    
            return {
                "content": research_content,
                "sources": sources,
                "success": True
            }
            
        except Exception as e:
            print(f"  WARNING: General research failed: {e}")
            
            # Create fallback content with available information
            fallback_parts = [f"Basic info - {project_name}"]
            if basic_profile.get('tagline'):
                fallback_parts.append(f"Tagline: {basic_profile['tagline']}")
            if basic_profile.get('tags'):
                tags = ', '.join(basic_profile['tags'].values()) if isinstance(basic_profile['tags'], dict) else str(basic_profile['tags'])
                fallback_parts.append(f"Tags: {tags}")
            if basic_profile.get('phase'):
                fallback_parts.append(f"Phase: {basic_profile['phase']}")
            
            fallback_content = '. '.join(fallback_parts)
            
            return {
                "content": fallback_content,
                "sources": [],
                "success": False,
                "error": str(e)
            } 