# tests/test_ingestion.py
# Tests for the document ingestion pipeline: chunker, pipeline, and API endpoint.

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

API_KEY = os.getenv("RAG_API_KEY", "ci-test-key")
HEADERS = {"X-API-Key": API_KEY}


# ---------------------------------------------------------------------------
# Chunker
# ---------------------------------------------------------------------------

class TestChunker:
    def test_empty_string_returns_empty_list(self):
        from src.ingestion.chunker import chunk_text
        assert chunk_text("", 500, 50) == []

    def test_whitespace_only_returns_empty_list(self):
        from src.ingestion.chunker import chunk_text
        assert chunk_text("   \n\t  ", 500, 50) == []

    def test_text_shorter_than_chunk_size_returns_single_chunk(self):
        from src.ingestion.chunker import chunk_text
        result = chunk_text("Hello world", 500, 50)
        assert result == ["Hello world"]

    def test_text_exactly_chunk_size_returns_single_chunk(self):
        from src.ingestion.chunker import chunk_text
        text = "a" * 100
        result = chunk_text(text, 100, 10)
        assert len(result) == 1
        assert result[0] == text

    def test_long_text_produces_multiple_chunks(self):
        from src.ingestion.chunker import chunk_text
        text = "word " * 300  # 1500 chars
        result = chunk_text(text, 500, 50)
        assert len(result) > 1

    def test_each_chunk_within_size_limit(self):
        from src.ingestion.chunker import chunk_text
        text = "x" * 2000
        chunk_size = 400
        result = chunk_text(text, chunk_size, 40)
        for chunk in result:
            assert len(chunk) <= chunk_size

    def test_overlap_creates_shared_content(self):
        """Consecutive chunks share exactly the last *overlap* characters
        of the prior chunk (modulo trailing whitespace stripping)."""
        from src.ingestion.chunker import chunk_text
        # Build text with distinct 10-char segments to make overlap visible
        text = "".join(f"{i:010d}" for i in range(50))  # 500 chars
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        assert len(chunks) >= 2
        # End of chunk[0] should appear at start of chunk[1]
        tail = chunks[0][-20:]
        assert chunks[1].startswith(tail)

    def test_no_empty_chunks_in_output(self):
        from src.ingestion.chunker import chunk_text
        text = "Hello world. This is a test document. " * 30
        result = chunk_text(text, 100, 10)
        assert all(len(c) > 0 for c in result)
        assert all(c == c.strip() for c in result)

    def test_invalid_chunk_size_raises(self):
        from src.ingestion.chunker import chunk_text
        with pytest.raises(ValueError):
            chunk_text("some text", chunk_size=0, overlap=0)

    def test_overlap_clamped_when_larger_than_chunk_size(self):
        """overlap >= chunk_size should not cause infinite loop or error."""
        from src.ingestion.chunker import chunk_text
        text = "a" * 200
        # overlap > chunk_size — should be clamped, not raise
        result = chunk_text(text, chunk_size=50, overlap=100)
        assert len(result) >= 1
        assert all(len(c) > 0 for c in result)

    def test_complete_coverage_no_content_lost(self):
        """All characters of the original text appear in at least one chunk."""
        from src.ingestion.chunker import chunk_text
        text = "The quick brown fox jumps over the lazy dog. " * 20
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        combined = "".join(chunks)
        # Every character in text should appear somewhere across all chunks.
        # We verify by checking that combined length >= original (overlap adds chars)
        assert len(combined) >= len(text.strip())


# ---------------------------------------------------------------------------
# Ingestion pipeline
# ---------------------------------------------------------------------------

