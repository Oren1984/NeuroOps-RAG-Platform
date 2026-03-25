# src/vectorstores/memory_store.py
# In-memory vector store for the NeuroOps Agent Platform.
#
# ┌─────────────────────────────────────────────────────────────────┐
# │  DEV / TESTING ONLY — NOT FOR PRODUCTION USE                    │
# │                                                                  │
# │  search() returns documents in insertion order.                  │
# │  There is NO semantic similarity, NO vector math, NO ranking.   │
# │  Documents closest to the query are NOT guaranteed to appear.   │
# │                                                                  │
# │  For real semantic search use VECTORSTORE=pgvector.             │
# └─────────────────────────────────────────────────────────────────┘

from src.vectorstores.base import VectorStore


class MemoryVectorStore(VectorStore):
    """In-memory document store for development and unit testing.

    Stores documents in a plain dict. ``search()`` returns the first *k*
    documents in insertion order — it does NOT perform semantic similarity
    search of any kind.  Use PGVectorStore for any deployment where
    retrieval quality matters.
    """

    def __init__(self) -> None:
        self._docs: dict[str, str] = {}

    def upsert(self, doc_id: str, text: str) -> None:
        self._docs[doc_id] = text

    def search(self, query: str, k: int = 3) -> list[str]:
        # Returns documents in insertion order — query is intentionally
        # ignored because this store has no vector/similarity capability.
        return list(self._docs.values())[:k]
