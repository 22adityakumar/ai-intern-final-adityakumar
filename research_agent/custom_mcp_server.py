from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fpdf import FPDF
from datetime import datetime
from ddgs import DDGS
import os

app = FastAPI(title="Custom MCP Server")

# Create a directory to store the files we receive
DOWNLOADS_DIR = "mcp_downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Serve the downloads directory so files can be accessed via URL
app.mount("/download", StaticFiles(directory=DOWNLOADS_DIR), name="download")

# This is your secret token!
MY_SECRET_TOKEN = "my-super-secret-123"

class ExportRequest(BaseModel):
    filename: str
    content: str
    format: str

def generate_pdf_from_text(topic: str, summary: str) -> bytes:
    def sanitize(text: str) -> str:
        return text.encode('latin-1', 'ignore').decode('latin-1')
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    epw = pdf.w - 2 * pdf.l_margin
    
    # Clean up topic (remove timestamp part if it looks like one)
    import re
    topic = re.sub(r'_\d{8}_\d{6}$', '', topic)
    topic = topic.replace('_', ' ').strip()

    # Title
    pdf.set_font("helvetica", 'B', 24)
    pdf.cell(epw, 20, sanitize("Research Summary (MCP Sync)"), new_x="LMARGIN", new_y="NEXT", align='C')
    
    # Topic
    pdf.set_font("helvetica", 'B', 16)
    pdf.multi_cell(epw, 10, sanitize(f"Topic: {topic}"), align='C')
    
    # Date
    pdf.ln(5)
    pdf.set_font("helvetica", 'I', 10)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.cell(epw, 10, sanitize(f"Generated on: {timestamp}"), new_x="LMARGIN", new_y="NEXT", align='C')
    
    pdf.ln(10)
    
    # Content
    lines = summary.split('\n')
    for line in lines:
        line = sanitize(line).strip()
        
        if not line:
            pdf.ln(2)
            continue
            
        if line.startswith('## '):
            header_text = line.replace('## ', '').replace('**', '').strip()
            # Avoid orphaned headers at the bottom of the page
            if pdf.get_y() > 250:
                pdf.add_page()
            pdf.ln(5)
            pdf.set_font("helvetica", 'B', 14)
            pdf.multi_cell(epw, 10, header_text)
            pdf.set_font("helvetica", '', 11)
            pdf.ln(2)
        elif line.startswith('* '):
            # Bullet point handling
            bullet_text = line.replace('* ', '').replace('**', '').strip()
            pdf.set_font("helvetica", '', 11)
            pdf.set_x(pdf.l_margin + 5)
            pdf.multi_cell(epw - 5, 7, f"- {bullet_text}")
            pdf.ln(1)
        else:
            # Regular text, remove bolding markers
            text = line.replace('**', '').strip()
            pdf.set_font("helvetica", '', 11)
            pdf.multi_cell(epw, 7, text)
            pdf.ln(1)
            
    return bytes(pdf.output())

@app.get("/status")
async def get_status(authorization: str = Header(None)):
    if authorization != f"Bearer {MY_SECRET_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"status": "connected"}

@app.post("/export")
async def export_file(request: ExportRequest, authorization: str = Header(None)):
    if authorization != f"Bearer {MY_SECRET_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    file_path = os.path.join(DOWNLOADS_DIR, request.filename)
    
    if request.format == 'pdf':
        # Extract topic from filename
        topic_raw = request.filename.replace("Research_", "").replace(".pdf", "")
        pdf_bytes = generate_pdf_from_text(topic_raw, request.content)
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
    else:
        # Default to text
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(request.content)
    
    print(f"--- MCP SERVER SAVED {request.format.upper()} FILE ---")
    print(f"Saved to: {file_path}")
    print(f"-----------------------------")
    
    return {
        "status": "success",
        "downloadLink": f"http://127.0.0.1:9000/download/{request.filename}"
    }

class SearchRequest(BaseModel):
    query: str

@app.post("/search")
async def search(request: SearchRequest, authorization: str = Header(None)):
    if authorization != f"Bearer {MY_SECRET_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    print(f"--- MCP SERVER SEARCHING (DDG): {request.query} ---")
    
    try:
        results = []
        with DDGS() as ddgs:
            # Fetch top 5 results
            ddgs_results = ddgs.text(request.query, max_results=5)
            for r in ddgs_results:
                results.append({
                    "title": r.get("title", "No Title"),
                    "snippet": r.get("body", "No Snippet"),
                    "url": r.get("href", "#")
                })
        
        print(f"--- FOUND {len(results)} REAL RESULTS ---")
        return {"results": results}
    except Exception as e:
        print(f"--- DDG SEARCH ERROR: {str(e)} ---")
        return {"results": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9000)
