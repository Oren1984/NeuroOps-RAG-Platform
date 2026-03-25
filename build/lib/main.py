# src/main.py
# Main application entry point for the NeuroOps Agent Platform.

import logging

from fastapi import FastAPI

from src.core.logging import configure_logging, get_logger
from src.core.settings import settings
from src.api.routes import router
from src.meta.build_info import build_info
from src.middleware.cors import cors_middleware
from src.middleware.rate_limit import rate_limit_middleware
from src.middleware.request_id import request_id_middleware
from src.middleware.security_headers import security_headers_middleware

logger = get_logger(__name__)


# Create and configure the FastAPI application
def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    if not settings.rag_api_key or settings.rag_api_key.strip() == "":
        raise RuntimeError("RAG_API_KEY is required. Set it in .env (or environment).")

    app = FastAPI(title=settings.app_name)
    app.state.build = build_info()

    # Middlewares — order matters: last registered runs outermost (first on request)
    cors_middleware(app)
    security_headers_middleware(app)
    rate_limit_middleware(app)
    request_id_middleware(app)   # outermost: runs first, logs every request

    app.include_router(router)

    logger.info(
        "startup",
        extra={
            "app": settings.app_name,
            "env": settings.app_env,
            "provider": settings.llm_provider,
            "vectorstore": settings.vectorstore,
        },
    )
    return app


app = create_app()
