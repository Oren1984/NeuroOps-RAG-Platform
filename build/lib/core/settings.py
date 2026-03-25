# src/core/settings.py
# Application settings for the RAG Agent Kit application.

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Application settings class
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default="rag-agent-kit")
    app_env: str = Field(default="dev")
    log_level: str = Field(default="INFO")

    # Required security
    rag_api_key: str = Field(default="")

    # Providers
    llm_provider: str = Field(default="openai")

    openai_api_key: str = Field(default="")
    openai_chat_model: str = Field(default="gpt-4o-mini")
    openai_embed_model: str = Field(default="text-embedding-3-small")

    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-1.5-flash")

    anthropic_api_key: str = Field(default="")
    anthropic_model: str = Field(default="claude-3-5-sonnet-latest")

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_per_minute: int = Field(default=60)

    # CORS
    cors_enabled: bool = Field(default=False)
    cors_origins: str = Field(default="")

    # Web search
    web_search_enabled: bool = Field(default=False)
    web_search_provider: str = Field(default="serper")
    web_search_api_key: str = Field(default="")

    # Connector
    connector: str = Field(default="rest")
    app_base_url: str = Field(default="http://localhost:5000")
    files_base_path: str = Field(default="data")

    # Vector store
    vectorstore: str = Field(default="memory")  # memory|pgvector
    pg_dsn: str = Field(default="postgresql://rag:rag@db:5432/rag")  # Use 'db' for Docker networks
    pg_collection: str = Field(default="rag_docs")

settings = Settings()
