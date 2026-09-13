# E2.1 — Shared orchestration core (§4 Steps 1-7)
from __future__ import annotations

import asyncio
import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from harness.citations.pipeline import finalize
from harness.citations.registry import SourceRegistry
from harness.loop.dispatcher import async_dispatch
from harness.loop.parser import CallType, ToolCall, classify, clean_final_text, extract_tool_calls
from harness.loop.prompts import build_system_prompt
from harness.loop.recovery import correction_prompt
from harness.memory.assembler import build_context
from harness.memory.budget import compute
from harness.memory.dedup import DedupCache
from harness.memory.doccache import DocumentCache
from harness.registry.index import ToolRegistry
from harness.registry.tool import ToolResult

FORCE_FINAL_PROMPT = (
    "You now have all the information needed. Provide your final answer to the "
    "user in plain text with citations. Do NOT request any more tools."
)


@dataclass
class LoopState:
    messages: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 8
    strike_count: int = 0
    done: bool = False
    final_answer: str = ""

    def step(self, response_text: str) -> dict:
        """Process one model response; return event dict."""
        ctype, payload = classify(response_text)
        if ctype == CallType.FINAL_ANSWER:
            self.done = True
            self.final_answer = payload if isinstance(payload, str) else ""
            return {"type": "final_answer", "text": self.final_answer}
        if ctype == CallType.TOOL_CALL:
            tc = payload
            if self.iteration >= self.max_iterations:
                return {"type": "force_final", "text": response_text}
            self.iteration += 1
            return {"type": "tool_call", "name": tc.name, "arguments": tc.arguments}
        self.strike_count += 1
        if self.strike_count >= 5:
            self.done = True
            return {"type": "tools_off", "text": "I cannot answer with the available tools."}
        return {"type": "malformed", "strikes": self.strike_count}


async def run_chat(
    client: Any,
    registry: ToolRegistry,
    message: str,
    *,
    history: list[dict] | None = None,
    source_registry: SourceRegistry | None = None,
    max_tool_rounds: int = 3,
    max_parallel: int = 4,
    per_call_timeout: float = 30.0,
    context_window: int | None = None,
    citation_config: dict | None = None,
    fallback_to_training: bool = True,
    document_cache: DocumentCache | None = None,
) -> dict:
    """Run plan.md §4 Steps 1-7 once for CLI/UI parity."""
    sources = source_registry or SourceRegistry()
    turns = list(history or []) + [{"role": "user", "content": message}]
    tool_calls_seen: list[dict] = []
    documents: list[dict] = []
    response_text = ""
    model_name = getattr(client, "model_name", "llama3")
    system_prompt = build_system_prompt(registry, _citation_rules(), fallback_to_training, model_name)

    tool_round = 0
    malformed = 0
    seen_results = DedupCache()
    while True:
        prompt, context_report = _assemble_prompt(system_prompt, turns, documents, context_window)
        response_text = await _chat(client, prompt)
        calls = extract_tool_calls(response_text)
        ctype, _ = classify(response_text)

        if not calls and ctype == CallType.MALFORMED:
            malformed += 1
            turns.append({"role": "assistant", "content": response_text})
            turns.append({"role": "system", "content": correction_prompt(malformed)})
            if malformed >= 5:
                response_text = await _chat(
                    client,
                    _assemble_prompt(system_prompt, turns, documents, context_window)[0],
                )
                final, report = finalize(clean_final_text(response_text), sources, citation_config)
                return _result(final, tool_calls_seen, sources, model_name, report, context_report)
            continue
        if not calls:
            clean = clean_final_text(response_text)
            final, report = finalize(clean, sources, citation_config)
            return _result(final, tool_calls_seen, sources, model_name, report, context_report)

        turns.append({"role": "assistant", "content": response_text})
        if tool_round >= max_tool_rounds:
            turns.append({"role": "system", "content": FORCE_FINAL_PROMPT})
            response_text = await _chat(
                client,
                _assemble_prompt(system_prompt, turns, documents, context_window)[0],
            )
            final, report = finalize(clean_final_text(response_text), sources, citation_config)
            return _result(final, tool_calls_seen, sources, model_name, report, context_report)

        normalized = [_call_dict(call) for call in calls[:max_parallel]]
        tool_calls_seen.extend(normalized)
        results = await _dispatch_with_cache(
            registry, normalized, seen_results, max_parallel, per_call_timeout
        )
        for call, result in zip(normalized, results, strict=False):
            payload = _tool_payload(result)
            _register_sources(sources, call["name"], payload, tool_round)
            documents.extend(_documents_from_payload(payload, document_cache))
            turns.append({"role": "tool", "content": json.dumps(payload, ensure_ascii=False), "name": call["name"]})
        if sources.all():
            turns.append({"role": "system", "content": sources.reference_table()})
        tool_round += 1


