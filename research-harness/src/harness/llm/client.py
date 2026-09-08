"""LLM Client — OpenAI-compatible chat completions."""
from __future__ import annotations

import os
from typing import Any

import httpx


class LLMConnectionError(Exception):
    pass


class LLMResponseError(Exception):
    pass


class LLMClient:
    """Public API: __init__(base_url, model_name, api_key_env=...)"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model_name: str = "llama3",
        api_key_env: str = "none",
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.api_key_env = api_key_env
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key_env and self.api_key_env != "none":
            val = os.environ.get(self.api_key_env, "")
            if val:
                h["Authorization"] = f"Bearer {val}"
        return h

    def chat(self, message: str) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": message}],
            "stream": False,
        }
        try:
            r = self.client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
        except httpx.ConnectError as exc:
            raise LLMConnectionError(f"Connection refused: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise LLMConnectionError(f"Timeout: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMResponseError(f"HTTP {exc.response.status_code}") from exc
        data = r.json()
        choices = data.get("choices", [])
        if not choices:
            raise LLMResponseError("Empty choices in response")
        return choices[0].get("message", {}).get("content", "")
