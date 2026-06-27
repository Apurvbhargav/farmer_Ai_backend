from google import genai

from google.genai.errors import ClientError

from app.config import GEMINI_API_KEY

import logging
import time

logger = logging.getLogger(__name__)

client = genai.Client(
    api_key=GEMINI_API_KEY
)


def ask_llm(prompt: str, max_retries: int = 3):

    for attempt in range(max_retries):
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

            logger.error(f"ClientError from LLM (attempt {attempt + 1}/{max_retries}): {e}")
            
            if "UNAVAILABLE" in str(e) and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # exponential backoff: 1s, 2s, 4s
                logger.info(f"Retrying after {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            return ""
        
        except Exception as e:
            
            logger.error(f"Unexpected error in ask_llm (attempt {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying after {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            return ""
    
    return ""