# src/websearch/base.py
# Base class for web search providers in the RAG Agent Kit application.

from abc import ABC, abstractmethod

# Abstract base class for web search providers
class WebSearchProvider(ABC):
    @abstractmethod
    def search(self, query: str) -> list[str]:
        raise NotImplementedError
