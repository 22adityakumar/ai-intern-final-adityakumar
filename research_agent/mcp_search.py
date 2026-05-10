import os
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Search MCP configuration
MCP_URL = os.getenv("SEARCH_MCP_URL", "http://127.0.0.1:9000")
MCP_TOKEN = os.getenv("SEARCH_MCP_TOKEN")

def check_connection() -> bool:
    """
    Checks if the Search MCP server is reachable and authenticated.
    """
    if not MCP_TOKEN:
        return False
    
    try:
        headers = {"Authorization": f"Bearer {MCP_TOKEN}"}
        response = httpx.get(f"{MCP_URL}/status", headers=headers, timeout=5.0)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Search MCP Connection Check Failed: {str(e)}")
        return False

def web_search(query: str) -> list:
    """
    Performs a web search via the MCP server.
    """
    if not MCP_TOKEN:
        logger.warning("Search MCP unavailable: Missing token")
        return []

    try:
        headers = {
            "Authorization": f"Bearer {MCP_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {"query": query}
        
        response = httpx.post(f"{MCP_URL}/search", headers=headers, json=data, timeout=10.0)
        
        if response.status_code == 200:
            return response.json().get("results", [])
        else:
            logger.error(f"Search MCP failed: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Search MCP Error: {str(e)}")
        return []
