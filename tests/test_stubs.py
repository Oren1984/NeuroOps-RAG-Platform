# tests/test_stubs.py
# Tests for previously-stubbed components: Tavily, REST connector, MemoryVectorStore.

import os
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Tavily search
# ---------------------------------------------------------------------------

class TestTavilySearch:
    def test_disabled_returns_empty(self, monkeypatch):
        """Returns [] when web search is disabled, regardless of API key."""
        monkeypatch.setenv("WEB_SEARCH_ENABLED", "false")
        monkeypatch.setenv("WEB_SEARCH_API_KEY", "tvly-test")
        # Re-import after env change so Settings re-reads
        from importlib import reload
        import src.core.settings as s_mod
        reload(s_mod)
        import src.websearch.tavily_search as t_mod
        reload(t_mod)

        result = t_mod.TavilySearch().search("test query")
        assert result == []

    def test_missing_api_key_returns_error_string(self, monkeypatch):
        """Returns a descriptive error string when API key is absent."""
        monkeypatch.setenv("WEB_SEARCH_ENABLED", "true")
        monkeypatch.setenv("WEB_SEARCH_API_KEY", "")
        from importlib import reload
        import src.core.settings as s_mod
        reload(s_mod)
        import src.websearch.tavily_search as t_mod
        reload(t_mod)

        result = t_mod.TavilySearch().search("test query")
        assert len(result) == 1
        assert "missing WEB_SEARCH_API_KEY" in result[0]

    def test_api_returns_results(self, monkeypatch):
        """Parses Tavily API response and returns formatted strings."""
        monkeypatch.setenv("WEB_SEARCH_ENABLED", "true")
        monkeypatch.setenv("WEB_SEARCH_API_KEY", "tvly-fake-key")
        from importlib import reload
        import src.core.settings as s_mod
        reload(s_mod)
        import src.websearch.tavily_search as t_mod
        reload(t_mod)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"title": "Result A", "url": "https://a.com", "content": "Content A"},
                {"title": "Result B", "url": "https://b.com", "content": "Content B"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("src.websearch.tavily_search.requests.post", return_value=mock_response):
            result = t_mod.TavilySearch().search("what is RAG?")

        assert len(result) == 2
        assert "Result A" in result[0]
        assert "https://a.com" in result[0]
        assert "Content A" in result[0]

    def test_api_error_returns_error_string(self, monkeypatch):
        """Returns a graceful error string on HTTP failure — does not raise."""
        monkeypatch.setenv("WEB_SEARCH_ENABLED", "true")
        monkeypatch.setenv("WEB_SEARCH_API_KEY", "tvly-fake-key")
        from importlib import reload
        import src.core.settings as s_mod
        reload(s_mod)
        import src.websearch.tavily_search as t_mod
        reload(t_mod)

        with patch("src.websearch.tavily_search.requests.post", side_effect=Exception("boom")):
            result = t_mod.TavilySearch().search("test")

        assert len(result) == 1
        assert "[tavily] error" in result[0]

    def test_empty_results_returns_no_results_string(self, monkeypatch):
        """Returns ['[tavily] no results'] when API returns empty list."""
        monkeypatch.setenv("WEB_SEARCH_ENABLED", "true")
        monkeypatch.setenv("WEB_SEARCH_API_KEY", "tvly-fake-key")
        from importlib import reload
        import src.core.settings as s_mod
        reload(s_mod)
        import src.websearch.tavily_search as t_mod
        reload(t_mod)

        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        with patch("src.websearch.tavily_search.requests.post", return_value=mock_response):
            result = t_mod.TavilySearch().search("obscure query")

        assert result == ["[tavily] no results"]


# ---------------------------------------------------------------------------
# REST connector
# ---------------------------------------------------------------------------

class TestRestConnector:
    def test_empty_base_url_returns_empty_string(self, monkeypatch):
        """Returns '' immediately when APP_BASE_URL is not configured."""
        monkeypatch.setenv("APP_BASE_URL", "")
        from importlib import reload
        import src.core.settings as s_mod
        reload(s_mod)
        import src.connectors.rest_connector as rc_mod
        reload(rc_mod)

        result = rc_mod.RestConnector().fetch_context("hello")
        assert result == ""

    def test_connection_error_returns_empty_string(self, monkeypatch):
        """Returns '' on ConnectionError — pipeline continues without context."""
        monkeypatch.setenv("APP_BASE_URL", "http://localhost:9999")
        from importlib import reload
        import src.core.settings as s_mod
        reload(s_mod)
        import src.connectors.rest_connector as rc_mod
        reload(rc_mod)

        import requests as req_lib
        with patch(
            "src.connectors.rest_connector.requests.get",
            side_effect=req_lib.exceptions.ConnectionError,
        ):
            result = rc_mod.RestConnector().fetch_context("test question")

        assert result == ""

    def test_timeout_returns_empty_string(self, monkeypatch):
        """Returns '' on request timeout."""
        monkeypatch.setenv("APP_BASE_URL", "http://localhost:9999")
        from importlib import reload
        import src.core.settings as s_mod
        reload(s_mod)
        import src.connectors.rest_connector as rc_mod
        reload(rc_mod)

        import requests as req_lib
        with patch(
            "src.connectors.rest_connector.requests.get",
            side_effect=req_lib.exceptions.Timeout,
        ):
            result = rc_mod.RestConnector().fetch_context("test question")

        assert result == ""

    def test_success_returns_response_text(self, monkeypatch):
        """Returns response text on a successful 200 response."""
        monkeypatch.setenv("APP_BASE_URL", "http://myapp:5000")
        monkeypatch.setenv("REST_CONTEXT_PATH", "/context")
        from importlib import reload
        import src.core.settings as s_mod
        reload(s_mod)
        import src.connectors.rest_connector as rc_mod
        reload(rc_mod)

        mock_response = MagicMock()
        mock_response.text = "This is the app context for your question."
        mock_response.raise_for_status = MagicMock()

        with patch("src.connectors.rest_connector.requests.get", return_value=mock_response) as mock_get:
            result = rc_mod.RestConnector().fetch_context("what is NeuroOps?")

        assert result == "This is the app context for your question."
        called_url = mock_get.call_args[0][0]
        assert "http://myapp:5000/context" in called_url
        assert "q=" in called_url

    def test_response_truncated_to_4000_chars(self, monkeypatch):
        """Truncates very long responses to prevent LLM prompt flooding."""
        monkeypatch.setenv("APP_BASE_URL", "http://myapp:5000")
        from importlib import reload
        import src.core.settings as s_mod
        reload(s_mod)
        import src.connectors.rest_connector as rc_mod
        reload(rc_mod)

        mock_response = MagicMock()
        mock_response.text = "x" * 10_000
        mock_response.raise_for_status = MagicMock()

        with patch("src.connectors.rest_connector.requests.get", return_value=mock_response):
            result = rc_mod.RestConnector().fetch_context("test")

        assert len(result) == 4000


# ---------------------------------------------------------------------------
# MemoryVectorStore
# ---------------------------------------------------------------------------

class TestMemoryVectorStore:
    def test_upsert_and_search_returns_docs(self):
        """Inserted documents are returned by search."""
        from src.vectorstores.memory_store import MemoryVectorStore
        store = MemoryVectorStore()
        store.upsert("doc1", "The sky is blue.")
        store.upsert("doc2", "RAG stands for Retrieval-Augmented Generation.")

        results = store.search("sky", k=5)
        assert "The sky is blue." in results
        assert "RAG stands for Retrieval-Augmented Generation." in results

    def test_search_respects_k_limit(self):
        """search() returns at most k documents."""
        from src.vectorstores.memory_store import MemoryVectorStore
        store = MemoryVectorStore()
        for i in range(10):
            store.upsert(f"doc{i}", f"Document number {i}")

        results = store.search("anything", k=3)
        assert len(results) == 3

    def test_search_returns_insertion_order_not_semantic(self):
        """Documents are returned in insertion order — no semantic ranking.

        This test documents the known limitation of MemoryVectorStore:
        the query has no effect on which documents are returned.
        """
        from src.vectorstores.memory_store import MemoryVectorStore
        store = MemoryVectorStore()
        store.upsert("first", "Completely unrelated content about astronomy.")
        store.upsert("second", "This is about Python programming.")

        # Both queries return the same order regardless of relevance
        results_a = store.search("astronomy", k=2)
        results_b = store.search("Python", k=2)
        assert results_a == results_b  # order is insertion-based, not query-based

    def test_upsert_overwrites_existing_doc_id(self):
        """Upserting with the same doc_id replaces the existing document."""
        from src.vectorstores.memory_store import MemoryVectorStore
        store = MemoryVectorStore()
        store.upsert("doc1", "original text")
        store.upsert("doc1", "updated text")

        results = store.search("anything", k=5)
        assert "updated text" in results
        assert "original text" not in results

    def test_empty_store_returns_empty_list(self):
        """search() on an empty store returns []."""
        from src.vectorstores.memory_store import MemoryVectorStore
        store = MemoryVectorStore()
        assert store.search("anything") == []


# ---------------------------------------------------------------------------
# Pipeline — boot document removed
# ---------------------------------------------------------------------------

class TestPipelineBootDoc:
    def test_fresh_memory_store_has_no_boot_doc(self):
        """The pipeline no longer seeds a 'boot' document into the store.

        A fresh MemoryVectorStore should start empty so boot-doc text
        never appears in retrieval results.
        """
        from src.vectorstores.memory_store import MemoryVectorStore
        store = MemoryVectorStore()
        results = store.search("boot", k=5)
        assert results == []
        assert not any("default knowledge snippet" in r for r in results)