async def run_chat_stream(
    client: Any,
    registry: ToolRegistry,
    message: str,
    *,
    history: list[dict] | None = None,
    source_registry: SourceRegistry | None = None,
    max_tool_rounds: int = 3,
    max_parallel: int = 4,
    per_call_timeout: float = 30.0,
    context_window: int | None = None,
    citation_config: dict | None = None,
    fallback_to_training: bool = True,
    document_cache: DocumentCache | None = None,
):
    """Yield token/tool/final events through the shared core; streaming is opt-in."""
    sources = source_registry or SourceRegistry()
    turns = list(history or []) + [{"role": "user", "content": message}]
    tool_calls_seen: list[dict] = []
    documents: list[dict] = []
    model_name = getattr(client, "model_name", "llama3")
    system_prompt = build_system_prompt(registry, _citation_rules(), fallback_to_training, model_name)
    tool_round = 0
    malformed = 0
    seen_results = DedupCache()

    while True:
        prompt, context_report = _assemble_prompt(system_prompt, turns, documents, context_window)
        response_text = ""
        async for token in _stream_response(client, prompt):
            response_text += token
            yield {"type": "token", "text": token}

        calls = extract_tool_calls(response_text)
        ctype, _ = classify(response_text)
        if not calls and ctype == CallType.MALFORMED:
            malformed += 1
            turns.append({"role": "assistant", "content": response_text})
            turns.append({"role": "system", "content": correction_prompt(malformed)})
            if malformed >= 5:
                continue
            continue
        if not calls:
            final, report = finalize(clean_final_text(response_text), sources, citation_config)
            yield {"type": "final", **_result(final, tool_calls_seen, sources, model_name, report, context_report)}
            return

        turns.append({"role": "assistant", "content": response_text})
        if tool_round >= max_tool_rounds:
            turns.append({"role": "system", "content": FORCE_FINAL_PROMPT})
            continue

        normalized = [_call_dict(call) for call in calls[:max_parallel]]
        tool_calls_seen.extend(normalized)
        for call in normalized:
            yield {"type": "tool_call", **call}
        results = await _dispatch_with_cache(
            registry, normalized, seen_results, max_parallel, per_call_timeout
        )
        for call, result in zip(normalized, results, strict=False):
            payload = _tool_payload(result)
            _register_sources(sources, call["name"], payload, tool_round)
            documents.extend(_documents_from_payload(payload, document_cache))
            turns.append({"role": "tool", "content": json.dumps(payload, ensure_ascii=False), "name": call["name"]})
            yield {"type": "tool_result", "name": call["name"], "result": payload}
        if sources.all():
            turns.append({"role": "system", "content": sources.reference_table()})
        tool_round += 1


async def _dispatch_with_cache(
    registry: ToolRegistry,
    calls: list[dict],
    seen_results: DedupCache,
    max_parallel: int,
    per_call_timeout: float,
) -> list[ToolResult]:
    results: list[ToolResult | None] = [None] * len(calls)
    pending: list[dict] = []
    pending_slots: list[tuple[int, str]] = []
    for index, call in enumerate(calls):
        arguments = call.get("arguments") or {}
        cached = seen_results.get(call["name"], arguments)
        if cached is None:
            pending.append(call)
            pending_slots.append((index, call["name"]))
            continue
        meta = dict(cached.meta or {})
        meta.update({"cached": True, "note": "This query was already executed. Returning cached result."})
        results[index] = ToolResult(ok=cached.ok, data=cached.data, error=cached.error, meta=meta)

    for (index, _name), result in zip(
        pending_slots,
        await async_dispatch(registry, pending, max_parallel, per_call_timeout),
        strict=False,
    ):
        call = calls[index]
        results[index] = result
        seen_results.put(call["name"], call.get("arguments") or {}, result)
    return [result for result in results if result is not None]


def _assemble_prompt(
    system_prompt: str,
    turns: list[dict],
    documents: list[dict],
    context_window: int | None,
) -> tuple[str, dict]:
    budget = compute(context_window=context_window) if context_window else None
    return build_context(system_prompt, turns, documents, budget)


async def _chat(client: Any, prompt: str) -> str:
    return await asyncio.to_thread(client.chat, prompt)


def _call_dict(call: dict | ToolCall) -> dict:
    if isinstance(call, ToolCall):
        return {"name": call.name, "arguments": call.arguments or {}}
    return {"name": call.get("name", ""), "arguments": call.get("arguments") or {}}


def _tool_payload(result: ToolResult | dict) -> dict:
    if isinstance(result, ToolResult):
        return {"ok": result.ok, "data": result.data, "error": result.error, "meta": result.meta}
    return result


def _documents_from_payload(payload: dict, document_cache: DocumentCache | None) -> list[dict]:
    encoded = json.dumps(payload, ensure_ascii=False)[:6000]
    documents = [{"content": encoded}]
    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    items = data.get("results", []) if isinstance(data, dict) else []
    for item in items:
        if not isinstance(item, dict) or not item.get("url"):
            continue
        url = item["url"]
        content = item.get("content") or item.get("snippet") or item.get("abstract") or ""
        if not content:
            continue
        cached = document_cache.get(url) if document_cache else None
        doc = cached or {"url": url, "title": item.get("title", url), "content": content}
        if document_cache and cached is None:
            document_cache.set(url, dict(doc))
        documents.append(doc)
    return documents


def _register_sources(registry: SourceRegistry, tool_name: str, payload: dict, turn: int) -> None:
    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    for item in data.get("results", []) if isinstance(data, dict) else []:
        if isinstance(item, dict) and item.get("url"):
            registry.add(
                item.get("title") or item["url"],
                item["url"],
                tool_name,
                turn,
                item.get("snippet") or item.get("abstract") or "",
            )


def _result(
    response: str,
    tool_calls: list[dict],
    sources: SourceRegistry,
    model: str,
    report: dict,
    context_report: dict,
) -> dict:
    return {
        "response": response,
        "tool_calls": tool_calls,
        "sources": [s.__dict__ for s in sources.all()],
        "model": model,
        "report": report,
        "context": context_report,
    }


_DONE = object()


def _next_token(tokens: Iterator[str]) -> str | object:
    try:
        return next(tokens)
    except StopIteration:
        return _DONE


async def _stream_response(client: Any, prompt: str):
    tokens = client.stream_chat(prompt)
    while True:
        token = await asyncio.to_thread(_next_token, tokens)
        if token is _DONE:
            return
        yield token


def _citation_rules() -> str:
    return "Cite retrieved sources with [n] matching the provided source numbers."
