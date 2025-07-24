"""
Web Search Module for Local Models
Provides DDGS-based web search functionality compatible with LiteLLM function calling
"""

import json
import logging
from typing import List, Dict, Any, Optional
from ddgs import DDGS

# Configure logging
logger = logging.getLogger(__name__)

def web_search(query: str, max_results: int = 10, region: str = "us-en", timelimit: str = "m") -> str:
    """
    Perform web search using DDGS (DuckDuckGo Search)
    
    Parameters
    ----------
    query : str
        Search query string
    max_results : int
        Maximum number of search results to return (default: 10)
    region : str
        Search region (default: "us-en")
    timelimit : str
        Time limit for search results: "d" (day), "w" (week), "m" (month), "y" (year)
        
    Returns
    -------
    str
        JSON string containing search results formatted for LLM consumption
    """
    try:
        # Initialize DDGS
        ddgs = DDGS()
        
        # Perform text search
        search_results = list(ddgs.text(
            query,
            region=region,
            max_results=max_results,
            timelimit=timelimit
        ))
        
        # Format results for LLM consumption
        formatted_results = []
        for idx, result in enumerate(search_results, 1):
            formatted_result = {
                "rank": idx,
                "title": result.get("title", ""),
                "snippet": result.get("body", ""),
                "url": result.get("href", ""),
                "source": result.get("hostname", "")
            }
            formatted_results.append(formatted_result)
        
        # Create summary for LLM
        search_summary = {
            "query": query,
            "total_results": len(formatted_results),
            "search_region": region,
            "time_limit": timelimit,
            "results": formatted_results
        }
        
        # Return as JSON string for function calling
        return json.dumps(search_summary, indent=2)
        
    except Exception as e:
        logger.error(f"Web search failed for query '{query}': {e}")
        
        # Return error information
        error_response = {
            "query": query,
            "error": f"Search failed: {str(e)}",
            "total_results": 0,
            "results": []
        }
        return json.dumps(error_response, indent=2)

def web_search_news(query: str, max_results: int = 5, region: str = "us-en", timelimit: str = "w") -> str:
    """
    Perform news search using DDGS
    
    Parameters
    ----------
    query : str
        Search query string
    max_results : int
        Maximum number of news results to return (default: 5)
    region : str
        Search region (default: "us-en")
    timelimit : str
        Time limit for news results: "d" (day), "w" (week), "m" (month)
        
    Returns
    -------
    str
        JSON string containing news search results
    """
    try:
        # Initialize DDGS
        ddgs = DDGS()
        
        # Perform news search
        news_results = list(ddgs.news(
            query,
            region=region,
            max_results=max_results,
            timelimit=timelimit
        ))
        
        # Format news results
        formatted_news = []
        for idx, result in enumerate(news_results, 1):
            formatted_result = {
                "rank": idx,
                "title": result.get("title", ""),
                "snippet": result.get("body", ""),
                "url": result.get("url", ""),
                "source": result.get("source", ""),
                "date": result.get("date", "")
            }
            formatted_news.append(formatted_result)
        
        # Create summary
        news_summary = {
            "query": query,
            "total_results": len(formatted_news),
            "search_type": "news",
            "search_region": region,
            "time_limit": timelimit,
            "results": formatted_news
        }
        
        return json.dumps(news_summary, indent=2)
        
    except Exception as e:
        logger.error(f"News search failed for query '{query}': {e}")
        
        error_response = {
            "query": query,
            "error": f"News search failed: {str(e)}",
            "total_results": 0,
            "results": []
        }
        return json.dumps(error_response, indent=2)

# LiteLLM Function Definitions for Function Calling
WEB_SEARCH_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information about projects, partnerships, blockchain technology, and developer resources. Use this when you need current information not available in your training data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query. Be specific and include relevant keywords like project names, blockchain terms, partnership info, etc."
                    },
                    "max_results": {
                        "type": "integer", 
                        "description": "Maximum number of search results to return (1-20)",
                        "minimum": 1,
                        "maximum": 20,
                        "default": 10
                    },
                    "timelimit": {
                        "type": "string",
                        "enum": ["d", "w", "m", "y"],
                        "description": "Time limit for results: 'd' (past day), 'w' (past week), 'm' (past month), 'y' (past year)",
                        "default": "m"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "web_search_news",
            "description": "Search for recent news about blockchain projects, partnerships, hackathons, or technology developments. Use for time-sensitive information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "News search query focused on recent developments, announcements, or events"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of news results (1-10)",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5
                    },
                    "timelimit": {
                        "type": "string", 
                        "enum": ["d", "w", "m"],
                        "description": "Time limit for news: 'd' (past day), 'w' (past week), 'm' (past month)",
                        "default": "w"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# Function execution mapping for LiteLLM
AVAILABLE_FUNCTIONS = {
    "web_search": web_search,
    "web_search_news": web_search_news
} 