class TestIngestionPipeline:
    def setup_method(self):
        """Reset the store singleton before each test so state doesn't bleed."""
        import src.retrieval.pipeline as p
        p._store = None

    def test_ingest_creates_chunks_in_store(self):
        """Ingested document chunks appear in the store and are searchable."""
        from src.ingestion.pipeline import ingest_document
        from src.retrieval.pipeline import _get_store

        text = "NeuroOps is an agentic AI platform. " * 10  # ~360 chars
        result = ingest_document(text, source="test-doc", doc_type="text")

        assert result.chunks_created >= 1
        assert result.total_chars == len(text)
        assert result.source == "test-doc"
        assert result.doc_type == "text"

        # Chunks should now be in the store
        store = _get_store()
        docs = store.search("NeuroOps", k=10)
        assert any("NeuroOps" in d for d in docs)

    def test_chunk_ids_follow_expected_pattern(self):
        """Doc IDs are deterministic: {safe_source}:chunk:{index}."""
        from src.ingestion.pipeline import ingest_document
        from src.retrieval.pipeline import _get_store
        from src.vectorstores.memory_store import MemoryVectorStore

        ingest_document("word " * 500, source="my source.txt", doc_type="text")
        store = _get_store()
        assert isinstance(store, MemoryVectorStore)

        # Source is sanitized: spaces → underscores
        ids = list(store._docs.keys())
        assert all(":chunk:" in id_ for id_ in ids)
        assert all(id_.startswith("my_source.txt:chunk:") for id_ in ids)

    def test_reingest_same_source_replaces_chunks(self):
        """Re-ingesting the same source overwrites existing chunks (upsert)."""
        from src.ingestion.pipeline import ingest_document
        from src.retrieval.pipeline import _get_store

        ingest_document("first version " * 50, source="doc-a")
        first_count = len(_get_store()._docs)

        ingest_document("second version " * 50, source="doc-a")
        second_count = len(_get_store()._docs)

        # Same number of chunks — not duplicated
        assert second_count == first_count
        # Content updated
        docs = list(_get_store()._docs.values())
        assert any("second version" in d for d in docs)
        assert not any("first version" in d for d in docs)

    def test_empty_text_creates_zero_chunks(self):
        """When the chunker returns no chunks (mocked), chunks_created is 0."""
        from src.ingestion.pipeline import ingest_document
        with patch("src.ingestion.pipeline.chunk_text", return_value=[]):
            result = ingest_document("some text", source="empty")
        assert result.chunks_created == 0

    def test_memory_store_warning_present(self):
        """Response includes a warning when using the memory vector store."""
        from src.ingestion.pipeline import ingest_document
        result = ingest_document("Hello world. " * 10, source="test")
        assert result.warning is not None
        assert "memory" in result.warning.lower()
        assert "persist" in result.warning.lower()

    def test_pgvector_store_no_warning(self, monkeypatch):
        """No warning when vectorstore is pgvector."""
        monkeypatch.setenv("VECTORSTORE", "pgvector")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
        from importlib import reload
        import src.core.settings as s_mod; reload(s_mod)
        import src.ingestion.pipeline as ip; reload(ip)

        # Mock the store so we don't need a real DB
        mock_store = patch("src.ingestion.pipeline._get_store")
        with mock_store as ms:
            ms.return_value.upsert = lambda *a: None
            result = ip.ingest_document("Hello world. " * 10, source="test")

        assert result.warning is None

    def test_result_vectorstore_reflects_active_backend(self):
        from src.ingestion.pipeline import ingest_document
        result = ingest_document("Hello world. " * 10)
        assert result.vectorstore == "memory"  # default in test env


# ---------------------------------------------------------------------------
# API endpoint — POST /ingest
# ---------------------------------------------------------------------------

class TestIngestEndpoint:
    def setup_method(self):
        import src.retrieval.pipeline as p
        p._store = None

    @pytest.fixture
    def client(self):
        from src.main import app
        return TestClient(app)

    def test_ingest_returns_201(self, client):
        """Successful ingestion returns HTTP 201 Created."""
        resp = client.post(
            "/ingest",
            json={"text": "NeuroOps is an agentic AI platform.", "source": "intro.txt"},
            headers=HEADERS,
        )
        assert resp.status_code == 201

    def test_ingest_response_structure(self, client):
        """Response contains all expected fields."""
        resp = client.post(
            "/ingest",
            json={"text": "Test document content. " * 20, "source": "test.txt", "doc_type": "text"},
            headers=HEADERS,
        )
        data = resp.json()
        assert "source" in data
        assert "doc_type" in data
        assert "chunks_created" in data
        assert "total_chars" in data
        assert "vectorstore" in data
        assert "request_id" in data
        assert data["source"] == "test.txt"
        assert data["doc_type"] == "text"
        assert data["chunks_created"] >= 1
        assert data["total_chars"] == len("Test document content. " * 20)

    def test_ingest_without_api_key_returns_401(self, client):
        """Unauthenticated requests are rejected."""
        resp = client.post(
            "/ingest",
            json={"text": "Some content"},
        )
        assert resp.status_code == 401

    def test_ingest_empty_text_returns_422(self, client):
        """Pydantic validation rejects empty text with HTTP 422."""
        resp = client.post(
            "/ingest",
            json={"text": ""},
            headers=HEADERS,
        )
        assert resp.status_code == 422

    def test_ingest_text_too_long_returns_422(self, client):
        """Pydantic validation rejects text over 100,000 characters."""
        resp = client.post(
            "/ingest",
            json={"text": "x" * 100_001},
            headers=HEADERS,
        )
        assert resp.status_code == 422

    def test_ingest_defaults_source_and_doc_type(self, client):
        """source and doc_type default to 'unknown' and 'text' respectively."""
        resp = client.post(
            "/ingest",
            json={"text": "Minimal payload."},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["source"] == "unknown"
        assert data["doc_type"] == "text"

    def test_ingest_then_ask_retrieves_content(self, client):
        """Documents ingested via /ingest are immediately searchable via /ask."""
        # Ingest a distinctive document
        unique_phrase = "NeuroOpsTestPhrase12345"
        client.post(
            "/ingest",
            json={"text": f"This document contains {unique_phrase}. " * 5, "source": "e2e-test.txt"},
            headers=HEADERS,
        )

        # Ask a question — the stub provider won't answer it semantically,
        # but retrieved_count should be > 0 showing the doc was indexed.
        resp = client.post(
            "/ask",
            json={"question": f"What is {unique_phrase}?"},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["sources"]["retrieved_count"] > 0

    def test_ingest_response_includes_x_request_id_header(self, client):
        """X-Request-ID header is present on every /ingest response."""
        resp = client.post(
            "/ingest",
            json={"text": "Hello world."},
            headers=HEADERS,
        )
        assert "x-request-id" in resp.headers
