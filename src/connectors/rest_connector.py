# src/connectors/rest_connector.py
# REST connector for the NeuroOps Agent Platform.
#
# Fetches external context from a running application's REST endpoint.
# Configure via CONNECTOR=rest, APP_BASE_URL, and REST_CONTEXT_PATH in .env.
#
# Request format:  GET {APP_BASE_URL}{REST_CONTEXT_PATH}?q={question}
# Expected response: plain text or JSON string used as RAG context.
#
# If the target URL is unreachable, returns an empty string — the RAG
# pipeline continues without external app context rather than failing.

from urllib.parse import urlencode

import requests

from src.connectors.base import AppConnector
from src.core.logging import get_logger
from src.core.settings import settings

logger = get_logger(__name__)


class RestConnector(AppConnector):
    def fetch_context(self, question: str) -> str:
        base = (settings.app_base_url or "").rstrip("/")
        if not base:
            return ""

        path = (settings.rest_context_path or "/context").lstrip("/")
        url = f"{base}/{path}?{urlencode({'q': question})}"

        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            # Truncate to avoid flooding the LLM prompt
            return r.text[:4000]

        except requests.exceptions.ConnectionError:
            logger.warning(
                "rest connector unreachable",
                extra={"url": url},
            )
            return ""
        except requests.exceptions.Timeout:
            logger.warning(
                "rest connector timeout",
                extra={"url": url},
            )
            return ""
        except Exception as e:
            logger.warning(
                "rest connector error",
                extra={"url": url, "error": type(e).__name__},
            )
            return ""
