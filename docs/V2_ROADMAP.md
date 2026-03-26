# NeuroOps Agent Platform — V2 Implementation Roadmap

**Date:** 2026-03-26
**Branch:** `main`
**Source of Truth:** `docs/V2_AUDIT_REPORT.md`
**Status:** Phase 1 largely complete — see completed items below

---

## 1. V2 Target Identity

### Final Name

**NeuroOps Agent Platform**

Internal package/CLI name: `neuroops` (replaces `rag-agent-kit` in `pyproject.toml`)

### Defining Sentence

> NeuroOps is a modular, production-ready agentic AI platform that combines a RAG knowledge backbone, persistent memory, a tool execution layer, and multi-step agent orchestration — served through a clean API and an optional chat UI.

### What V2 Is Not
- Not a RAG-only Q&A system (that was V1)
- Not an LLM wrapper
- Not a research prototype — production-oriented from day one

---

## 2. V2 Architecture Map

### Layers to Keep (from V1 — unchanged or lightly modified)

| Layer | Files | Action |
|-------|-------|--------|
| LLM Provider abstraction | `src/providers/` | Keep as-is. Add function-calling method. |
| Security + Auth | `src/security/auth.py` | Keep. Add multi-key support later. |
| Middleware stack | `src/middleware/` | Keep. Upgrade rate limiter to Redis in Phase 4. |
| Configuration system | `src/core/settings.py` | Keep. Expand with new settings fields. |
| pgvector store | `src/vectorstores/pgvector_store.py` | Keep. Upgrade schema in Phase 3. |
| Deployment | `Dockerfile`, `docker-compose.yml` | Keep. Add new services incrementally. |
| Documentation structure | `docs/` | Keep. Add new sections per phase. |

### Layers to Upgrade (existing code, needs rework)

| Layer | Files | Action |
|-------|-------|--------|
| RAG pipeline | `src/retrieval/pipeline.py` | Decompose `answer_question()` into discrete stages |
| API routes | `src/api/routes.py` | Add new endpoints; evolve `/ask` |
| Connectors | `src/connectors/rest_connector.py` | ✅ Real REST connector implemented |
| Web search | `src/websearch/tavily_search.py` | ✅ Real Tavily integration implemented |
| Memory store | `src/vectorstores/memory_store.py` | Either fix or remove (broken search) |
| Logging | `src/core/logging.py` | Implement structured logging (currently empty) |
| Embeddings | `src/embeddings/` | Add multi-model support |
| CI/CD | `.github/workflows_disabled/ci.yml` | Re-enable by moving to `.github/workflows/` |

### New Layers to Add

| Layer | Location | Priority |
|-------|----------|----------|
| **Memory service** | `src/memory/` | Phase 1 |
| **Agent orchestration** | `src/agents/` | Phase 2 |
| **Tool registry + execution** | `src/tools/` | Phase 2 |
| **Ingestion pipeline** | `src/ingestion/` | ✅ Phase 1 — complete |
| **Reranking** | `src/retrieval/reranker.py` | Phase 3 |
| **Chunking strategies** | `src/ingestion/chunking.py` | Phase 1 |
| **Streaming support** | `src/api/streaming.py` | Phase 2 |
| **OTEL instrumentation** | `src/core/telemetry.py` | Phase 4 |
| **Async HTTP clients** | all providers | Phase 4 |
| **Chat UI** | `ui/` | Phase 5 |

### What Remains Optional
- Phoenix observability stack (`observability/`)
- Tavily search (can use Serper exclusively)
- Gemini provider
- pgvector (memory store serves local dev)
- Chat UI

### What Becomes First-Class in V2
- Document ingestion (was entirely missing)
- Conversation history (was entirely missing)
- Memory layer (was entirely missing)
- Agent loop (was entirely missing)
- Structured logging and OTEL tracing

---

## 3. Phase-by-Phase Implementation Roadmap

---

### Phase 1 — Critical Foundations
**Goal:** Make the V1 RAG pipeline production-complete and establish the API contracts V2 depends on.

Nothing in V2 is buildable without these. Phase 1 has no external dependencies.

#### ✅ 1.1 Re-enable CI/CD
- **Status:** Done — `.github/workflows/ci.yml` is active
- **Outcome:** Every commit is automatically tested

#### 1.2 Structured Logging
- **What:** Implement `src/core/logging.py` using Python's stdlib `logging` with JSON formatter. Inject logger into all modules. Add request ID middleware.
- **Files changed:** `src/core/logging.py` (currently empty), `src/middleware/` (new `request_id.py`), `src/main.py`
- **New modules:** `src/middleware/request_id.py`
- **Risk:** Low
- **Outcome:** Every request has a traceable `request_id`. Logs are structured JSON. Debugging becomes possible.

