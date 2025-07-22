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
        Research the project "{project_name}" comprehensively. Known info from NEAR catalog:
        - Tagline: {tagline}
        - Tags: {tags}
        - Phase: {phase}
        
        Please provide detailed information about:
        1. Official website, documentation, and repositories
        2. Technical architecture and core technology stack
        3. Current development status and recent updates
        4. Team background, advisors, and funding history
        5. Integration capabilities, APIs, and developer tools
        6. Community size, adoption metrics, and partnerships
        7. Business model and tokenomics (if applicable)
        8. Competitive landscape and positioning
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