# agents/research_agent.py
"""
Research Agent for NEAR Partnership Analysis

Agent 1: Gathers comprehensive information about projects using web search.
Provides foundational research that other agents build upon.
"""

from .config import TIMEOUTS


class ResearchAgent:
    """
    Agent 1: Research agent that gathers comprehensive information about projects
    using OpenAI's web search capabilities.
    """
    
    def __init__(self, client):
        """Initialize the research agent with OpenAI client."""
        self.client = client
        self.timeout = TIMEOUTS['research_agent']
    
    def analyze(self, project_name, project_data):
        """
        Conduct comprehensive research about a project.
        
        Args:
            project_name (str): Name of the project
            project_data (dict): Basic project data from NEAR catalog
            
        Returns:
            dict: Research results with content, sources, and success status
        """
        profile = project_data.get('profile', {})
        tagline = profile.get('tagline', 'No tagline available')
        tags = ', '.join(profile.get('tags', {}).values())
        phase = profile.get('phase', 'Unknown')
        
        research_prompt = f"""
        Research the project "{project_name}" for NEAR Protocol partnership evaluation using the "1+1=3" framework.
        
        Known info from NEAR catalog:
        - Tagline: {tagline}
        - Tags: {tags}
        - Phase: {phase}
        
        Focus your research on partnership potential as a force multiplier for NEAR developers:
        
        **A. Synergistic Technology Assessment:**
        1. Official website, documentation, APIs, and core technology offering
        2. Does this fill a strategic gap in NEAR's stack or overlap with NEAR's core blockchain functionality?
        3. Integration capabilities - APIs, SDKs, developer tools, and documentation quality
        4. Previous blockchain integrations or Web3 partnership examples
        
        **B. Aligned Developer Ecosystem Analysis:**
        5. Target developer audience - do they serve the same developers as NEAR?
        6. Developer workflow positioning - different function or competing role?
        7. Community size, developer adoption metrics, and support quality
        8. Technical support responsiveness and commitment to developer success
        
        **C. Clear and Immediate Value for Builders:**
        9. Integration complexity - can developers wire the stacks together in hours?
        10. Hackathon readiness - plug-and-play integration vs complex setup
        11. Partnership support history - mentors, bounties, hands-on hackathon participation
        12. Potential for "Better Together" narrative that's clear without diagrams
        
        **Red Flag Detection:**
        - Direct product overlap with NEAR's blockchain functionality
        - Either/or choice scenarios for developers
        - "Logo on a slide" partnerships with no technical substance
        - Conflicting technical standards or integration friction
        
        Evaluate specifically: Does this create exponential value (1+1=3) when combined with NEAR Protocol for hackathon developers?
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
                if item.type == "message" and item.role == "assistant":
                    research_content = item.content[0].text
                    # Extract sources/citations if available
                    if hasattr(item.content[0], 'annotations'):
                        for annotation in item.content[0].annotations:
                            if annotation.type == "url_citation":
                                sources.append({
                                    "url": annotation.url,
                                    "title": getattr(annotation, 'title', 'No title'),
                                    "start_index": annotation.start_index,
                                    "end_index": annotation.end_index
                                })
                    break
                    
            return {
                "content": research_content,
                "sources": sources,
                "success": True
            }
            
        except Exception as e:
            print(f"  WARNING: General research failed: {e}")
            return {
                "content": f"Basic info - {project_name}: {tagline}. Tags: {tags}. Phase: {phase}",
                "sources": [],
                "success": False,
                "error": str(e)
            } 