from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

import httpx

from ..config import settings


@dataclass
class AIResponse:
    content: str


class AIClient:
    """Simple HTTP client for talking to a local LLM server (e.g. Ollama)."""

    def __init__(self, host: str | None = None, model: str | None = None) -> None:
        self.host = host or settings.DEFAULT_AI_HOST
        self.model = model or settings.DEFAULT_AI_MODEL

    def get_model_name(self) -> str:
        """Get a display-friendly model name."""
        # Extract just the model name without version/size tags
        name = self.model.split(":")[0] if ":" in self.model else self.model
        return name.upper()

    def chat(self, messages: List[Dict[str, str]]) -> AIResponse:
        """Send a chat-style request and return full text response.

        Expected backend: Ollama-compatible /api/chat endpoint.
        """
        url = f"{self.host.rstrip('/')}/api/chat"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"AI request failed: {exc}") from exc

        data = resp.json()
        # Ollama-style: { 'message': { 'content': '...'} }
        if "message" in data and isinstance(data["message"], dict):
            content = data["message"].get("content", "")
        else:
            # Fallback for slightly different schemas
            content = data.get("content", "") or str(data)

        return AIResponse(content=content)
