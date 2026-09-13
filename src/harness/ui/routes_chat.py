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

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from harness.llm.client import LLMClient, LLMConnectionError, LLMResponseError
from harness.mcp.builtin import BUILTIN_SERVERS
from harness.ui import _chat_state
from harness.ui._ai_state import get_state, update_state

MAX_TOOL_ROUNDS = 3


class ChatMessage(BaseModel):
    message: str
    model: str | None = None
    session_id: str | None = None


class InspectMessage(BaseModel):
    """U2.3 — reactive text inspection payload (Define / Break down)."""

    phrase: str
    context: str = ""
    sources: list[dict] = []
    mode: str = "define"  # "define" | "breakdown"
    model: str | None = None


_MAX_INSPECT_PHRASE = 300
_MAX_INSPECT_CONTEXT = 4000


def _inspect_transcript(msg: InspectMessage, sources: list[dict]) -> str:
    # ponytail: single hop, no tool rounds — A2's multi-query research workflow
    # is not built yet (AI plan, in flight separately). Upgrade path: route
    # mode="breakdown" through the A2 workflow once E2.3/A3 freeze their APIs.
    phrase = msg.phrase.strip()[:_MAX_INSPECT_PHRASE]
    context = (msg.context or "").strip()[:_MAX_INSPECT_CONTEXT]
    if sources:
        ref = "\n".join(
            f"[{i}] {s.get('title') or s.get('url') or 'source'} — {s.get('url') or ''}"
            for i, s in enumerate(sources, 1)
        )
    else:
        ref = "(none — do not use [n] markers)"
    if msg.mode == "breakdown":
        task = (
            f'Give a deeper contextual breakdown of the phrase "{phrase}" within '
            "the passage below: what it means here, why it matters, and the key "
            "sub-points. 120-260 words, plain markdown, no preamble. Cite a "
            "source as [n] only when the claim comes from the numbered reference "
            "list."
        )
    else:
        task = (
            f'Define the phrase "{phrase}" as it is used in the passage below. '
            "2-4 sentences, plain markdown, no preamble. Cite a source as [n] "
            "only when the reference list actually supports the definition."
        )
    return (
        "You are the inspection lens of a research assistant: you answer "
        "questions about one phrase the user selected from a previous answer, "
        "grounded in that answer's context.\n\n"
        f"Selected phrase: {phrase}\n\n"
        f"Reference sources from that answer:\n{ref}\n\n"
        f"Passage:\n{context or '(none provided)'}\n\n"
        f"Task: {task}"
    )


def _tool_docs() -> str:
    lines = []
    for server in BUILTIN_SERVERS.values():
        for tool in server.list_tools():
            params = ", ".join(tool.get("inputSchema", {}).get("properties", {}).keys())
            lines.append(f"- {tool['name']}({params}): {tool['description']} [server: {server.name}]")
    return "\n".join(lines)


def _build_system_prompt() -> str:
    return (
        "You are a research assistant powered by LLM Research Harness. "
        "You can browse the web using the built-in tools below.\n\n"
        "Available tools:\n" + _tool_docs() + "\n\n"
        "When you need a tool, reply with a tool call in ONE of these forms:\n"
        '  {"tool_calls": [{"name": "<tool>", "arguments": { ... }}]}\n'
        '  <tool_call>{"name": "<tool>", "arguments": { ... }}</tool_call>\n\n'
        "After the tool results are provided, answer the user's question in plain "
        "text and cite the sources (title + URL) you used. Do NOT include the "
        "tool-call markup or JSON in your final answer. Be concise."
    )


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
    except Exception:
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


def _maybe_resolve_model(client: LLMClient, explicit_model: str | None) -> None:
    if explicit_model or not isinstance(client, LLMClient):
        return
    if get_state().get("model"):
        return
    discovered = _discover_model(client)
    if discovered:
        update_state(model=discovered)
        client.model_name = discovered


_TOOL_BLOCK_RE = re.compile(r"<\s*/?\s*(?:antml:)?tool_call\s*>", re.IGNORECASE)
_TOOL_BLOCK_PAIR_RE = re.compile(
    r"<\s*(?:antml:)?tool_call\s*>.*?<\s*/\s*(?:antml:)?tool_call\s*>",
    re.IGNORECASE | re.DOTALL,
)


