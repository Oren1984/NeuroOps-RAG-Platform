# src/vectorstores/base.py
# Base class for vector store implementations in the RAG Agent Kit application.

from abc import ABC, abstractmethod

# Base vector store class
class VectorStore(ABC):
    @abstractmethod
    def upsert(self, doc_id: str, text: str) -> None:
        raise NotImplementedError

    # Search for similar documents
    @abstractmethod
    def search(self, query: str, k: int = 3) -> list[str]:
        raise NotImplementedError
