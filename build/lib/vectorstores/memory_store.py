# src/vectorstores/memory_store.py
# In-memory vector store implementation for the RAG Agent Kit application.

from src.vectorstores.base import VectorStore

# In-memory vector store class
class MemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._docs: dict[str, str] = {}

    # Upsert document into the store
    def upsert(self, doc_id: str, text: str) -> None:
        self._docs[doc_id] = text

    # Search for similar documents
    def search(self, query: str, k: int = 3) -> list[str]:
        # naive: return up to k docs
        return list(self._docs.values())[:k]
