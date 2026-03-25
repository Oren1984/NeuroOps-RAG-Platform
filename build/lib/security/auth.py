# src/security/auth.py
# Module to handle API key authentication for the RAG Agent Kit application.

from fastapi import Header, HTTPException
from src.core.settings import settings

# Dependency to require valid API key
def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    if not settings.rag_api_key or settings.rag_api_key.strip() == "":
        # Fail-fast: service should not run without a key
        raise HTTPException(status_code=500, detail="RAG_API_KEY is not configured")

    # Validate the provided API key
    if x_api_key != settings.rag_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
