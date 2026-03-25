# src/websearch/tavily_search.py
# Tavily web search provider for the NeuroOps Agent Platform.
#
# Uses the Tavily Search API (https://tavily.com).
# Requires WEB_SEARCH_PROVIDER=tavily and WEB_SEARCH_API_KEY=tvly-...
# in .env (or environment).

import requests

from src.core.logging import get_logger
from src.core.settings import settings
from src.websearch.base import WebSearchProvider

logger = get_logger(__name__)

_TAVILY_URL = "https://api.tavily.com/search"


class TavilySearch(WebSearchProvider):
    def search(self, query: str) -> list[str]:
        if not settings.web_search_enabled:
            return []

        if not settings.web_search_api_key:
            return ["[tavily] missing WEB_SEARCH_API_KEY"]

        payload = {
            "api_key": settings.web_search_api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": 3,
        }

        try:
            r = requests.post(_TAVILY_URL, json=payload, timeout=8)
            r.raise_for_status()
            data = r.json()

            out = []
            for item in (data.get("results") or [])[:3]:
                title = item.get("title", "")
                url = item.get("url", "")
                content = item.get("content", "")
                out.append(f"{title} | {url} | {content}".strip())

            return out or ["[tavily] no results"]

        except Exception as e:
            logger.warning(
                "tavily search error",
                extra={"error": type(e).__name__, "query_len": len(query)},
            )
            return [f"[tavily] error: {type(e).__name__}"]
