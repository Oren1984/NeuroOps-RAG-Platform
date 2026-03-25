# src/middleware/cors.py
# CORS middleware configuration for the RAG Agent Kit application.

from fastapi.middleware.cors import CORSMiddleware
from src.core.settings import settings

# Function to add CORS middleware to the FastAPI app
def cors_middleware(app):
    if not settings.cors_enabled:
        return app

    # Parse and clean CORS origins
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    
    # If enabled but empty, stay locked (do NOT allow "*")
    if not origins:
        origins = []

    # Add CORS middleware with specified settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["X-API-Key", "Content-Type"],
        max_age=600,
    )
    return app
