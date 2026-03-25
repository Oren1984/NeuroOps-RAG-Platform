# src/vectorstores/pgvector_store.py
# PostgreSQL vector store implementation for the RAG Agent Kit application.

import re
import psycopg
from pgvector.psycopg import register_vector
from src.vectorstores.base import VectorStore
from src.core.settings import settings
from src.embeddings.openai_embeddings import OpenAIEmbeddings

# Sanitize table name to be a safe Postgres identifier
def _safe_table(name: str) -> str:
    # allow only letters, numbers, underscore. must start with letter/underscore.
    name = name.strip()
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    if not re.match(r"^[a-zA-Z_]", name):
        name = "_" + name
    return name[:63]  # postgres identifier max (safe)

# DDL for creating the vector table
DDL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS {table_name} (
  id TEXT PRIMARY KEY,
  content TEXT NOT NULL,
  embedding VECTOR(1536) NOT NULL
);

CREATE INDEX IF NOT EXISTS {table_name}_embedding_idx
ON {table_name} USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
"""

# PostgreSQL vector store class
class PGVectorStore(VectorStore):
    def __init__(self):
        self._dsn = settings.pg_dsn
        self._table = _safe_table(settings.pg_collection)
        self._emb = OpenAIEmbeddings()

        # Ensure table exists
        with psycopg.connect(self._dsn) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute(DDL.format(table_name=self._table))
            conn.commit()

    # Upsert document into the store
    def upsert(self, doc_id: str, text: str) -> None:
        # Upsert document into the store
        vec = self._emb.embed(text)
        with psycopg.connect(self._dsn) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self._table} (id, content, embedding)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                      content = EXCLUDED.content,
                      embedding = EXCLUDED.embedding
                    """,
                    (doc_id, text, vec),
                )
            conn.commit()

    # Search for similar documents
    def search(self, query: str, k: int = 3) -> list[str]:
        qvec = self._emb.embed(query)
        with psycopg.connect(self._dsn) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT content
                    FROM {self._table}
                    ORDER BY embedding <=> %s
                    LIMIT %s
                    """,
                    (qvec, k),
                )
                rows = cur.fetchall()
        return [r[0] for r in rows]
