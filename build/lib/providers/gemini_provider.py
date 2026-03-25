# src/providers/gemini_provider.py
# Gemini LLM provider implementation for the RAG Agent Kit application.

import requests
from src.providers.base import LLMProvider
from src.core.settings import settings

# Gemini LLM provider class to generate
class GeminiProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        if not settings.gemini_api_key:
            return f"[gemini-stub] {prompt}"

        # Google Generative Language API (v1beta)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
        payload = {
            "contents": [
                {"parts": [{"text": "You are a helpful RAG agent. Use provided context only.\n\n" + prompt}]}
            ],
            "generationConfig": {"temperature": 0.2},
        }
        
        # Call Gemini API to get response
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
