import logging

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=GEMINI_API_KEY
)


def generate_embedding(text: str):
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set in environment variables")
        raise ValueError("GEMINI_API_KEY is not configured")

    if not text or not text.strip():
        logger.error("Cannot generate embedding for empty text")
        raise ValueError("Text cannot be empty")

    try:
        return embeddings.embed_query(text)

    except Exception as e:
        logger.error(f"Error generating embedding through LangChain: {str(e)}")
        raise