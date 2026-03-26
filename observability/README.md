# Observability (Phoenix + OpenTelemetry)

This folder contains an **optional** observability stack for tracing RAG / LLM flows.
It is **not required** for the core RAG API to run and is intended for **local debugging** and learning.

## What’s inside

- `docker-compose.phoenix.yml` – runs Phoenix + OpenTelemetry Collector
- `otel/config.yaml` – Collector configuration (receivers/exporters/pipelines)

## When to use this

Use it when you want to:

- verify the RAG pipeline steps (retrieve → generate)
- inspect request traces and span timings
- debug latency, retries, or unexpected behavior

## When NOT to use this

- not needed for core runtime
- not configured as production monitoring
- no persistence / scaling assumptions

## Quick Start

1) From repo root:
docker compose -f observability/docker-compose.phoenix.yml up -d

2) Open Phoenix UI:  http://localhost:6006

3) Stop:
docker compose -f observability/docker-compose.phoenix.yml down

## Notes

If the app is not instrumented yet, Phoenix may show no traces (that’s expected).

Keep this stack optional and isolated from the main compose/runtime unless explicitly enabled.


