# Observability (Phoenix + OpenTelemetry)

This project includes an **optional** observability stack used to inspect and debug **traces** for RAG / LLM flows.
It is **disabled by default** and **not required** for the core API to run.

## Why this exists
When building RAG systems, it’s easy to lose visibility into:
- where time is spent (retrieval vs. generation)
- which steps ran (retrieve → rerank → generate)
- latency spikes / timeouts
- repeated LLM calls or unexpected branching

This stack provides a lightweight way to see end-to-end traces and validate that the pipeline behaves as expected.

## What’s included
Located under `observability/`:
- **Phoenix**: UI for exploring traces (RAG/LLM oriented)
- **OpenTelemetry Collector (otelcol)**: receives OTLP traces and exports them to Phoenix
- **Docker Compose**: runs Phoenix + Collector on an isolated network

## High-level flow
1. The RAG API emits traces (spans) using OpenTelemetry instrumentation.
2. Traces are sent via **OTLP** (gRPC/HTTP) to the **OpenTelemetry Collector**.
3. The Collector exports traces to **Phoenix**.
4. You open Phoenix UI and inspect requests, spans, durations, and errors.

## Components and responsibilities

### Phoenix
- Provides a UI to explore traces and sessions
- Helps verify the pipeline steps and timings
- Runs as a container (see `observability/docker-compose.phoenix.yml`)

### OpenTelemetry Collector
- Receives traces from your app (OTLP receiver)
- Forwards them to Phoenix (exporter)
- Configured in `observability/otel/config.yaml`

## Quick Start (local)
From the repo root:

1) Start observability stack:
docker compose -f observability/docker-compose.phoenix.yml up -d

2) Verify containers:
docker ps

3) Open Phoenix UI:

http://localhost:6006

If your app is not instrumented yet, Phoenix may show no traces.
That’s OK — the stack can be prepared in advance.

## Common checks
Phoenix UI loads at http://localhost:6006

Collector is running and has no repeated error logs:

docker logs <otel_container_name>
Network connectivity between otel → phoenix is healthy (same docker network)


## Boundaries (important)
Optional: the API does not depend on this stack

Local/dev focused: no production assumptions (auth, scaling, persistence)

Not a full monitoring solution: this is tracing-focused tooling


## Where to look next
observability/README.md – short explanation + quick commands


---