#### ✅ 1.3 Fix / Remove Broken Components
- **Status:** Done
  - `src/vectorstores/memory_store.py` marked as dev-only
  - `src/websearch/tavily_search.py` — real Tavily API integration
  - `src/connectors/rest_connector.py` — real HTTP GET implementation
- **Outcome:** All advertised features work. No silent stubs.

#### 1.4 Provider Hardening
- **What:** Add HTTP timeouts to all provider calls (currently missing — a hung call blocks forever). Add basic retry with exponential backoff (1-2 retries). Add proper error types.
- **Files changed:** `src/providers/openai_provider.py`, `src/providers/anthropic_provider.py`, `src/providers/gemini_provider.py`
- **Risk:** Low
- **Outcome:** The platform doesn't hang indefinitely when an LLM API is slow.

#### ✅ 1.5 Document Ingestion Pipeline
- **Status:** Done — `POST /ingest` endpoint live
- **Files:** `src/ingestion/chunker.py`, `src/ingestion/pipeline.py`, `src/ingestion/models.py`
- **Outcome:** Users can load text documents into the platform via API. Fixed-size chunking + OpenAI embeddings + pgvector upsert.

#### 1.6 Conversation History (Multi-Turn)
- **What:** Add `thread_id` (optional UUID) to `/ask` request. Store message history in PostgreSQL (new `conversations` table). Inject recent turns into the LLM prompt. Return `thread_id` in every response.
- **New files:**
  - `src/memory/__init__.py`
  - `src/memory/conversation.py` — `ConversationStore` (PostgreSQL-backed)
  - `src/memory/models.py` — `Message`, `Thread` Pydantic models
- **Files changed:** `src/api/routes.py`, `src/retrieval/pipeline.py`, `src/core/settings.py`, `db/init.sql`
- **Risk:** Medium — DB schema addition, backward-compatible (thread_id is optional)
- **Outcome:** `/ask` becomes a conversational endpoint. Stateless Q&A → stateful assistant.

#### Phase 1 Test Additions
- `tests/test_ingestion.py` — ingestion pipeline unit tests
- `tests/test_conversation.py` — thread/history unit tests
- `tests/test_providers.py` — timeout and error behavior

**Phase 1 Outcome:** A complete, honest RAG platform with real ingestion, real conversation history, real logging, and no silent stubs. V1 becomes genuinely production-ready. All Phase 2 work can build on this.

---

### Phase 2 — Agent Core
**Goal:** Transform the platform from a conversational RAG API into a tool-using, multi-step agent.

**Dependency:** Phase 1 must be complete (function calling requires working providers; agent loop requires conversation history).

#### 2.1 LLM Function Calling Integration
- **What:** Extend `LLMProvider` base class with a `generate_with_tools(prompt, tools) -> ToolCallResult` method. Implement for OpenAI (`tools` parameter) and Anthropic (`tool_use` parameter). Gemini optional.
- **Files changed:** `src/providers/base.py`, `src/providers/openai_provider.py`, `src/providers/anthropic_provider.py`
- **New files:** `src/providers/models.py` — `ToolCall`, `ToolResult`, `ToolCallResult` Pydantic models
- **Risk:** Medium — interface change to provider base class
- **Outcome:** Providers can now request tool execution from the LLM. This is the unlock for all agent behavior.

#### 2.2 Tool Registry
- **What:** A catalog of callable tools that the agent can invoke. Each tool has a name, description, JSON schema (for LLM), and a Python callable. Register tools at startup.
- **New files:**
  - `src/tools/__init__.py`
  - `src/tools/registry.py` — `ToolRegistry` class, `register_tool()` decorator
  - `src/tools/base.py` — `Tool` abstract base, `ToolResult` model
  - `src/tools/builtin/web_search.py` — wraps `src/websearch/` as a tool
  - `src/tools/builtin/vector_search.py` — wraps `src/vectorstores/` as a tool
  - `src/tools/builtin/file_read.py` — file reading tool
- **Files changed:** `src/main.py` (register tools at startup)
- **Risk:** Low — purely additive
- **Outcome:** The LLM can request specific tools by name. Tool execution is centralized and auditable.

#### 2.3 Agent Loop (ReAct)
- **What:** Implement a basic ReAct (Reason + Act) agent loop. On each turn: send prompt + available tools to LLM → if tool_call, execute tool → append result → loop → return final answer. Max iterations configurable.
- **New files:**
  - `src/agents/__init__.py`
  - `src/agents/base.py` — `Agent` abstract base class
  - `src/agents/react.py` — `ReActAgent` — plan → act → observe loop
  - `src/agents/models.py` — `AgentRun`, `AgentStep`, `AgentResult` Pydantic models
