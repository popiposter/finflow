"""Minimal Ollama API client for structured chat completions."""

from __future__ import annotations

import json

import httpx

from app.core.config import settings


class OllamaClient:
    """HTTP client for Ollama chat completions."""

    def __init__(self) -> None:
        self.base_url = settings.ollama_api_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_seconds
        self.api_key = settings.ollama_api_key

    async def chat(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Call the Ollama chat API and return assistant text content."""
        headers: dict[str, str] = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat",
                headers=headers,
                content=json.dumps(payload),
            )
            response.raise_for_status()
            data = response.json()

        message = data.get("message", {})
        content = message.get("content")
        if not isinstance(content, str):
            raise ValueError("Ollama response did not contain text content")
        return content
