# src/middleware/request_id.py
# Request ID middleware for NeuroOps Agent Platform.
#
# Attaches a unique request_id to every HTTP request:
#   - Reads X-Request-ID header if provided by the caller (passthrough)
#   - Generates a new UUID v4 otherwise
#   - Stores it on request.state.request_id for use in route handlers
#   - Echoes it back as X-Request-ID on every response
#   - Emits one structured access log line per request (method, path, status, latency)

import logging
import time
import uuid
from contextvars import ContextVar

from fastapi import Request

logger = logging.getLogger("neuroops.access")

# Module-level context variable so any code running within a request
# can call get_request_id() without needing the Request object.
_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Return the request_id for the currently active request, or '' if none."""
    return _request_id_ctx.get()


def request_id_middleware(app):
    @app.middleware("http")
    async def _request_id(request: Request, call_next):
        # Honour a caller-supplied ID (useful for end-to-end tracing from a client)
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Make it available via context var and request state
        token = _request_id_ctx.set(req_id)
        request.state.request_id = req_id

        t0 = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            _request_id_ctx.reset(token)

        latency_ms = round((time.perf_counter() - t0) * 1000)
        response.headers["X-Request-ID"] = req_id

        logger.info(
            "request",
            extra={
                "request_id": req_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "latency_ms": latency_ms,
            },
        )
        return response

    return app
