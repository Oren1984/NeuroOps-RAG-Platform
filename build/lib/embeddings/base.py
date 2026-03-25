# src/embeddings/base.py
# Base embeddings class for the RAG Agent Kit application.

from abc import ABC, abstractmethod

# Abstract base class for embeddings
class Embeddings(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError
