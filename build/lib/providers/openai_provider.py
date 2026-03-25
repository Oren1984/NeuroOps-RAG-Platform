# src/providers/openai_provider.py
# OpenAI LLM provider implementation for the RAG Agent Kit application.

import requests
from src.providers.base import LLMProvider
from src.core.settings import settings

# OpenAI LLM provider class to generate
class OpenAIProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        if not settings.openai_api_key:
            return f"[openai-stub] {prompt}"

        # Call OpenAI API to get response
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.openai_chat_model,
            "messages": [
                {"role": "system", "content": "You are a helpful RAG agent. Use provided context only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        # Call OpenAI API to get response
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