def _extract_tool_calls(text: str) -> list[dict]:
    """Extract tool call requests from LLM output (bugfix.json BF-013).

    Tolerates: pure JSON, JSON wrapped in <tool_call>…</tool_call> tags,
    fenced code blocks, surrounding prose, multiple separate blocks, and the
    single-call shorthand {"name": …, "arguments": …}.
    """
    found: list[dict] = []

    def _accept(data: object) -> bool:
        if not isinstance(data, dict):
            return False
        if isinstance(data.get("tool_calls"), list):
            calls = [c for c in data["tool_calls"] if isinstance(c, dict) and c.get("name")]
            if calls:
                found.extend(calls)
                return True
        if data.get("name") and "arguments" in data:  # single-call shorthand
            found.append({"name": data["name"], "arguments": data.get("arguments") or {}})
            return True
        return False

    try:
        if _accept(json.loads(text)):
            return found
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    # Scan every '{' and parse the JSON object that starts there — this finds
    # tool-call JSON no matter what tags/prose/markdown wraps it.
    decoder = json.JSONDecoder()
    idx = text.find("{")
    while idx != -1 and len(found) < 8:
        try:
            data, end = decoder.raw_decode(text, idx)
        except ValueError:
            idx = text.find("{", idx + 1)
            continue
        idx = text.find("{", end) if _accept(data) else text.find("{", idx + 1)
    return found


def _strip_tool_call_json(text: str) -> str:
    """Remove any raw JSON tool-call payloads (the model sometimes emits the
    tool call as its whole reply, or repeats it inside its final answer).

    Handles both forms: {"tool_calls":[{...}]} and the single-call shorthand
    {"name": ..., "arguments": {...}} — even when buried in prose/XML tags.
    """
    decoder = json.JSONDecoder()
    out = text
    idx = out.find("{")
    while idx != -1:
        try:
            data, end = decoder.raw_decode(out, idx)
        except ValueError:
            idx = out.find("{", idx + 1)
            continue
        is_tool = False
        if isinstance(data, dict):
            calls = data.get("tool_calls")
            if isinstance(calls, list) and any(
                isinstance(c, dict) and c.get("name") for c in calls
            ):
                is_tool = True
            elif data.get("name") and "arguments" in data:
                is_tool = True
        if is_tool:
            out = out[:idx] + out[end:]
            idx = out.find("{")
        else:
            idx = out.find("{", idx + 1)
    return out


