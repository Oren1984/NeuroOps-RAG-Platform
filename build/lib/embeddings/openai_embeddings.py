# src/embeddings/openai_embeddings.py
# OpenAI embeddings implementation for the RAG Agent Kit application.

import requests
from src.core.settings import settings
from src.embeddings.base import Embeddings

# OpenAI embeddings class to generate text embeddings using OpenAI API
class OpenAIEmbeddings(Embeddings):
    def embed(self, text: str) -> list[float]:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for embeddings when using pgvector")

        # Call OpenAI API to get embeddings
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.openai_embed_model,
            "input": text[:8000],
        }
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data["data"][0]["embedding"]
