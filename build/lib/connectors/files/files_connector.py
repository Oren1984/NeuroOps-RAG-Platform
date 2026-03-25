# src/connectors/files_connector.py
# Files connector implementation for the RAG Agent Kit application.

from pathlib import Path
from src.connectors.base import AppConnector

# Files connector class to fetch context from local text files
class FilesConnector(AppConnector):
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)

    # Fetch context by reading text files from the specified directory
    def fetch_context(self, question: str) -> str:
        if not self.base_path.exists():
            return "No files directory found."

        # Read text files and compile their contents
        texts = []
        for p in self.base_path.glob("**/*.txt"):
            try:
                texts.append(p.read_text(encoding="utf-8")[:2000])
            except Exception:
                continue
        
        # Limit to first 3 files for context
        if not texts:
            return "No readable files found."

        return "\n---\n".join(texts[:3])
