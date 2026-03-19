# NeuroOps – RAG Platform

AI-powered Retrieval-Augmented Generation platform for secure knowledge retrieval, context enrichment, and intelligent agent workflows.

> Part of the NeuroOps ecosystem – AI Systems • Intelligent Operations • Autonomous Platforms

---

## Overview

NeuroOps – RAG Platform is a modular, API-first system designed to integrate intelligent knowledge retrieval into any application.

It is built with a strong focus on:
- **Security-first design**
- **Modularity and extensibility**
- **Production-ready deployment (Docker-based)**

> No UI. API-only. Designed for autonomous operation with built-in safety checks.

---

## Features

- Core RAG API: `POST /ask`
- Health & Readiness: `GET /health`, `GET /ready`
- Pluggable LLM providers: OpenAI / Gemini / Anthropic *(Copilot optional/experimental)*
- Pluggable connectors: REST / Files *(extendable)*
- Optional Web Search (OFF by default)
- Built-in audit + smoke test scripts
- CI pipeline for validation and testing
- **Automation Ready**: Integration with n8n, webhooks, and external workflows
- **Live Intelligence (Optional)**: Tavily / Serper for real-time enrichment

---

## Architecture Philosophy

This system is designed as a **platform**, not just a single agent.

It enables:
- Knowledge retrieval pipelines
- Context-aware AI responses
- Integration into larger AI systems (agents, workflows, dashboards)

---

## Infrastructure (Optional)

Includes an **infra-only Terraform setup** for AWS (ECR repository only).

- Not used at runtime
- Intended for learning and future extension

See: `docs/AWS_INFRA_ONLY.md`

---

## Quickstart (Docker - Recommended)

1. Clone:
   - `git clone <your-repo-url>`

2. Create `.env`:
   - `cp .env.example .env`
   - Set `RAG_API_KEY` to a strong value

3. Run:
   - `docker compose up -d --build`

4. Open API docs:
   - http://127.0.0.1:8000/docs

---

## Quickstart (No Docker - Dev Only)

1. `python -m venv .venv`
2. Activate environment
3. `pip install -U pip`
4. `pip install .`
5. Copy `.env.example` → `.env`
6. Set `RAG_API_KEY`
7. Run:
   - `uvicorn src.main:app --host 127.0.0.1 --port 8000`

---

## Security (Important)

- **Authentication is mandatory** (`X-API-Key`)
- Runs on **localhost only** by default
- Web search is **disabled by default**
- Do not expose publicly without reverse proxy + TLS

See:
- `docs/SECURITY.md`
- `docs/SECURITY_MODEL.md`

---

## Documentation

- Install: `docs/INSTALL.md`
- Config: `docs/CONFIG.md`
- Security: `docs/SECURITY.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- Deployment: `SUPPORTED_DEPLOYMENT.md`

Hebrew docs:
- `README.he.md`
- `docs/*he.md`

---

## NeuroOps Ecosystem

This project is part of **NeuroOps**, a collection of AI-driven systems:

- Control Room
- Autopilot
- Incident Replay
- AI Agents (BI, Career, etc.)

---

## License

MIT (see `LICENSE`)

---
