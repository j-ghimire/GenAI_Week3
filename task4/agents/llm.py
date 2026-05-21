import os
from typing import Optional

import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


class LLM:
    """Wrapper for Google AI Studio (Gemini) using v1beta endpoint with x-goog-api-key header."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or GEMINI_MODEL

    def generate(self, system: str, user: str, temperature: float = 0.0, max_tokens: int = 800) -> str:
        """Generate text using Gemini API with x-goog-api-key header (working approach from task3)."""
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY not set")

        prompt = f"System:\n{system}\n\nUser:\n{user}"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": float(temperature),
                "maxOutputTokens": int(max_tokens),
            },
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
        except Exception as exc:
            raise RuntimeError(f"Gemini request failed: {response.status_code} {response.text}") from exc

        data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini returned no text candidate")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise RuntimeError("Gemini response missing content parts")
        return "".join([part.get("text", "") for part in parts]).strip()