- **Files changed:** `src/retrieval/pipeline.py` (route agent-mode requests through ReActAgent), `src/api/routes.py` (add `/agent/run` endpoint), `src/core/settings.py` (add `agent_max_iterations`, `agent_mode_enabled`)
- **Risk:** High — new execution paradigm. Requires careful error handling and loop termination guards.
- **Outcome:** The platform can answer questions that require multiple steps: search → read → synthesize. This is the core V2 capability.

#### 2.4 New Agent Endpoint
- **What:** `POST /agent/run` — accepts `task` (string), optional `thread_id`, optional `tools` list. Runs ReActAgent. Returns final answer + step trace (list of tool calls and results).
- **Files changed:** `src/api/routes.py`
- **New files:** `src/api/models.py` — request/response Pydantic models (consolidate all API models here)
- **Risk:** Low — additive endpoint
- **Outcome:** Clients can invoke the agent explicitly vs. the simpler `/ask` endpoint.

#### 2.5 Streaming Responses
- **What:** Add `stream=true` query parameter to `/ask` and `/agent/run`. Use FastAPI `StreamingResponse` + Server-Sent Events. Stream LLM tokens as they arrive.
- **New files:** `src/api/streaming.py` — SSE formatter and stream helpers
- **Files changed:** `src/providers/openai_provider.py`, `src/providers/anthropic_provider.py`, `src/api/routes.py`
- **Risk:** Medium — async streaming requires provider refactor to use `httpx.AsyncClient`
- **Outcome:** UI can show tokens as they stream. Perceived latency drops dramatically.

#### Phase 2 Test Additions
- `tests/test_tools.py` — tool registry and individual tool tests
- `tests/test_agent.py` — ReActAgent loop, termination, error handling
- `tests/test_streaming.py` — SSE output validation

**Phase 2 Outcome:** NeuroOps can run multi-step tasks using real tools. It is now meaningfully an "agent platform," not just a Q&A API. Demo-worthy milestone.

---

### Phase 3 — Retrieval Quality
**Goal:** Make the RAG knowledge backbone genuinely useful at production scale.

**Dependency:** Phase 1 ingestion pipeline must exist.

#### 3.1 Chunking Strategies
- **What:** Upgrade `src/ingestion/chunker.py` (created in Phase 1) with multiple strategies:
  - Fixed-size with overlap
  - Recursive text splitter (respects paragraph/sentence boundaries)
  - Markdown-aware chunker
- **Files changed:** `src/ingestion/chunker.py`, `src/core/settings.py` (add `chunk_strategy`, `chunk_size`, `chunk_overlap`)
- **Risk:** Low
- **Outcome:** Document ingestion produces meaningfully-sized, contextually coherent chunks.

#### 3.2 Metadata Storage
- **What:** Add metadata columns to pgvector table (`source`, `doc_type`, `created_at`, `chunk_index`, `total_chunks`). Pass metadata through ingestion and return in retrieval results.
- **Files changed:** `src/vectorstores/pgvector_store.py`, `db/init.sql`, `src/ingestion/models.py`
- **New files:** `db/migrations/001_add_metadata.sql` (start migration tracking)
- **Risk:** Medium — schema change. Requires migration for existing deployments.
- **Outcome:** Retrieved chunks include source attribution. `/ask` and `/agent/run` responses can cite document sources.

#### 3.3 Reranking Stage
- **What:** After vector retrieval (top-k cosine similarity), apply a reranking pass to reorder by relevance. Start with a lightweight cross-encoder or BM25 hybrid. Optional Cohere Rerank API integration.
- **New files:**
  - `src/retrieval/reranker.py` — `Reranker` abstract base + `BM25Reranker` + optional `CohereReranker`
- **Files changed:** `src/retrieval/pipeline.py` (add reranking stage), `src/core/settings.py` (add `rerank_enabled`, `rerank_top_k`)
- **Risk:** Low — purely additive stage
- **Outcome:** Retrieved context is higher quality. LLM gets the most relevant chunks, not just the nearest vectors.

#### 3.4 Multi-Source Connectors
- **What:** Implement the real REST connector. Add a URL connector (fetch + extract main content from a web page). Both become available tools in the Tool Registry.
- **Files changed:** `src/connectors/rest_connector.py` (implement), `src/connectors/url_connector.py` (new)
- **New files:** `src/connectors/url_connector.py`, `src/tools/builtin/url_fetch.py`
- **Risk:** Low
- **Outcome:** Agent can pull context from REST APIs and URLs, not just local files and vector search.

