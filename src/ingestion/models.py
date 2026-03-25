# src/ingestion/models.py
# Pydantic models for the document ingestion pipeline.

from __future__ import annotations

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """Payload for POST /ingest.

    Fields:
        text:     Raw document text to chunk, embed, and store.
                  Must be between 1 and 100,000 characters.
        source:   Human-readable name identifying the document origin
                  (e.g. a file name, URL, or logical label).
                  Used as a prefix in the internal chunk ID so that
                  re-ingesting the same source replaces existing chunks.
                  Defaults to "unknown".
        doc_type: Arbitrary label describing the document type
                  (e.g. "text", "markdown", "faq").  Not interpreted by
                  the pipeline; returned in the response for traceability.
                  Defaults to "text".
    """

    text: str = Field(..., min_length=1, max_length=100_000)
    source: str = Field(default="unknown", max_length=255)
    doc_type: str = Field(default="text", max_length=64)


class IngestResult(BaseModel):
    """Response body for POST /ingest.

    Fields:
        source:         Echo of the supplied source label.
        doc_type:       Echo of the supplied doc_type.
        chunks_created: Number of text chunks produced and upserted into
                        the vector store.
        total_chars:    Total character length of the input text.
        vectorstore:    Name of the active vector store backend
                        ("memory" or "pgvector").
        warning:        Optional advisory message, e.g. when the active
                        vector store does not persist data across restarts.
    """

    source: str
    doc_type: str
    chunks_created: int
    total_chars: int
    vectorstore: str
    warning: str | None = None
