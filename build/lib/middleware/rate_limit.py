# src/middleware/rate_limit.py
# Rate limiting middleware for the RAG Agent Kit application.

import time
from collections import defaultdict, deque
from fastapi import Request
from fastapi.responses import JSONResponse
from src.core.settings import settings

# In-memory sliding window: key -> timestamps
_hits: dict[str, deque[float]] = defaultdict(deque)

# Get current time in seconds
def _now() -> float:
    return time.time()

# Function to add rate limiting middleware to the FastAPI app
def rate_limit_middleware(app):
    @app.middleware("http")
    async def _rate_limit(request: Request, call_next):
        if not getattr(settings, "rate_limit_enabled", True):
            return await call_next(request)

        # Apply only to API endpoints (avoid blocking docs if you want)
        path = request.url.path
        if path in ("/health", "/ready"):
            return await call_next(request)

        # Key: API key + client IP (best-effort)
        api_key = request.headers.get("X-API-Key", "no-key")
        client_ip = request.client.host if request.client else "unknown"
        bucket = f"{client_ip}:{api_key}"

        limit = int(getattr(settings, "rate_limit_per_minute", 60))
        window = 60.0
        q = _hits[bucket]
        t = _now()

        # drop old
        while q and (t - q[0]) > window:
            q.popleft()

        if len(q) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )

        q.append(t)
        return await call_next(request)

    return app