#### 3.5 Long-Term Memory Service
- **What:** Expand `src/memory/` (created in Phase 1) with a long-term memory layer. Key-value facts stored per user/thread. Vector-searchable memory entries. Supports `remember(fact)` and `recall(query)` operations.
- **New files:**
  - `src/memory/long_term.py` — `LongTermMemory` — PostgreSQL + pgvector backed
  - `src/memory/session.py` — `SessionMemory` — Redis-backed short-term (with in-memory fallback)
  - `src/tools/builtin/memory_store.py` — exposes memory as a tool the agent can call
- **Files changed:** `src/core/settings.py` (add `redis_url`, `memory_ttl_seconds`), `db/init.sql`
- **Risk:** Medium — Redis introduces a new infrastructure dependency (with fallback path)
- **Outcome:** Agent can remember things across sessions. Users get a persistent assistant, not an amnesiac.

#### Phase 3 Test Additions
- `tests/test_chunking.py` — chunking strategy correctness
- `tests/test_reranking.py` — reranker output ordering
- `tests/test_memory.py` — long-term memory store/recall

**Phase 3 Outcome:** The RAG pipeline is genuinely production-quality. Context is chunked, ranked, and sourced. The agent has a memory system. This is a complete intelligent assistant backend.

---

### Phase 4 — Observability and Infrastructure
**Goal:** Make the platform operable at production scale. Enable debugging, performance analysis, and horizontal scaling.

**Dependency:** Phase 1 and 2 must be complete (you need the system to instrument).

#### 4.1 OTEL Instrumentation
- **What:** Implement `src/core/telemetry.py`. Add spans to: request lifecycle, RAG pipeline stages, provider LLM calls (with token counts), tool executions, agent loop iterations, vector store queries.
- **New files:** `src/core/telemetry.py` — OTEL tracer setup + span context helpers
- **Files changed:** `src/retrieval/pipeline.py`, `src/providers/` (all), `src/agents/react.py`, `src/vectorstores/pgvector_store.py`, `src/main.py`
- **Risk:** Low — additive instrumentation
- **Outcome:** Full distributed traces visible in Phoenix. Every agent run shows every step with latency.

#### 4.2 Async Provider Migration
- **What:** Replace `requests` with `httpx.AsyncClient` in all providers. Convert `generate()` to `async def generate()`. Cascades to `answer_question()` and agent loop (already async).
- **Files changed:** `src/providers/openai_provider.py`, `src/providers/anthropic_provider.py`, `src/providers/gemini_provider.py`, `src/retrieval/pipeline.py`, `src/agents/react.py`, `pyproject.toml` (add httpx)
- **Risk:** Medium — async refactor touches many files. Must be done atomically.
- **Outcome:** FastAPI's async event loop is no longer blocked by LLM API calls. Throughput under load improves significantly.

#### 4.3 Redis for Rate Limiter and Session Cache
- **What:** Upgrade `src/middleware/rate_limit.py` to use Redis for distributed sliding window. Session memory (Phase 3) uses Redis as primary store.
- **Files changed:** `src/middleware/rate_limit.py`, `docker-compose.yml` (add Redis service), `src/core/settings.py` (add `redis_url`)
- **Risk:** Medium — new infrastructure dependency. Must maintain in-memory fallback for local dev without Redis.
- **Outcome:** Multiple API workers share the same rate limit state. Rate limiting works correctly at scale.

#### 4.4 Database Migrations
- **What:** Replace inline DDL in `src/vectorstores/pgvector_store.py` with proper Alembic migrations. Add migration runner to `src/cli.py`.
- **New files:** `alembic/` directory, initial migrations for all tables
- **Files changed:** `src/vectorstores/pgvector_store.py`, `src/cli.py`, `pyproject.toml` (add alembic)
- **Risk:** Medium — migration setup requires care around existing deployments
- **Outcome:** Schema changes are versioned, reversible, and safe to run in production.

#### 4.5 Prometheus Metrics Endpoint
- **What:** Add `GET /metrics` (Prometheus format). Track: request count, latency histograms, LLM token usage, agent loop iterations, error rates, vector store query latency.
- **New files:** `src/core/metrics.py`
- **Files changed:** `src/main.py`, `src/api/routes.py`, `pyproject.toml` (add prometheus-fastapi-instrumentator or starlette-exporter)
- **Risk:** Low
- **Outcome:** Platform is monitorable. Grafana dashboards can be built. Alerts can fire.

**Phase 4 Outcome:** The platform is production-operable. Every request is traceable. The system scales horizontally. Database migrations are safe. Metrics are scrape-able.

---

### Phase 5 — UI Layer
**Goal:** Make NeuroOps accessible to non-API users. Ship a thin but real chat interface and admin view.