def _clean_final_text(text: str) -> str:
    """Strip every trace of tool-call markup so it never leaks into the reply.

    1. Drop whole <tool_call>…</tool_call> blocks (tags + inner JSON).
    2. Drop any stray opening/closing tags.
    3. Drop any raw tool-call JSON payloads.
    """
    if not text:
        return ""
    cleaned = _TOOL_BLOCK_PAIR_RE.sub("", text)
    cleaned = _TOOL_BLOCK_RE.sub("", cleaned)
    cleaned = _strip_tool_call_json(cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _fit_context(lines: list[str], context_window: int | None) -> list[str]:
    """BF-014: trim the transcript so it fits within `context_window` tokens.

    Always keeps the system prompt + user message, then keeps the most recent
    assistant/tool lines. Uses a ~4 chars-per-token heuristic. Returns the
    original list untouched when no context_window is set.
    """
    if not context_window or context_window <= 0:
        return lines
    budget = context_window * 4
    head = lines[:2]
    head_cost = sum(len(l) for l in head)
    if head_cost >= budget:
        # Even the prompt alone is over budget — keep it but cap each piece.
        head = [l[: max(1, budget // 2)] for l in head]
        return head
    remaining = budget - head_cost
    kept: list[str] = []
    for line in reversed(lines[2:]):
        if remaining <= 0:
            break
        if len(line) > remaining:
            kept.append(line[:remaining])
            remaining = 0
        else:
            kept.append(line)
            remaining -= len(line)
    kept.reverse()
    return head + kept


async def _run_tool(name: str, arguments: dict) -> dict:
    for server in BUILTIN_SERVERS.values():
        if name in {t["name"] for t in server.list_tools()}:
            return await server.call_tool(name, arguments)
    return {"ok": False, "error": f"unknown tool: {name}"}


def _run_tool_sync(name: str, arguments: dict) -> dict:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_run_tool(name, arguments))
    # Inside a running loop (FastAPI route) → create + run the coroutine on a
    # side thread so it isn't tied to the caller's loop.
    import concurrent.futures

    def _runner():
        return asyncio.run(_run_tool(name, arguments))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(_runner).result()


def mount(app: FastAPI) -> None:
    async def _handle_chat(msg: ChatMessage, allow_model_retry: bool) -> dict:
        client = _get_client(msg.model)
        _maybe_resolve_model(client, msg.model)  # BF-011: discover+persist if unset
        transcript = [
            f"[system] {_build_system_prompt()}",
            f"[user] {msg.message}",
        ]
        tool_calls_seen: list[dict] = []
        sources: list[dict] = []
        response_text = ""
        context_window = get_state().get("context_window") or None

        for _round in range(MAX_TOOL_ROUNDS + 1):
            try:
                response_text = client.chat(
                    "\n\n".join(_fit_context(transcript, context_window))
                )
            except LLMConnectionError as exc:
                raise HTTPException(
                    503,
                    detail=f"Cannot reach the AI endpoint: {exc} — open “02 · AI Provider”, "
                           "enter your base URL + API key, press Test, then Save as default.",
                )
            except LLMResponseError as exc:
                # BF-011: stale saved model (provider deprecated it) → forget
                # it, rediscover from the endpoint, retry once.
                if allow_model_retry and not msg.model and "404" in str(exc):
                    update_state(model="")
                    return await _handle_chat(msg, allow_model_retry=False)
                raise HTTPException(502, detail=str(exc))

            calls = _extract_tool_calls(response_text)
            if not calls:
                break  # a clean answer — done
            if _round == MAX_TOOL_ROUNDS:
                # BF-014: the model kept asking for tools right up to the cap.
                # Run them one last time, then insist on a final answer instead
                # of surfacing raw markup / the empty-answer fallback.
                transcript.append(f"[assistant] {response_text}")
                for call in calls[:4]:
                    name = call.get("name", "")
                    arguments = call.get("arguments", {}) or {}
                    tool_calls_seen.append({"name": name, "arguments": arguments})
                    result = _run_tool_sync(name, arguments)
                    if isinstance(result, dict) and result.get("ok") and name == "web_search":
                        sources.extend(result.get("results", [])[:5])
                    transcript.append(
                        f"[tool:{name}] {json.dumps(result, ensure_ascii=False)[:6000]}"
                    )
                transcript.append(
                    "[system] You now have all the information needed. Provide your "
                    "final answer to the user in plain text with citations. Do NOT "
                    "request any more tools."
                )
                try:
                    response_text = client.chat(
                        "\n\n".join(_fit_context(transcript, context_window))
                    )
                except (LLMConnectionError, LLMResponseError):
                    pass
                break

            transcript.append(f"[assistant] {response_text}")
            for call in calls[:4]:
                name = call.get("name", "")
                arguments = call.get("arguments", {}) or {}
                tool_calls_seen.append({"name": name, "arguments": arguments})
                result = _run_tool_sync(name, arguments)
                if isinstance(result, dict) and result.get("ok") and name == "web_search":
                    sources.extend(result.get("results", [])[:5])
                transcript.append(
                    f"[tool:{name}] {json.dumps(result, ensure_ascii=False)[:6000]}"
                )

        # Persist into the sidebar session history.
        session = _chat_state.get_session(msg.session_id) if msg.session_id else None
        if session is None:
            session = _chat_state.create_session(msg.message)
        _chat_state.append_message(session, {"role": "user", "content": msg.message, "ts": time.time()})
        used_model = msg.model or client.model_name
        final_text = _clean_final_text(response_text)
        if not final_text:
            # The model only ever emitted tool calls and never produced a clean
            # answer — surface a friendly note instead of raw markup/JSON.
            final_text = (
                "I gathered information with my browsing tools, but couldn't "
                "produce a clean summary this time. Please try rephrasing the "
                "question."
            )
        _chat_state.append_message(session, {
            "role": "assistant",
            "content": final_text,
            "tool_calls": tool_calls_seen,
            "sources": sources,
            "model": used_model,
            "ts": time.time(),
        })

        return {
            "response": final_text,
            "tool_calls": tool_calls_seen,
            "sources": sources,
            "model": used_model,
            "session_id": session["id"],
        }

    @app.post("/api/chat")
    async def chat(msg: ChatMessage):
        return await _handle_chat(msg, allow_model_retry=True)

    @app.post("/api/chat/inspect")
    async def inspect(msg: InspectMessage):
        # U2.3: single-hop inspection. BF-008-safe by construction (no async
        # tools — the sync client only, same call shape as /api/chat) and
        # reuses the saved-provider state (get_state via _get_client, BF-010).
        # Deliberately NOT persisted into the sidebar session history: the
        # popover is an ephemeral loupe, not part of the conversation.
        if msg.mode not in ("define", "breakdown"):
            raise HTTPException(422, detail="mode must be 'define' or 'breakdown'")
        if not msg.phrase.strip():
            raise HTTPException(422, detail="phrase is required")
        client = _get_client(msg.model)
        _maybe_resolve_model(client, msg.model)  # BF-011: same resolution as chat
        sources = [s for s in msg.sources if isinstance(s, dict)][:5]
        try:
            raw = client.chat(_inspect_transcript(msg, sources))
        except LLMConnectionError as exc:
            raise HTTPException(503, detail=f"Cannot reach the AI endpoint: {exc}")
        except LLMResponseError as exc:
            raise HTTPException(502, detail=str(exc))
        final = _clean_final_text(raw)
        if not final:
            raise HTTPException(502, detail="Empty inspection — the model produced no text. Retry.")
        return {
            "response": final,
            "sources": sources,
            "model": msg.model or client.model_name,
        }

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
