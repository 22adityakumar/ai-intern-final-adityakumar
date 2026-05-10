import os
import logging
from datetime import datetime
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not found in environment variables.")

def generate_research(topic: str, search_context: str = "") -> dict:
    """
    Generates a structured research summary using Google Gemini API (gemini-2.5-flash).
    
    Args:
        topic (str): The research topic.
        search_context (str): Optional context from web search.
        
    Returns:
        dict: A dictionary containing topic, summary, timestamp, and word_count.
        
    Raises:
        ValueError: If the topic is invalid.
        RuntimeError: If the API call fails.
    """
    # Validation
    if not topic or not topic.strip():
        raise ValueError("Please enter a research topic")
    
    topic = topic.strip()
    if len(topic) < 3:
        raise ValueError("Topic must be at least 3 characters")
    if len(topic) > 500:
        raise ValueError("Topic must be under 500 characters")

    if not client:
        raise RuntimeError("AI service configuration missing. Please check API keys.")

    try:
        context_prompt = ""
        if search_context:
            context_prompt = f"\n\nHere is some initial research context from web search:\n{search_context}\n\nUse this information to inform your summary while still providing a comprehensive overview."

        prompt = f"""You are an expert research assistant. Generate a comprehensive, well-structured research summary on the topic: {topic}{context_prompt}
  
Format your response with these exact sections:
## Overview
## Key Concepts
## Current Developments
## Applications & Use Cases
## Challenges & Limitations
## Future Outlook
## References & Further Reading

Be thorough, accurate, and cite credible sources where possible."""

        logger.info(f"Generating research for topic: {topic} using gemini-2.5-flash")
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        if not response or not response.text:
            raise RuntimeError("Empty response from AI service.")

        summary = response.text
        word_count = len(summary.split())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return {
            "topic": topic,
            "summary": summary,
            "timestamp": timestamp,
            "word_count": word_count
        }

    except Exception as e:
        logger.error(f"Gemini API Error: {str(e)}")
        if "rate limit" in str(e).lower() or "429" in str(e):
            raise RuntimeError("AI service rate limit exceeded. Please try again later.")
        if "model not found" in str(e).lower() or "404" in str(e):
             raise RuntimeError(f"Model 'gemini-2.5-flash' not found. Ensure it is available for your API key.")
        raise RuntimeError("AI service temporarily unavailable. Please try again.")