**Dependency:** Phase 1 and 2 complete. The API must support `thread_id` and streaming.

#### 5.1 Chat Interface
- **What:** Minimal chat UI. Shows conversation thread, streams LLM response tokens, displays tool call steps (collapsible), shows source citations.
- **Location:** `ui/` (top-level directory, separate from `src/`)
- **Framework:** **Next.js 14 (App Router)** with Tailwind CSS
  - Rationale: React ecosystem, built-in SSE support, easy Docker deployment, large community
- **Files:**
  - `ui/app/page.tsx` — chat view
  - `ui/app/layout.tsx` — base layout
  - `ui/components/ChatWindow.tsx`
  - `ui/components/Message.tsx`
  - `ui/components/SourceCard.tsx`
  - `ui/components/ToolCallTrace.tsx`
  - `ui/lib/api.ts` — typed API client (calls NeuroOps backend)
  - `ui/Dockerfile` — standalone UI container
- **Risk:** Medium — new technology stack (TypeScript, Next.js). Isolated in `ui/` so backend is unaffected.
- **Outcome:** Anyone can use NeuroOps without curl or Postman.

#### 5.2 Document Management View
- **What:** Simple admin page for uploading documents, viewing ingested chunks, deleting from vector store. Requires `POST /ingest` and new `GET /documents` + `DELETE /documents/{id}` endpoints (add in this phase).
- **Files:** `ui/app/admin/page.tsx`, `ui/components/DocumentList.tsx`, `ui/components/UploadForm.tsx`
- **Backend:** `src/api/routes.py` (add `/documents` endpoints)
- **Risk:** Low
- **Outcome:** Operators can manage the knowledge base without direct DB access.

#### 5.3 Docker Compose Integration
- **What:** Add `ui` service to `docker-compose.yml` (disabled by default via a `profiles` config). One command brings up the full stack.
- **Files changed:** `docker-compose.yml`
- **Risk:** Low
- **Outcome:** `docker compose --profile ui up` brings up backend + DB + UI in one command.

**Phase 5 Outcome:** NeuroOps is a complete product. API-first for developers, UI available for operators and end-users. Both backed by the same codebase.

---

## 4. Phase Summary Table

| Phase | Name | Risk | New Files | Changed Files | Key Unlock |
|-------|------|------|-----------|---------------|------------|
| 1 | Critical Foundations | Low-Medium | ~8 | ~10 | Real RAG + multi-turn |
| 2 | Agent Core | Medium-High | ~12 | ~8 | Multi-step tool use |
| 3 | Retrieval Quality | Low-Medium | ~8 | ~6 | Production RAG quality |
| 4 | Observability & Infra | Medium | ~6 | ~12 | Production operability |
| 5 | UI Layer | Medium | ~15 | ~3 | Product accessibility |

---

## 5. Proposed V2 Repository Structure

