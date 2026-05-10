import io
import logging
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional

from agent import generate_research
import mcp_txt
import mcp_pdf
import mcp_search
from exporter import export_txt, export_pdf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Research Agent API")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class ResearchRequest(BaseModel):
    topic: str

class ResearchResponse(BaseModel):
    topic: str
    summary: str
    timestamp: str
    word_count: int
    mcp_status: dict  # Changed from str to dict to support multiple MCPs

class ExportRequest(BaseModel):
    topic: str
    summary: str

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse("static/index.html")

@app.get("/api/mcp/status")
async def get_mcp_status():
    return {
        "txt": mcp_txt.check_connection(),
        "pdf": mcp_pdf.check_connection(),
        "search": mcp_search.check_connection()
    }

@app.post("/api/research", response_model=ResearchResponse)
async def conduct_research(request: ResearchRequest):
    try:
        # 1. Perform Web Search via MCP
        search_results = mcp_search.web_search(request.topic)
        search_context = ""
        if search_results:
            search_context = "\n".join([f"- {r['title']}: {r['snippet']} ({r['url']})" for r in search_results])
            logger.info(f"Found {len(search_results)} search results via MCP")

        # 2. Generate research using Gemini with search context
        result = generate_research(request.topic, search_context)
        
        # 3. Attempt to save to multiple MCPs
        mcp_status = {
            "txt": mcp_txt.save_to_txt(result["topic"], result["summary"]),
            "pdf": mcp_pdf.save_to_pdf(result["topic"], result["summary"]),
            "search": "Search completed" if search_results else "No results found"
        }
        
        return {
            **result,
            "mcp_status": mcp_status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unhandled Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/export/txt")
async def download_txt(request: ExportRequest):
    try:
        content = export_txt(request.topic, request.summary)
        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=Research_{request.topic.replace(' ', '_')}.txt"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/pdf")
async def download_pdf(request: ExportRequest):
    try:
        content = export_pdf(request.topic, request.summary)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Research_{request.topic.replace(' ', '_')}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
