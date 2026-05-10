import os
import logging
import httpx
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# PDF Download MCP configuration
MCP_URL = os.getenv("PDF_DOWNLOAD_MCP_URL", "https://pdfmcp.googleapis.com/mcp/v1")
MCP_TOKEN = os.getenv("PDF_DOWNLOAD_MCP_TOKEN")

def check_connection() -> bool:
    """
    Checks if the PDF Download MCP server is reachable and authenticated.
    """
    if not MCP_TOKEN:
        return False
    
    try:
        headers = {"Authorization": f"Bearer {MCP_TOKEN}"}
        response = httpx.get(f"{MCP_URL}/status", headers=headers, timeout=5.0)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"PDF MCP Connection Check Failed: {str(e)}")
        return False

def save_to_pdf(topic: str, content: str) -> str:
    """
    Saves research content to PDF via MCP server.
    """
    if not MCP_TOKEN:
        return "PDF MCP unavailable"

    import re
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_topic = re.sub(r'[^\w\s]', '', topic)
    filename = f"Research_{clean_topic.replace(' ', '_')}_{timestamp}.pdf"
    
    try:
        headers = {
            "Authorization": f"Bearer {MCP_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "filename": filename,
            "content": content,
            "format": "pdf"
        }
        
        response = httpx.post(f"{MCP_URL}/export", headers=headers, json=data, timeout=10.0)
        
        if response.status_code in (200, 201):
            file_info = response.json()
            return file_info.get("downloadLink", "PDF export successful via MCP")
        else:
            return f"PDF Sync failed: {response.status_code}"
            
    except Exception as e:
        logger.error(f"PDF MCP Export Error: {str(e)}")
        return "PDF export unavailable"
