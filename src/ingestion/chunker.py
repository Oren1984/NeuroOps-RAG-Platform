# src/ingestion/chunker.py
# Text chunking strategies for the NeuroOps Agent Platform.
#
# Phase 1: Fixed-size character chunking with overlap.
# Phase 3 will extend this module with recursive and semantic strategies
# without changing the interface used by the ingestion pipeline.

from __future__ import annotations


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split *text* into overlapping fixed-size character chunks.

    Produces chunks of at most *chunk_size* characters. Each consecutive
    chunk starts *overlap* characters before the end of the previous one,
    preserving context across boundaries.

    Rules:
    - Empty or whitespace-only input returns ``[]``.
    - Text shorter than *chunk_size* returns a single-element list.
    - Each returned chunk is stripped of leading/trailing whitespace.
    - Zero-length chunks (after stripping) are discarded.

    Args:
        text:       Input text to split.
        chunk_size: Maximum characters per chunk (must be > 0).
        overlap:    Characters of overlap between consecutive chunks.
                    Clamped to ``chunk_size - 1`` if larger.

    Returns:
        Ordered list of non-empty text chunks.
    """
    if not text or not text.strip():
        return []

    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be > 0, got {chunk_size}")

    # Clamp overlap so the sliding step is always at least 1 character
    overlap = min(overlap, chunk_size - 1)
    step = chunk_size - overlap

    if len(text) <= chunk_size:
        stripped = text.strip()
        return [stripped] if stripped else []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start += step

    return chunks
