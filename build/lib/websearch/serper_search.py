# src/websearch/serper_search.py
# Serper web search provider implementation for the RAG Agent Kit application.

import requests
from src.websearch.base import WebSearchProvider
from src.core.settings import settings

# Serper web search provider class
class SerperSearch(WebSearchProvider):
    
    # Perform a web search using Serper API
    def search(self, query: str) -> list[str]:
        if not settings.web_search_enabled:
            return []
        if settings.web_search_provider.strip().lower() != "serper":
            return []
        if not settings.web_search_api_key:
            return ["[serper] missing WEB_SEARCH_API_KEY"]

        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": settings.web_search_api_key,
            "Content-Type": "application/json"
        }
        payload = {"q": query}

        # Send POST request to Serper API and process the response
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=8)
            r.raise_for_status()
            data = r.json()

            out = []
            for item in (data.get("organic") or [])[:3]:
                title = item.get("title", "")
                link = item.get("link", "")
                snippet = item.get("snippet", "")
                out.append(f"{title} | {link} | {snippet}".strip())
            return out or ["[serper] no results"]
        except Exception as e:
            return [f"[serper] error: {type(e).__name__}"]
