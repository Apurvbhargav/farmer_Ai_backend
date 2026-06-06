from google import genai

from app.config import GEMINI_API_KEY

client = genai.Client(
    api_key=GEMINI_API_KEY
)

def generate_embedding(text: str):

    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )

    #print(response)

    return response.embeddings[0].values