```
NeuroOps-RAG-Platform/
│
├── .github/
│   └── workflows/
│       └── ci.yml                        ← MOVED from workflows_disabled/
│
├── alembic/                              ← NEW (Phase 4)
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
│
├── db/
│   ├── init.sql                          ← Keep (dev bootstrap)
│   └── migrations/                       ← NEW (Phase 3)
│       └── 001_add_metadata.sql
│
├── docs/                                 ← Keep + expand per phase
│
├── observability/                        ← Keep unchanged
│
├── src/
│   ├── agents/                           ← NEW (Phase 2)
│   │   ├── __init__.py
│   │   ├── base.py                       ← Agent abstract base
│   │   ├── react.py                      ← ReActAgent implementation
│   │   └── models.py                     ← AgentRun, AgentStep, AgentResult
│   │
│   ├── api/
│   │   ├── routes.py                     ← UPGRADE (new endpoints)
│   │   ├── models.py                     ← NEW (consolidated API models)
│   │   └── streaming.py                  ← NEW (Phase 2, SSE helpers)
│   │
│   ├── connectors/
│   │   ├── base.py                       ← Keep
│   │   ├── rest_connector.py             ← IMPLEMENT (Phase 1)
│   │   ├── url_connector.py              ← NEW (Phase 3)
│   │   └── files/
│   │       └── files_connector.py        ← Keep
│   │
│   ├── core/
│   │   ├── settings.py                   ← EXPAND (new config fields)
│   │   ├── logging.py                    ← IMPLEMENT (Phase 1, currently empty)
│   │   ├── telemetry.py                  ← NEW (Phase 4, OTEL)
│   │   └── metrics.py                    ← NEW (Phase 4, Prometheus)
│   │
│   ├── embeddings/
│   │   ├── base.py                       ← Keep
│   │   └── openai_embeddings.py          ← Keep
│   │
│   ├── ingestion/                        ← NEW (Phase 1)
│   │   ├── __init__.py
│   │   ├── chunker.py                    ← Chunking strategies
│   │   ├── pipeline.py                   ← Ingestion orchestration
│   │   └── models.py                     ← IngestRequest, IngestResult
│   │
│   ├── memory/                           ← NEW (Phase 1 + 3)
│   │   ├── __init__.py
│   │   ├── conversation.py               ← Phase 1: ConversationStore (Postgres)
│   │   ├── session.py                    ← Phase 3: SessionMemory (Redis)
│   │   ├── long_term.py                  ← Phase 3: LongTermMemory (pgvector)
│   │   └── models.py                     ← Message, Thread, MemoryEntry
│   │
│   ├── meta/
│   │   └── build_info.py                 ← Keep
│   │
│   ├── middleware/
│   │   ├── cors.py                       ← Keep
│   │   ├── rate_limit.py                 ← UPGRADE (Phase 4, Redis-backed)
│   │   ├── request_id.py                 ← NEW (Phase 1)
│   │   └── security_headers.py           ← Keep
│   │
│   ├── providers/
│   │   ├── base.py                       ← UPGRADE (add tool-calling interface)
│   │   ├── models.py                     ← NEW (ToolCall, ToolResult models)
│   │   ├── openai_provider.py            ← UPGRADE (function calling + async)
│   │   ├── anthropic_provider.py         ← UPGRADE (tool_use + async)
│   │   └── gemini_provider.py            ← Keep (async later)
│   │
│   ├── retrieval/
│   │   ├── pipeline.py                   ← REFACTOR (decompose stages)
│   │   └── reranker.py                   ← NEW (Phase 3)
│   │
│   ├── security/
│   │   └── auth.py                       ← Keep
│   │
│   ├── tools/                            ← NEW (Phase 2)
│   │   ├── __init__.py
│   │   ├── registry.py                   ← ToolRegistry + register_tool()
│   │   ├── base.py                       ← Tool abstract base
│   │   └── builtin/
│   │       ├── web_search.py             ← Wraps websearch/ providers
│   │       ├── vector_search.py          ← Wraps vectorstores/
│   │       ├── file_read.py              ← File reading tool
│   │       ├── url_fetch.py              ← NEW Phase 3
│   │       └── memory_store.py           ← NEW Phase 3
│   │
│   ├── vectorstores/
│   │   ├── base.py                       ← Keep
│   │   ├── memory_store.py               ← MARK dev-only or remove
│   │   └── pgvector_store.py             ← UPGRADE (metadata columns)
│   │
│   ├── websearch/
│   │   ├── base.py                       ← Keep
│   │   ├── serper_search.py              ← Keep
│   │   └── tavily_search.py              ← IMPLEMENT (Phase 1)
│   │
│   ├── cli.py                            ← UPGRADE (add migrate command)
│   └── main.py                           ← UPGRADE (register tools at startup)
│
├── tests/
│   ├── test_health.py                    ← Keep
│   ├── test_ingestion.py                 ← NEW (Phase 1)
│   ├── test_conversation.py              ← NEW (Phase 1)
│   ├── test_providers.py                 ← NEW (Phase 1)
│   ├── test_tools.py                     ← NEW (Phase 2)
│   ├── test_agent.py                     ← NEW (Phase 2)
│   ├── test_chunking.py                  ← NEW (Phase 3)
│   ├── test_reranking.py                 ← NEW (Phase 3)
│   ├── test_memory.py                    ← NEW (Phase 3)
│   └── smoke_test.py                     ← Keep + extend
│
├── ui/                                   ← NEW (Phase 5)
│   ├── app/
│   │   ├── page.tsx                      ← Chat view
│   │   ├── layout.tsx
│   │   └── admin/
│   │       └── page.tsx                  ← Document management
│   ├── components/
│   │   ├── ChatWindow.tsx
│   │   ├── Message.tsx
│   │   ├── SourceCard.tsx
│   │   └── ToolCallTrace.tsx
│   ├── lib/
│   │   └── api.ts                        ← Typed NeuroOps API client
│   ├── Dockerfile
│   ├── next.config.js
│   └── package.json
│
├── scripts/                              ← Keep + add new scripts
├── terraform/                            ← Keep (expand later)
├── docker-compose.yml                    ← UPGRADE (add Redis, UI profile)
├── Dockerfile                            ← Keep
├── pyproject.toml                        ← UPGRADE (rename, add deps)
└── .env.example                          ← EXPAND (new config fields)
```

---

## 6. API Evolution Plan

### Current API (V1)
```
GET  /health
GET  /ready
POST /ask   { "question": str }
```

### V2 API — Full Surface

