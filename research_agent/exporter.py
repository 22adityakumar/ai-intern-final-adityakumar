import logging
from fpdf import FPDF
from datetime import datetime

logger = logging.getLogger(__name__)

def export_txt(topic: str, summary: str) -> bytes:
    """
    Exports the research summary as a TXT byte stream.
    
    Args:
        topic (str): The research topic.
        summary (str): The research summary text.
        
    Returns:
        bytes: The TXT content in bytes.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"RESEARCH TOPIC: {topic}\n"
        content += f"GENERATED AT: {timestamp}\n"
        content += "="*50 + "\n\n"
        content += summary
        return content.encode('utf-8')
    except Exception as e:
        logger.error(f"TXT Export Error: {str(e)}")
        raise RuntimeError("Failed to generate TXT export")

def export_pdf(topic: str, summary: str) -> bytes:
    """
    Exports the research summary as a PDF byte stream using fpdf2.
    """
    def sanitize(text: str) -> str:
        return text.encode('latin-1', 'ignore').decode('latin-1')

    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        epw = pdf.w - 2 * pdf.l_margin
        
        # Title Page
        pdf.set_font("helvetica", 'B', 24)
        pdf.cell(epw, 20, sanitize("Research Summary"), new_x="LMARGIN", new_y="NEXT", align='C')
        
        pdf.set_font("helvetica", 'B', 16)
        pdf.multi_cell(epw, 10, sanitize(f"Topic: {topic}"), align='C')
        
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
                # Prevent orphaned headers
                if pdf.get_y() > 250:
                    pdf.add_page()
                pdf.ln(5)
                pdf.set_font("helvetica", 'B', 14)
                pdf.multi_cell(epw, 10, header_text)
                pdf.set_font("helvetica", '', 11)
                pdf.ln(2)
            elif line.startswith('* '):
                # Bullet point
                bullet_text = line.replace('* ', '').replace('**', '').strip()
                pdf.set_font("helvetica", '', 11)
                pdf.set_x(pdf.l_margin + 5)
                pdf.multi_cell(epw - 5, 7, f"- {bullet_text}")
                pdf.ln(1)
            else:
                # Regular text
                text = line.replace('**', '').strip()
                pdf.set_font("helvetica", '', 11)
                pdf.multi_cell(epw, 7, text)
                pdf.ln(1)
                
        # Footer
        pdf.set_y(-15)
        pdf.set_font("helvetica", 'I', 8)
        pdf.cell(epw, 10, sanitize(f'Page {pdf.page_no()}'), align='C')
        
        return bytes(pdf.output())
    except Exception as e:
        logger.error(f"PDF Export Error: {str(e)}")
        raise RuntimeError(f"Failed to generate PDF export: {str(e)}")
