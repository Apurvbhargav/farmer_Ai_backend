from google import genai

from google.genai.errors import ClientError

from app.config import GEMINI_API_KEY

import logging

logger = logging.getLogger(__name__)

client = genai.Client(
    api_key=GEMINI_API_KEY
)


def ask_llm(prompt: str):

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        if response.text:
            return response.text
        else:
            logger.warning("LLM returned empty response")
            return ""

    except ClientError as e:

        logger.error(f"ClientError from LLM: {e}")
        return ""
    
    except Exception as e:
        
        logger.error(f"Unexpected error in ask_llm: {e}")
        return ""