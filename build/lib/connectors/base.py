# src/connectors/base.py
# Base connector class for the RAG Agent Kit application.

from abc import ABC, abstractmethod

# Abstract base class for application connectors
class AppConnector(ABC):
    @abstractmethod
    def fetch_context(self, question: str) -> str:
        raise NotImplementedError