#### Unchanged (backward compatible)
```
GET  /health                              ← Unchanged
GET  /ready                               ← Unchanged
```

#### Evolved Endpoints
```
POST /ask                                 ← EVOLVED (backward compatible)
  Request:
    {
      "question": str,                    ← Keep (existing)
      "thread_id": str | null,            ← NEW (optional, enables history)
      "stream": bool                      ← NEW (optional, default false)
    }
  Response:
    {
      "answer": str,                      ← Keep
      "thread_id": str,                   ← NEW (always returned)
      "provider": str,                    ← Keep
      "sources": { ... },                 ← Keep + add doc metadata
      "request_id": str                   ← NEW
    }
```

**Backward compatibility:** `thread_id` is optional. Callers that don't send it get a fresh thread each time. V1 clients continue to work.

#### New Endpoints — Phase 1
```
POST /ingest
  Request:  { "text": str, "source": str, "doc_type": str, "metadata": dict }
  Response: { "doc_id": str, "chunks": int, "tokens": int }

POST /ingest/batch
  Request:  [IngestRequest, ...]
  Response: [IngestResult, ...]
```

#### New Endpoints — Phase 2
```
POST /agent/run
  Request:
    {
      "task": str,
      "thread_id": str | null,
      "tools": [str] | null,              ← Subset of tool names to allow
      "max_iterations": int               ← Default from settings
    }
  Response:
    {
      "answer": str,
      "thread_id": str,
      "steps": [AgentStep],               ← Tool calls and results
      "iterations": int,
      "request_id": str
    }

GET /tools
  Response: [{ "name": str, "description": str, "schema": dict }]
```

#### New Endpoints — Phase 3
```
GET  /memory/{thread_id}                  ← Retrieve conversation history
DELETE /memory/{thread_id}               ← Clear a thread

GET  /documents                          ← List ingested documents
GET  /documents/{doc_id}                 ← Get document + chunks
DELETE /documents/{doc_id}               ← Remove from vector store
```

#### New Endpoints — Phase 4
```
GET /metrics                             ← Prometheus scrape endpoint
```

### What Must Remain Backward Compatible
- `POST /ask` request body (`question` field required, all new fields optional)
- `/health` and `/ready` response schemas
- `X-API-Key` authentication mechanism

---

## 7. Minimal Viable V2 Milestone

### V2 Milestone 1 — "Conversational RAG with Ingestion"

**Definition:** The smallest release that is meaningfully different from V1, demo-worthy, and provides a real foundation for the agent layer.

**Scope:** Phase 1 complete.

**What it includes:**
1. CI/CD re-enabled (every commit tested)
2. Structured logging + request IDs on all responses
3. `POST /ingest` — load documents with chunking into pgvector
4. `POST /ask` — now supports `thread_id` for multi-turn conversation
5. All stubs replaced with real implementations (Tavily, REST connector)
6. Provider timeouts and basic error handling
7. Boot document removed from vector store
8. Test coverage expanded to cover pipeline, providers, ingestion

**What it does NOT include:**
- Agent loop (Phase 2)
- Tool registry (Phase 2)
- Streaming (Phase 2)
- Reranking (Phase 3)
- UI (Phase 5)

**Why this is the right milestone:**
- It is complete — every feature works correctly
- It is demonstrable — you can ingest a document and have a multi-turn conversation about it
- It is a foundation — Phase 2 tools and agents build directly on ingestion + history
- It has no stubs — every listed feature is real

**Demo script for Milestone 1:**
```bash
# 1. Ingest a document
curl -X POST /ingest -H "X-API-Key: ..." \
  -d '{"text": "NeuroOps is an agentic AI platform...", "source": "about.md"}'

# 2. Start a conversation
curl -X POST /ask -H "X-API-Key: ..." \
  -d '{"question": "What is NeuroOps?"}'
# → Returns: answer + thread_id

# 3. Continue the conversation
curl -X POST /ask -H "X-API-Key: ..." \
  -d '{"question": "Tell me more", "thread_id": "<from above>"}'
# → Responds with context from previous turn
```

---

## 8. UI Recommendation

### Framework: Next.js 14 (App Router) + Tailwind CSS

**Rationale:**
- Built-in SSE support for streaming responses (no extra library)
- TypeScript by default — matches the typed API contract
- App Router's `use client` / `use server` model maps cleanly to the API interaction pattern
- Easy Dockerization with `output: 'standalone'` in `next.config.js`
- Deployed as a separate Docker service — completely decoupled from the Python backend

**Alternative considered:** SvelteKit — lighter weight, but smaller ecosystem and fewer NeuroOps-adjacent examples.

### Screens to Build First (in order)

