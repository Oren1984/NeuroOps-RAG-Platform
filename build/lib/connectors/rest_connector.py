# src/connectors/rest_connector.py
# REST connector implementation for the RAG Agent Kit application.

from src.connectors.base import AppConnector
from src.core.settings import settings

# REST connector class to fetch context from a RESTful API
class RestConnector(AppConnector):
    def fetch_context(self, question: str) -> str:
        # Placeholder: later you'll call the app API (settings.app_base_url)
        return f"Context from REST app at {settings.app_base_url} (stub)"
