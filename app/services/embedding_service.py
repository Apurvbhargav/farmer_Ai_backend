from google import genai
import logging

from app.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

client = genai.Client(
    api_key=GEMINI_API_KEY
)

def generate_embedding(text: str):
    
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set in environment variables")
        raise ValueError("GEMINI_API_KEY is not configured")

    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text
        )

        return response.embeddings[0].values
    
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise