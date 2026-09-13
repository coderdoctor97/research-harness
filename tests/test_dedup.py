# P10.T4 — Dedup cache tests
from __future__ import annotations

from typing import ClassVar

import pytest

from harness.memory.dedup import DedupCache, params_hash
from harness.registry.tool import Tool, ToolResult


def test_params_hash_deterministic():
    assert params_hash({"query": "AI"}) == params_hash({"query": "AI"})


def test_params_hash_differs():
    assert params_hash({"query": "AI"}) != params_hash({"query": "ML"})


def test_dedup_cache_hit():
    cache = DedupCache()
    r1 = ToolResult(ok=True, data="result1")
    cache.put("web_search", {"query": "AI"}, r1)
    cached = cache.get("web_search", {"query": "AI"})
    assert cached is r1


def test_dedup_cache_miss():
    cache = DedupCache()
    assert cache.get("web_search", {"query": "AI"}) is None


def test_dedup_cache_clear():
    cache = DedupCache()
    r1 = ToolResult(ok=True, data="x")
    cache.put("t", {"a": 1}, r1)
    cache.clear()
    assert cache.get("t", {"a": 1}) is None


class _CountingTool(Tool):
    name = "counting"
    description = "Count invocations"
    parameters: ClassVar[dict] = {"query": {"type": "string"}}

    def __init__(self):
        self.calls = 0

    def run(self, **params):
        self.calls += 1
        return ToolResult(ok=True, data={"calls": self.calls, "query": params.get("query")})


class _ScriptedClient:
    model_name = "scripted-model"

    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []

    def chat(self, prompt):
        self.prompts.append(prompt)
        return self.replies.pop(0)


@pytest.mark.asyncio
async def test_core_run_chat_uses_memory_dedup_cache():
    from harness.loop.agent import run_chat
    from harness.registry.index import ToolRegistry

    tool = _CountingTool()
    registry = ToolRegistry()
    registry.register(tool)
    client = _ScriptedClient([
        '{"tool_calls": [{"name": "counting", "arguments": {"query": "same"}}]}',
        '{"tool_calls": [{"name": "counting", "arguments": {"query": "same"}}]}',
        "done",
    ])

    result = await run_chat(client, registry, "dedupe please")

    assert result["response"] == "done"
    assert tool.calls == 1
    assert "Returning cached result" in client.prompts[2]
