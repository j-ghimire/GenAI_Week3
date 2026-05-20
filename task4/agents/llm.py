import os
from typing import Optional

import requests

from google.oauth2 import service_account
from google.auth.transport.requests import Request

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
SERVICE_ACCOUNT = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")


class LLM:
    """Wrapper for Google AI Studio (Gemini) via REST with optional service-account auth."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.gemini_key = api_key or GEMINI_API_KEY
        self.gemini_model = model or GEMINI_MODEL

    def _get_bearer_token(self) -> Optional[str]:
        # Use service account JSON if provided by GOOGLE_APPLICATION_CREDENTIALS
        sa_path = SERVICE_ACCOUNT
        if sa_path and os.path.exists(sa_path):
            try:
                creds = service_account.Credentials.from_service_account_file(sa_path)
                scoped = creds.with_scopes(["https://www.googleapis.com/auth/cloud-platform"])
                scoped.refresh(Request())
                return scoped.token
            except Exception:
                return None
        return None

    def generate(self, system: str, user: str, temperature: float = 0.0, max_tokens: int = 512) -> str:
        prompt = f"System:\n{system}\n\nUser:\n{user}"

        payload = {
            "prompt": {"text": prompt},
            "temperature": float(temperature),
            "maxOutputTokens": int(max_tokens),
        }

        # Determine auth method: prefer service-account bearer token
        bearer = self._get_bearer_token()
        headers = {}
        use_key_param = False
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        elif self.gemini_key:
            # fallback to API key query param
            use_key_param = True
        else:
            return f"FALLBACK: No Gemini API key or service account configured. System: {system} | User: {user}"

        # Try multiple API versions and action suffixes to handle endpoint differences
        versions = ["v1", "v1beta2"]
        actions = ["generateText", "generate", "predict", "chat"]
        last_err = None
        for version in versions:
            for action in actions:
                if use_key_param:
                    url = f"https://generativelanguage.googleapis.com/{version}/models/{self.gemini_model}:{action}?key={self.gemini_key}"
                else:
                    url = f"https://generativelanguage.googleapis.com/{version}/models/{self.gemini_model}:{action}"
                try:
                    r = requests.post(url, json=payload, headers=headers or None, timeout=30)
                    if r.status_code == 404:
                        last_err = f"404 Not Found for URL: {url}"
                        continue
                    r.raise_for_status()
                    j = r.json()

                    # Common response shapes
                    if isinstance(j, dict):
                        if "candidates" in j and len(j["candidates"]) > 0:
                            return j["candidates"][0].get("output", "").strip()
                        if "output" in j and isinstance(j.get("output"), str):
                            return j.get("output", "").strip()
                        if "responses" in j and len(j["responses"]) > 0:
                            resp = j["responses"][0]
                            if isinstance(resp, dict):
                                for key in ("text", "content", "message", "output"):
                                    if key in resp and isinstance(resp[key], str):
                                        return resp[key].strip()
                        if "predictions" in j and len(j["predictions"]) > 0:
                            p = j["predictions"][0]
                            if isinstance(p, dict):
                                for key in ("content", "text", "output"):
                                    if key in p and isinstance(p[key], str):
                                        return p[key].strip()
                        if "choices" in j and len(j["choices"]) > 0:
                            c = j["choices"][0]
                            if isinstance(c, dict) and "message" in c and isinstance(c["message"], dict):
                                for key in ("content", "text", "output"):
                                    if key in c["message"] and isinstance(c["message"][key], str):
                                        return c["message"][key].strip()

                    return ""
                except Exception as e:
                    last_err = str(e)

        return f"FALLBACK: Gemini request failed: {last_err}"
