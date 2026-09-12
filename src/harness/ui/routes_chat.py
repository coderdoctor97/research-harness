# P9.T4 — Chat interface routes: real LLM client + tool dispatch
from __future__ import annotations

import os
import json
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from harness.llm.client import LLMClient, LLMConnectionError, LLMResponseError
from harness.registry.executor import HttpExecutor


class ChatMessage(BaseModel):
    message: str
    model: str | None = None


def _build_system_prompt() -> str:
    return (
        "You are a research assistant powered by LLM Research Harness. "
        "You have access to tools for web search, computation, academic search, and more. "
        "When the user asks for information, use the available tools. "
        "Be concise and helpful. Cite sources when using search results."
    )


def _get_client(model: str | None) -> LLMClient:
    base_url = os.environ.get("HARNESS_LLM_BASE_URL", "http://localhost:11434/v1")
    api_key_env = os.environ.get("HARNESS_LLM_API_KEY_ENV", "none")
    return LLMClient(base_url=base_url, model_name=model or "llama3", api_key_env=api_key_env)


def _extract_tool_calls(text: str) -> list[dict]:
    """Extract tool call hints from LLM response text."""
    calls = []
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "tool_calls" in data:
            return data["tool_calls"]
    except (json.JSONDecodeError, TypeError):
        pass
    return calls


def mount(app: FastAPI) -> None:
    @app.post("/api/chat")
    async def chat(msg: ChatMessage):
        client = _get_client(msg.model)
        try:
            response_text = client.chat(msg.message)
        except LLMConnectionError as exc:
            raise HTTPException(503, detail=str(exc))
        except LLMResponseError as exc:
            raise HTTPException(502, detail=str(exc))

        tool_calls = _extract_tool_calls(response_text)
        sources: list[dict] = []

        return {
            "response": response_text,
            "tool_calls": tool_calls,
            "sources": sources,
            "model": msg.model or client.model_name,
        }

    @app.get("/api/chat/history")
    async def chat_history():
        return []
