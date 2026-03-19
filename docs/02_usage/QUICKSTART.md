# Quick Reference - NeuroOps – RAG Platform Local Development

## 🚀 Quick Start

```bash
# 1. Build and start
docker compose build --no-cache
docker compose up -d

# 2. Verify running
docker compose ps

# 3. Test endpoints
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready

# 4. Run smoke tests
python tests/smoke_test.py

# 5. Cleanup
docker compose down
```

## 📊 Observability Stack

```bash
# Start Phoenix + OTel
docker compose -f observability/docker-compose.phoenix.yml up -d

# Access Phoenix UI
http://127.0.0.1:6006

# Stop
docker compose -f observability/docker-compose.phoenix.yml down
```

## 🧪 Testing

```bash
# Smoke tests (no pytest required)
python tests/smoke_test.py

# Pytest (if installed)
pytest -q

# Test specific endpoint
curl -X POST http://127.0.0.1:8000/ask \
  -H "X-API-Key: dev-test-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```

## 🔧 Useful Commands

```bash
# View logs
docker compose logs -f api
docker compose logs -f db

# Restart single service
docker compose restart api

# Rebuild without cache
docker compose build --no-cache api

# Remove everything including volumes
docker compose down -v

# Check container health
docker compose ps
docker inspect rag-agent-kit-db-1 | grep -A 10 Health
```

## 📁 Important Files

| File | Purpose |
|------|---------|
| `.env` | Environment configuration (API keys, settings) |
| `docker-compose.yml` | Main stack (API + DB) |
| `observability/docker-compose.phoenix.yml` | Observability stack |
| `tests/smoke_test.py` | Standalone smoke tests |
| `src/core/settings.py` | Application settings |
| `.github/workflows/ci.yml` | CI/CD pipeline |

## 🌐 Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check |
| `/ready` | GET | No | Readiness check |
| `/docs` | GET | No | API documentation (Swagger) |
| `/ask` | POST | Yes | Ask questions (requires X-API-Key header) |

## 🔑 Environment Variables

Required:
```bash
RAG_API_KEY=dev-test-key-12345  # Required for API access
```

Optional (defaults work for local testing):
```bash
LLM_PROVIDER=openai              # openai|gemini|anthropic
VECTORSTORE=memory               # memory|pgvector
CONNECTOR=rest                   # rest|files
CORS_ENABLED=false               # Keep disabled
RATE_LIMIT_ENABLED=true          # Keep enabled
```

## 🐛 Troubleshooting

### API won't start
```bash
# Check logs
docker compose logs api

# Common issues:
# 1. RAG_API_KEY not set → Set in .env
# 2. Port 8000 in use → Change port in docker-compose.yml
# 3. DB not healthy → Check db logs
```

### Database connection failed
```bash
# Check DB is healthy
docker compose ps

# Verify PG_DSN in .env
PG_DSN=postgresql://rag:rag@db:5432/rag  # For Docker
# NOT: postgresql://rag:rag@127.0.0.1:5432/rag
```

### Docker Desktop not running
```bash
# Windows
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Wait ~30 seconds, then verify
docker ps
```

## 📝 Reports

All verification reports in `reports/`:
- `local_smoke_test.md` - Endpoint verification
- `observability_check.md` - Phoenix + OTel setup
- `test_output.txt` - Test results
- `cleanup_notes.md` - Shutdown procedures
- `VERIFICATION_SUMMARY.md` - Complete summary

## 🔒 Security Notes

- ✅ API key authentication enforced on `/ask`
- ✅ CORS disabled by default
- ✅ Rate limiting enabled (60 req/min)
- ✅ Security headers middleware active
- ✅ Stub mode when no LLM API keys set

## 📦 Container Images

- API: `rag-agent-kit-api` (built locally)
- DB: `pgvector/pgvector:pg16`
- Phoenix: `arizephoenix/phoenix:latest`
- OTel: `otel/opentelemetry-collector`

## 🎯 Common Workflows

### Start development session
```bash
docker compose up -d
# Make code changes...
docker compose restart api  # Restart API to pick up changes
```

### Full rebuild after dependency changes
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Fresh database
```bash
docker compose down -v  # Remove volumes
docker compose up -d    # Reinitialize
```

### Run CI locally
```bash
# Install dependencies
pip install -e .
pip install pytest

# Run tests
pytest -q
python tests/smoke_test.py
```

---

**Need help?** See full documentation in `docs/` directory.
