# src/providers/base.py
# Base LLM provider class for the RAG Agent Kit application.

from abc import ABC, abstractmethod

# Abstract base class for LLM providers
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError
