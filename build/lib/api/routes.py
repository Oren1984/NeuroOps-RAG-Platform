# src/api/routes.py
# API route definitions for the NeuroOps Agent Platform.

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.core.logging import get_logger
from src.security.auth import require_api_key
from src.core.settings import settings
from src.retrieval.pipeline import answer_question

router = APIRouter()
logger = get_logger(__name__)


# Pydantic model for the ask request payload
class AskRequest(BaseModel):
    question: str


# Health check endpoint
@router.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


# Readiness check endpoint
@router.get("/ready")
def ready():
    ok = bool(settings.rag_api_key and settings.rag_api_key.strip())
    return {"ready": ok, "provider": settings.llm_provider}


# Endpoint to handle question answering
@router.post("/ask")
def ask(payload: AskRequest, request: Request, _=Depends(require_api_key)):
    req_id = getattr(request.state, "request_id", "")
    logger.info(
        "ask",
        extra={"request_id": req_id, "question_len": len(payload.question)},
    )
    result = answer_question(payload.question)
    result["request_id"] = req_id
    return result
