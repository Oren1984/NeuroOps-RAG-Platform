# src/providers/anthropic_provider.py
# Anthropic LLM provider implementation for the RAG Agent Kit application.

import requests
from src.providers.base import LLMProvider
from src.core.settings import settings

# Anthropic LLM provider class to generate
class AnthropicProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        if not settings.anthropic_api_key:
            return f"[anthropic-stub] {prompt}"

        # Call Anthropic API to get completion
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": settings.anthropic_model,
            "max_tokens": 800,
            "temperature": 0.2,
            "system": "You are a helpful RAG agent. Use provided context only.",
            "messages": [{"role": "user", "content": prompt}],
        }

        # Call Anthropic API to get response
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()

        # Anthropic returns list content blocks
        parts = data.get("content", [])
        if parts and isinstance(parts, list) and "text" in parts[0]:
            return parts[0]["text"]
        return str(data)
