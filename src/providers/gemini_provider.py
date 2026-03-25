# src/providers/gemini_provider.py
# Gemini LLM provider for the NeuroOps Agent Platform.

from src.providers.base import LLMProvider, _post_with_retry
from src.core.settings import settings


class GeminiProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        if not settings.gemini_api_key:
            return f"[gemini-stub] {prompt}"

        url = (
            f"https://generativelanguage.googleapis.com/v1beta"
            f"/models/{settings.gemini_model}:generateContent"
            f"?key={settings.gemini_api_key}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "You are a helpful RAG agent. "
                                "Use provided context only.\n\n" + prompt
                            )
                        }
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.2},
        }

        r = _post_with_retry(
            url,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
            json=payload,
        )
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
