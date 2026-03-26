# Observability Check Report

**Date:** 2026-02-03  
**Stack:** Phoenix + OpenTelemetry Collector  
**Status:** ⚠️ PARTIAL - Infrastructure ready, API instrumentation pending

## Summary

The observability infrastructure (Phoenix + OTel Collector) is successfully deployed and operational. However, the NeuroOps – RAG Platform API does not currently have OpenTelemetry instrumentation configured, so no traces are being exported yet.

## Infrastructure Status

### Phoenix (Trace UI)
- **Image:** `arizephoenix/phoenix:latest` (v12.33.1)
- **Status:** ✅ Running
- **URL:** http://127.0.0.1:6006
- **Accessibility:** ✅ Verified (HTTP 200)
- **Features:**
  - UI accessible and responsive
  - Ready to receive traces via HTTP: `http://localhost:6006/v1/traces`
  - Storage: SQLite at `/root/.phoenix/phoenix.db`
  - Authentication: Disabled (local mode)

### OpenTelemetry Collector
- **Image:** `otel/opentelemetry-collector` (v0.144.0)
- **Status:** ✅ Running
- **HTTP Endpoint:** `http://127.0.0.1:4318`
- **Configuration:** `/etc/otel/config.yaml`
- **Pipeline:**
  ```yaml
  receivers: [otlp/http]
  exporters: [otlphttp → phoenix:6006/v1/traces]
  ```
- **Logs:**
  ```
  Everything is ready. Begin running and processing data.
  Starting HTTP server on endpoint: 127.0.0.1:4318
  ```

### Network Configuration
- **Network:** `observability` (Docker bridge)
- **Services:** Phoenix ↔ OTel Collector (can communicate)
- **Host Access:** Both services accessible from host machine

## Container Details

```
NAME                      IMAGE                          PORTS                            STATUS
observability-phoenix-1   arizephoenix/phoenix:latest    0.0.0.0:6006->6006/tcp          Up
observability-otel-1      otel/opentelemetry-collector   0.0.0.0:4318->4318/tcp          Up
```

## Current Limitations

### ⚠️ API Not Instrumented
The NeuroOps – RAG Platform API (`src/main.py`) does not currently include OpenTelemetry instrumentation. No traces are being generated or exported.

**Missing Components:**
1. OpenTelemetry SDK dependencies not installed
2. No tracer initialization in application startup
3. No instrumentation middleware configured
4. No environment variables for OTEL exporter endpoint

## Verification Steps Performed

1. ✅ Started Phoenix + OTel stack: `docker compose -f observability/docker-compose.phoenix.yml up -d`
2. ✅ Verified containers running: Both containers healthy
3. ✅ Tested Phoenix UI: `http://127.0.0.1:6006` → 200 OK
4. ✅ Checked OTel collector logs: HTTP server started successfully
5. ✅ Verified network connectivity: Phoenix ↔ OTel on same network
6. ⚠️ Generated API request: No traces appeared (instrumentation missing)

## Recommendations for Full Observability

To enable trace export from the API to Phoenix, the following changes would be needed:

### 1. Add OpenTelemetry Dependencies
```toml
# pyproject.toml
[project]
dependencies = [
    # ... existing dependencies ...
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-exporter-otlp>=1.20.0",
    "opentelemetry-instrumentation-fastapi>=0.41b0",
]
```

### 2. Configure API Environment Variables
```env
# .env or docker-compose.yml
OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318
OTEL_SERVICE_NAME=rag-agent-kit-api
OTEL_TRACES_EXPORTER=otlp
```

### 3. Instrument FastAPI Application
```python
# src/main.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def create_app() -> FastAPI:
    # Initialize OpenTelemetry
    trace.set_tracer_provider(TracerProvider())
    otlp_exporter = OTLPSpanExporter(endpoint="http://127.0.0.1:4318/v1/traces")
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    app = FastAPI(title=settings.app_name)
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # ... rest of app configuration ...
```

### 4. Connect API to OTel Network (if using Docker)
```yaml
# docker-compose.yml
services:
  api:
    # ... existing config ...
    environment:
      OTEL_EXPORTER_OTLP_ENDPOINT: http://otel:4318
    networks:
      - default
      - observability

networks:
  observability:
    external: true
```

## Testing Trace Export (Once Instrumented)

```bash
# 1. Generate a request
curl -X POST http://127.0.0.1:8000/ask \
  -H "X-API-Key: dev-test-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"question": "test trace"}'

# 2. Open Phoenix UI
open http://127.0.0.1:6006

# 3. Verify traces appear in Phoenix dashboard
```

## Conclusion

**Infrastructure:** ✅ Fully operational  
**API Integration:** ❌ Not yet implemented  
**Next Steps:** Add OpenTelemetry instrumentation to API (see recommendations above)

The observability stack is ready to receive traces. Once the API is instrumented with OpenTelemetry, all requests will be automatically traced and visible in the Phoenix UI for debugging and monitoring.

**Note:** This is intentionally left unimplemented as per the "no new features" boundary. The infrastructure is verified and documented.
