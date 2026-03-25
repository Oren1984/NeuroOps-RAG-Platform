# src/websearch/tavily_search.py
# Tavily web search provider implementation for the RAG Agent Kit application.

from src.websearch.base import WebSearchProvider
from src.core.settings import settings

# Tavily web search provider class
class TavilySearch(WebSearchProvider):
    def search(self, query: str) -> list[str]:
        if not settings.web_search_enabled:
            return []

        # STUB  intentionally no real HTTP calls yet
        return [f"[tavily-stub] result for: {query}"]
