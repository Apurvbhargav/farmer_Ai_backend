import logging
import time

from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.2
)


def ask_llm(prompt: str, max_retries: int = 3) -> str:
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not configured")
        return ""

    for attempt in range(max_retries):
        try:
            response = llm.invoke(prompt)

            if response and response.content:
                return response.content

            logger.warning("LLM returned empty response")
            return ""

        except Exception as e:
            logger.error(
                f"LLM error through LangChain "
                f"(attempt {attempt + 1}/{max_retries}): {e}"
            )

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying after {wait_time}s...")
                time.sleep(wait_time)
                continue

            return ""

    return ""