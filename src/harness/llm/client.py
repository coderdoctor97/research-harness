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
    """Public API: __init__(base_url, model_name, api_key_env=..., api_key=...)

    Works with any OpenAI-compatible endpoint (local or cloud). The API key
    can be supplied directly (`api_key`) or resolved from an env var name
    (`api_key_env`); a direct key wins over the env var.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model_name: str = "llama3",
        api_key_env: str = "none",
        timeout: float = 30.0,
        api_key: str | None = None,
        max_tokens: int | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.api_key_env = api_key_env
        self.api_key = api_key
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.client = httpx.Client(timeout=timeout)

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Content-Type": "application/json"}
        val = ""
        if getattr(self, "api_key", None):
            val = self.api_key
        elif self.api_key_env and self.api_key_env != "none":
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
        # BF-014: cap output tokens when the user has configured a ceiling.
        # `max_tokens` is the widely-supported OpenAI-compatible field.
        if getattr(self, "max_tokens", None):
            payload["max_tokens"] = self.max_tokens
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

    def list_models(self) -> list[dict]:
        """Fetch available models from the configured base_url."""
        url = f"{self.base_url}/models"
        try:
            r = self.client.get(url, headers=self._headers())
            r.raise_for_status()
        except httpx.ConnectError as exc:
            raise LLMConnectionError(f"Connection refused: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise LLMConnectionError(f"Timeout: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMResponseError(f"HTTP {exc.response.status_code}") from exc
        data = r.json()
        models = data.get("data", [])
        return [{"id": m.get("id", ""), "name": m.get("id", ""), "owned_by": m.get("owned_by", "")} for m in models]

    def stream_chat(self, message: str):
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": message}],
            "stream": True,
        }
        if getattr(self, "max_tokens", None):
            payload["max_tokens"] = self.max_tokens
        try:
            r = self.client.post(url, json=payload, headers=self._headers(), timeout=self.timeout + 60)
            r.raise_for_status()
        except httpx.ConnectError as exc:
            raise LLMConnectionError(f"Connection refused: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise LLMConnectionError(f"Timeout: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMResponseError(f"HTTP {exc.response.status_code}") from exc
        full_text = ""
        for line in r.text.splitlines():
            line = line.strip()
            if line.startswith("data: "):
                chunk = line[6:]
                if chunk == "[DONE]":
                    break
                try:
                    import json
                    obj = json.loads(chunk)
                    delta = obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    full_text += delta
                    yield delta
                except (json.JSONDecodeError, IndexError):
                    continue