1. **Chat screen** (`/`) — the core product surface
   - Message list with assistant + user bubbles
   - Streaming response rendering (tokens appear as they arrive)
   - Collapsible "Tool calls" trace for agent runs
   - Source citation cards below each response
   - Thread persistence via localStorage (`thread_id`)

2. **Document management** (`/admin`) — operator surface
   - Upload text or file to `/ingest`
   - List ingested documents (source, chunk count, date)
   - Delete button per document

3. **Settings panel** (sidebar) — developer convenience
   - Switch between `/ask` and `/agent/run` mode
   - Select which tools to enable for agent runs
   - Display current provider and model

### How to Keep It Decoupled

- The UI lives entirely in `ui/` — it has no imports from `src/`
- It communicates exclusively through the NeuroOps HTTP API
- `ui/lib/api.ts` is the only file that knows the API URL (configured via `NEXT_PUBLIC_API_URL` env var)
- UI is an optional Docker Compose service:
  ```yaml
  # docker-compose.yml
  ui:
    profiles: ["ui"]
    build: ./ui
    ports: ["3000:3000"]
    environment:
      NEXT_PUBLIC_API_URL: http://api:8000
  ```
- Adding `--profile ui` opts in. Default compose startup does not include it.
- The UI has its own `ui/package.json` and `ui/Dockerfile` — fully self-contained

---

## 9. Final Recommendation

### Current Phase 1 Status

1. ✅ **Re-enable CI/CD** — done
2. **Structured logging** (`src/core/logging.py` + `src/middleware/request_id.py`) — still pending
3. ✅ **Fix stubs** — Tavily and REST connector are real; memory store marked dev-only
4. ✅ **Document ingestion** (`src/ingestion/`) — `POST /ingest` endpoint live
5. **Conversation history** (`src/memory/conversation.py` + `thread_id` in `/ask`) — still pending

### Postpone Until Phase 2 is Stable

- Streaming responses — requires async provider migration. Do this after the agent loop is proven.
- Redis integration — add it when you need horizontal scaling. In-memory fallback works for Phase 1-2 development.
- Alembic migrations — important for production, but inline DDL is fine while the schema is still changing.

### Do NOT Build Yet

- **Kubernetes / ECS** — `docker-compose.yml` is sufficient through Phase 3. Cloud-native deployment is a post-V2 concern.
- **Multi-tenancy / per-user API keys** — single-key model is fine. Add multi-tenancy only if you have multiple real tenants.
- **A second embedding model** — OpenAI `text-embedding-3-small` is excellent. Multi-model embedding support adds complexity without benefit until you have a specific reason to switch.
- **GraphQL API** — REST is the right choice here. Do not add GraphQL.
- **Fine-tuned models** — out of scope for an agentic platform. Use best-available foundation models.
- **Knowledge graph** — mentioned in architecture direction but is premature. Implement only after long-term memory + reranking are proven insufficient.
- **Computer use / browser automation** — Playwright integration is a Phase 6+ concern. Build the agent loop first and prove it with simpler tools.

---

## Appendix: V2 Dependency Graph

```
Phase 1: Critical Foundations
├── CI/CD re-enable (no deps)
├── Structured logging (no deps)
├── Fix stubs (no deps)
├── Provider hardening (no deps)
├── Ingestion pipeline (no deps)
└── Conversation history (deps: DB schema)

Phase 2: Agent Core
├── Function calling (deps: Phase 1 providers)
├── Tool registry (deps: Phase 1 stubs fixed)
├── ReAct agent loop (deps: function calling, tool registry, conversation history)
├── /agent/run endpoint (deps: agent loop)
└── Streaming (deps: async providers, Phase 1)

Phase 3: Retrieval Quality
├── Chunking strategies (deps: Phase 1 ingestion)
├── Metadata columns (deps: Phase 1 ingestion)
├── Reranking (deps: metadata)
├── Multi-source connectors (deps: Phase 1 connectors fixed)
└── Long-term memory (deps: Phase 1 conversation history)

Phase 4: Observability & Infra
├── OTEL instrumentation (deps: Phase 2 complete — need full call graph)
├── Async providers (deps: Phase 2 — do atomically with streaming)
├── Redis (deps: Phase 3 — needed for session memory)
├── Alembic (deps: Phase 3 — schema stabilizes)
└── Prometheus metrics (deps: Phase 4 OTEL)

Phase 5: UI
├── Chat interface (deps: Phase 2 streaming, thread_id)
└── Document management (deps: Phase 1 ingestion, Phase 3 /documents endpoints)
```

---

*This roadmap is based on `docs/V2_AUDIT_REPORT.md`. Phase 1 is largely complete. Remaining phases (2–5) are pending.*
