# P9.T4 — Chat interface routes: OpenAI-compatible LLM + built-in tool loop.
#
# Kept deliberately simple: the model may answer directly OR request tools by
# replying with JSON {"tool_calls": [{"name": ..., "arguments": {...}}]}.
# Tool calls run against the built-in free MCP services (endpoint fetcher,
# DuckDuckGo search); results are fed back and the loop continues (bounded).
from __future__ import annotations

import asyncio
import json
import re
import time

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from harness.llm.client import LLMClient, LLMConnectionError, LLMResponseError
from harness.loop.agent import run_chat, run_chat_stream
from harness.mcp.builtin import builtin_tool_registry
from harness.ui import _chat_state
from harness.ui._ai_state import get_state, update_state

MAX_TOOL_ROUNDS = 3


class ChatMessage(BaseModel):
    message: str
    model: str | None = None
    session_id: str | None = None


def _get_client(model: str | None) -> LLMClient:
    import os

    from harness.ui._ai_state import AI_PROVIDER_PRESETS

    state = get_state()
    base_url = state.get("base_url") or "http://localhost:11434/v1"
    api_key = state.get("api_key") or ""
    if not api_key:
        base_url = os.environ.get("HARNESS_LLM_BASE_URL", base_url)

    # Fallback: nothing saved with a key? Resolve from a known AI key the user
    # set in the Keys tab (OPENROUTER_API_KEY, GROQ_API_KEY, …) and infer the
    # matching provider base_url, so chat works without a manual "save".
    if not api_key:
        key_env_to_preset = {
            "OPENROUTER_API_KEY": "openrouter",
            "OPENAI_API_KEY": "openai",
            "GROQ_API_KEY": "groq",
            "TOGETHER_API_KEY": "together",
        }
        for env_name, preset in key_env_to_preset.items():
            value = os.environ.get(env_name, "")
            if value:
                api_key = value
                base_url = AI_PROVIDER_PRESETS[preset]["base_url"]
                break

    return LLMClient(
        base_url=base_url,
        model_name=model or state.get("model") or "llama3",
        api_key_env="HARNESS_LLM_API_KEY" if api_key else "none",
        api_key=api_key or None,
        max_tokens=state.get("max_tokens") or None,
    )


# ---------------------------------------------------------------------------
# BF-011: model auto-discovery. Hardcoded cloud model IDs go stale, so when no
# model is saved we pick one from the endpoint's live /models list, persist
# it, and retry once if a saved model turns out to be a 404.
# ---------------------------------------------------------------------------

_NON_CHAT_RE = re.compile(
    r"(?i)(whisper|embed|guard|tts|orpheus|speech|transcri|moderation|compound|safeguard)"
)


def _discover_model(client: LLMClient) -> str:
    try:
        models = client.list_models()
    except (LLMConnectionError, LLMResponseError):
        return ""
    ids = [m.get("id", "") for m in models if m.get("id")]
    if not ids:
        return ""
    for mid in ids:  # prefer obvious chat models
        if re.search(r"(?i)(instruct|chat|auto|versatile)", mid) and not _NON_CHAT_RE.search(mid):
            return mid
    for mid in ids:  # then anything that isn't a utility model
        if not _NON_CHAT_RE.search(mid):
            return mid
    return ids[0]


async def _maybe_resolve_model(client: LLMClient, explicit_model: str | None) -> None:
    if explicit_model or not isinstance(client, LLMClient):
        return
    if get_state().get("model"):
        return
    discovered = await asyncio.to_thread(_discover_model, client)
    if discovered:
        update_state(model=discovered)
        client.model_name = discovered


