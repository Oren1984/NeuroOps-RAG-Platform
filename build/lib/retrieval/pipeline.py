# src/retrieval/pipeline.py
# Retrieval pipeline for the RAG Agent Kit application.

from src.core.settings import settings

# Import LLM providers
from src.providers.openai_provider import OpenAIProvider
from src.providers.gemini_provider import GeminiProvider
from src.providers.anthropic_provider import AnthropicProvider

# Import connectors
from src.connectors.rest_connector import RestConnector
from src.connectors.files.files_connector import FilesConnector

# Import vector stores
from src.vectorstores.memory_store import MemoryVectorStore
from src.vectorstores.pgvector_store import PGVectorStore

# Import web search providers
from src.websearch.tavily_search import TavilySearch
from src.websearch.serper_search import SerperSearch

_store = None

# Factory methods to get components based on settings
def _get_provider():
    p = settings.llm_provider.lower().strip()
    if p == "gemini":
        return GeminiProvider()
    if p == "anthropic":
        return AnthropicProvider()
    return OpenAIProvider()

# Factory methods to get components based on settings
def _get_connector():
    c = settings.connector.lower().strip()
    if c == "files":
        return FilesConnector(settings.files_base_path)
    return RestConnector()

# Factory methods to get components based on settings
def _get_web_search():
    p = settings.web_search_provider.lower().strip()
    if p == "serper":
        return SerperSearch()
    return TavilySearch()

# Factory methods to get components based on settings
def _get_store():
    global _store
    if _store is not None:
        return _store

    # Vector store selection
    vs = settings.vectorstore.lower().strip()
    if vs == "pgvector":
        # Fail-fast requirement: embeddings need OPENAI_API_KEY
        if not settings.openai_api_key:
            raise RuntimeError("VECTORSTORE=pgvector requires OPENAI_API_KEY for embeddings")
        _store = PGVectorStore()
    else:
        _store = MemoryVectorStore()

    # bootstrap
    _store.upsert("boot", "This is a default knowledge snippet (boot).")
    return _store

# Main pipeline function to answer a question
def answer_question(question: str) -> dict:
    connector = _get_connector()
    provider = _get_provider()
    web = _get_web_search()
    store = _get_store()

    # Fetch context, retrieve from vector store, and web search
    app_ctx = connector.fetch_context(question)
    retrieved = store.search(question, k=3)
    web_results = web.search(question) if settings.web_search_enabled else []

    # Construct prompt for LLM
    prompt = (
        "You are a RAG agent. Answer using the provided context.\n\n"
        f"APP_CONTEXT:\n{app_ctx}\n\n"
        f"RETRIEVED:\n- " + "\n- ".join(retrieved) + "\n\n"
        + (f"WEB_RESULTS:\n- " + "\n- ".join(web_results) + "\n\n" if web_results else "")
        + f"QUESTION:\n{question}\n"
    )

    answer = provider.generate(prompt)

    return {
        "answer": answer,
        "provider": settings.llm_provider,
        "connector": settings.connector,
        "vectorstore": settings.vectorstore,
        "web_search_enabled": settings.web_search_enabled,
        "sources": {
            "app_context": app_ctx,
            "retrieved_count": len(retrieved),
            "web_results_count": len(web_results),
        },
    }
