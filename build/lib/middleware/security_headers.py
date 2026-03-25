# src/middleware/security_headers.py
# Security headers middleware for the RAG Agent Kit application.

from fastapi import Request
from src.core.settings import settings

# Function to add security headers middleware to the FastAPI app
def security_headers_middleware(app):
    @app.middleware("http")
    async def _headers(request: Request, call_next):
        response = await call_next(request)

        # Basic security headers (safe defaults)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # HSTS only in non-dev (if behind TLS proxy)
        if getattr(settings, "app_env", "dev").lower() in ("prod", "production"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

    return app
