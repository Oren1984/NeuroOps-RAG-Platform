# src/ingestion/pipeline.py
# Document ingestion pipeline for the NeuroOps Agent Platform.
#
# Flow:
#   text  →  chunker.chunk_text()  →  [chunk_0, chunk_1, ...]
#                                          ↓
#                              store.upsert(doc_id, chunk)  (per chunk)
#                                          ↓
#                                    IngestResult
#
# The pipeline reuses the same vector-store singleton as the retrieval
# pipeline (_get_store from retrieval.pipeline), so documents ingested
# via POST /ingest are immediately searchable via POST /ask in the same
# process — no restart required.
#
# Chunk ID format:  "{safe_source}:chunk:{index}"
#   - Deterministic: re-ingesting the same source replaces existing chunks.
#   - safe_source is the source label with non-alphanumeric chars replaced
#     by underscores, truncated to 64 characters.

from __future__ import annotations

import re

from src.core.logging import get_logger
from src.core.settings import settings
from src.ingestion.chunker import chunk_text
from src.ingestion.models import IngestResult

logger = get_logger(__name__)

_MEMORY_WARNING = (
    "VECTORSTORE=memory: ingested documents are stored in process memory only "
    "and will be lost when the server restarts. Set VECTORSTORE=pgvector for "
    "persistent storage."
)


def _safe_source(source: str) -> str:
    """Sanitize source label for use inside a chunk doc_id."""
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", source.strip())
    return (sanitized or "unknown")[:64]


def ingest_document(
    text: str,
    source: str = "unknown",
    doc_type: str = "text",
) -> IngestResult:
    """Chunk *text* and upsert all chunks into the active vector store.

    Args:
        text:     Raw document content.
        source:   Origin label (file name, URL, logical ID).
        doc_type: Arbitrary document-type label (not interpreted by pipeline).

    Returns:
        ``IngestResult`` summarising what was stored.
    """
    # Import here to avoid circular imports at module load time.
    # retrieval.pipeline owns the store singleton; ingestion reuses it.
    from src.retrieval.pipeline import _get_store

    chunks = chunk_text(text, settings.ingest_chunk_size, settings.ingest_chunk_overlap)

    logger.info(
        "ingest",
        extra={
            "source": source,
            "doc_type": doc_type,
            "total_chars": len(text),
            "chunks": len(chunks),
            "vectorstore": settings.vectorstore,
        },
    )

    if chunks:
        safe = _safe_source(source)
        store = _get_store()
        for i, chunk in enumerate(chunks):
            doc_id = f"{safe}:chunk:{i}"
            store.upsert(doc_id, chunk)

    return IngestResult(
        source=source,
        doc_type=doc_type,
        chunks_created=len(chunks),
        total_chars=len(text),
        vectorstore=settings.vectorstore,
        warning=_MEMORY_WARNING if settings.vectorstore.lower() == "memory" else None,
    )