def _persist_chat(msg: ChatMessage, result: dict, client: LLMClient) -> dict:
    session = _chat_state.get_session(msg.session_id) if msg.session_id else None
    if session is None:
        session = _chat_state.create_session(msg.message)
    _chat_state.append_message(session, {"role": "user", "content": msg.message, "ts": time.time()})

    final_text = result["response"] or (
        "I gathered information with my browsing tools, but couldn't produce a clean "
        "summary this time. Please try rephrasing the question."
    )
    response = {
        "response": final_text,
        "tool_calls": result.get("tool_calls", []),
        "sources": result.get("sources", []),
        "model": msg.model or client.model_name,
        "session_id": session["id"],
    }
    _chat_state.append_message(session, {
        "role": "assistant",
        "content": final_text,
        "tool_calls": response["tool_calls"],
        "sources": response["sources"],
        "model": response["model"],
        "ts": time.time(),
    })
    return response


def _sse(event: dict) -> str:
    return f"event: {event['type']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"


def mount(app: FastAPI) -> None:
    async def _handle_chat(msg: ChatMessage, allow_model_retry: bool) -> dict:
        client = _get_client(msg.model)
        await _maybe_resolve_model(client, msg.model)  # BF-011: discover+persist if unset
        try:
            result = await run_chat(
                client,
                builtin_tool_registry(),
                msg.message,
                max_tool_rounds=MAX_TOOL_ROUNDS,
                context_window=get_state().get("context_window") or None,
            )
        except LLMConnectionError as exc:
            raise HTTPException(
                503,
                detail=f"Cannot reach the AI endpoint: {exc} — open “02 · AI Provider”, "
                "enter your base URL + API key, press Test, then Save as default.",
            ) from exc
        except LLMResponseError as exc:
            # BF-011: stale saved model (provider deprecated it) → forget it, rediscover, retry once.
            if allow_model_retry and not msg.model and "404" in str(exc):
                update_state(model="")
                return await _handle_chat(msg, allow_model_retry=False)
            raise HTTPException(502, detail=str(exc)) from exc

        return _persist_chat(msg, result, client)

    @app.post("/api/chat")
    async def chat(msg: ChatMessage):
        return await _handle_chat(msg, allow_model_retry=True)

    def _stream_response(msg: ChatMessage) -> StreamingResponse:
        async def events():
            client = _get_client(msg.model)
            await _maybe_resolve_model(client, msg.model)
            try:
                async for event in run_chat_stream(
                    client,
                    builtin_tool_registry(),
                    msg.message,
                    max_tool_rounds=MAX_TOOL_ROUNDS,
                    context_window=get_state().get("context_window") or None,
                ):
                    if event["type"] == "final":
                        event.update(_persist_chat(msg, event, client))
                    yield _sse(event)
            except (LLMConnectionError, LLMResponseError) as exc:
                yield _sse({"type": "error", "error": str(exc)})

        return StreamingResponse(events(), media_type="text/event-stream")

    @app.post("/api/chat/stream")
    async def chat_stream(msg: ChatMessage):
        return _stream_response(msg)

    @app.get("/api/chat/stream")
    async def chat_stream_get(
        message: str = Query(default=""),
        model: str | None = Query(default=None),
        session_id: str | None = Query(default=None),
    ):
        return _stream_response(ChatMessage(message=message, model=model, session_id=session_id))

    @app.get("/api/chat/sessions")
    async def list_sessions():
        return {"sessions": _chat_state.list_sessions()}

    @app.post("/api/chat/sessions")
    async def create_session(payload: dict | None = None):
        title = (payload or {}).get("title", "") if payload else ""
        return {"session": _chat_state.create_session(title)}

    @app.get("/api/chat/sessions/{session_id}")
    async def get_session(session_id: str):
        session = _chat_state.get_session(session_id)
        if session is None:
            raise HTTPException(404, "session not found")
        return {"session": session}

    @app.delete("/api/chat/sessions/{session_id}")
    async def delete_session(session_id: str):
        if not _chat_state.delete_session(session_id):
            raise HTTPException(404, "session not found")
        return {"status": "deleted"}

    @app.get("/api/chat/history")
    async def chat_history():
        return _chat_state.list_sessions()
