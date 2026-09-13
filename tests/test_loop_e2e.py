# P4.T6 — E2E loop tests with scripted mock LLM
from __future__ import annotations

import time
from typing import ClassVar

import pytest

from harness.loop.agent import LoopState, run_chat
from harness.loop.parser import CallType, classify
from harness.loop.recovery import correction_prompt
from harness.registry.index import ToolRegistry
from harness.registry.tool import Tool, ToolResult


class EchoTool(Tool):
    name = "echo"
    description = "Echo input"
    parameters: ClassVar[dict] = {"text": {"type": "string"}}

    def run(self, **params):
        return ToolResult(ok=True, data={"echo": params.get("text", "")})


def test_parser_final_answer():
    ctype, payload = classify("Here is the answer.")
    assert ctype == CallType.FINAL_ANSWER
    assert "answer" in payload


def test_parser_tool_call_openai():
    raw = '{"tool_calls": [{"function": {"name": "web_search", "arguments": "{\\"query\\": \\"x\\"}"}}]}'
    ctype, payload = classify(raw)
    assert ctype == CallType.TOOL_CALL
    assert payload.name == "web_search"


def test_parser_tool_call_wrapped_in_xml_tags():
    raw = (
        '<tool_call>{"tool_calls": [{"function": {"name": "web_search", '
        '"arguments": "{\\"query\\": \\"x\\"}"}}]}</tool_call>'
    )
    ctype, payload = classify(raw)
    assert ctype == CallType.TOOL_CALL
    assert payload.name == "web_search"


def test_parser_react_text():
    raw = "Thought: I need to search.\nAction: web_search\nAction Input: {\"query\": \"x\"}"
    ctype, payload = classify(raw)
    assert ctype == CallType.TOOL_CALL
    assert payload.name == "web_search"


def test_parser_malformed():
    ctype, _ = classify("")
    assert ctype == CallType.MALFORMED


def test_loop_iteration_cap():
    state = LoopState(max_iterations=2)
    state.step('{"tool_calls": [{"function": {"name": "echo", "arguments": "{}"}}]}')
    state.step('{"tool_calls": [{"function": {"name": "echo", "arguments": "{}"}}]}')
    evt = state.step('{"tool_calls": [{"function": {"name": "echo", "arguments": "{}"}}]}')
    assert evt["type"] == "force_final"


def test_loop_malformed_strike_count():
    state = LoopState(max_iterations=8)
    for _ in range(4):
        evt = state.step("")  # empty → MALFORMED
        assert evt["type"] == "malformed"
    assert state.strike_count == 4
    evt = state.step("")  # 5th strike → tools_off
    assert evt["type"] == "tools_off"
    assert state.done is True


def test_loop_final_answer():
    state = LoopState()
    evt = state.step("Paris is the capital of France.")
    assert evt["type"] == "final_answer"
    assert state.done is True


def test_correction_prompt_before_5():
    assert "tool call" in correction_prompt(1).lower()


def test_tools_off_after_5():
    p = correction_prompt(5)
    assert "disabled" in p.lower()


def test_parallel_dispatch_timing():
    reg = ToolRegistry()
    reg.register(EchoTool())

    def slow(name):
        time.sleep(0.05)
        return ToolResult(ok=True, data={"echo": name})
    reg.dispatch = lambda name, **kw: slow(name)  # type: ignore

    calls = [{"name": "echo", "arguments": {"text": f"t{i}"}} for i in range(4)]
    t0 = time.time()
    from harness.loop.dispatcher import dispatch
    results = dispatch(reg, calls, max_parallel=4, per_call_timeout=10.0)
    elapsed = time.time() - t0
    assert len(results) == 4
    assert all(r.ok for r in results)
    assert elapsed < 0.3


def test_duplicate_guard():
    from harness.loop.recovery import duplicate_guard_key
    k1 = duplicate_guard_key("echo", {"text": "hi"})
    k2 = duplicate_guard_key("echo", {"text": "hi"})
    k3 = duplicate_guard_key("echo", {"text": "bye"})
    assert k1 == k2
    assert k1 != k3


class SearchTool(Tool):
    name = "web_search"
    description = "Search web"
    parameters: ClassVar[dict] = {"query": {"type": "string"}}

    def run(self, **params):
        return ToolResult(
            ok=True,
            data={
                "results": [
                    {
                        "title": "Harness Note",
                        "url": "https://example.com/harness",
                        "snippet": f"Result for {params.get('query')}",
                    }
                ]
            },
        )


class ScriptedClient:
    model_name = "scripted-model"

    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []

    def chat(self, prompt):
        self.prompts.append(prompt)
        return self.replies.pop(0)


@pytest.mark.asyncio
async def test_run_chat_drives_steps_1_to_7():
    registry = ToolRegistry()
    registry.register(SearchTool())
    client = ScriptedClient([
        '{"tool_calls": [{"name": "web_search", "arguments": {"query": "harness"}}]}',
        "The harness result is useful [1]. https://example.com/harness",
    ])

    result = await run_chat(client, registry, "research harness?")

    assert result["response"].startswith("The harness result")
    assert "## Sources" in result["response"]
    assert result["tool_calls"] == [{"name": "web_search", "arguments": {"query": "harness"}}]
    assert result["sources"][0]["url"] == "https://example.com/harness"
    assert "Available tools" in client.prompts[0]
    assert "Result for harness" in client.prompts[1]
    assert "[Source 1] Harness Note | https://example.com/harness" in client.prompts[1]


@pytest.mark.asyncio
async def test_run_chat_force_final_after_tool_cap():
    registry = ToolRegistry()
    registry.register(EchoTool())
    client = ScriptedClient([
        '{"tool_calls": [{"name": "echo", "arguments": {"text": "again"}}]}',
        "Final after cap.",
    ])

    result = await run_chat(client, registry, "loop", max_tool_rounds=0)

    assert result["response"] == "Final after cap."
    assert "final answer" in client.prompts[-1].lower()


@pytest.mark.asyncio
async def test_run_chat_malformed_tools_off_at_five_strikes():
    client = ScriptedClient(["", "", "", "", "", "Direct fallback answer."])

    result = await run_chat(client, ToolRegistry(), "answer directly")

    assert result["response"] == "Direct fallback answer."
    assert "disabled" in client.prompts[-1].lower()


class SleepTool(Tool):
    name = "sleepy"
    description = "Sleep then return"
    parameters: ClassVar[dict] = {
        "label": {"type": "string"},
        "delay": {"type": "number"},
    }

    def run(self, **params):
        time.sleep(float(params.get("delay", 0)))
        label = params.get("label", "")
        return ToolResult(ok=True, data={"label": label})


@pytest.mark.asyncio
async def test_run_chat_parallel_partial_timeout_injected():
    registry = ToolRegistry()
    registry.register(SleepTool())
    client = ScriptedClient([
        (
            '{"tool_calls": ['
            '{"name": "sleepy", "arguments": {"label": "fast", "delay": 0}},'
            '{"name": "sleepy", "arguments": {"label": "slow", "delay": 0.1}}'
            ']}'
        ),
        "Final with partial failure noted.",
    ])

    result = await run_chat(
        client,
        registry,
        "parallel please",
        max_parallel=2,
        per_call_timeout=0.02,
    )

    assert result["response"] == "Final with partial failure noted."
    assert len(result["tool_calls"]) == 2
    assert '"label": "fast"' in client.prompts[1]
    assert "Tool call timed out after 0.02 seconds" in client.prompts[1]


@pytest.mark.asyncio
async def test_run_chat_unknown_tool_error_injected():
    client = ScriptedClient([
        '{"tool_calls": [{"name": "missing_tool", "arguments": {}}]}',
        "Fallback after missing tool.",
    ])

    result = await run_chat(client, ToolRegistry(), "use missing")

    assert result["response"] == "Fallback after missing tool."
    assert "Unknown tool: missing_tool" in client.prompts[1]


@pytest.mark.asyncio
async def test_run_chat_duplicate_tool_call_uses_cached_result():
    registry = ToolRegistry()
    registry.register(EchoTool())
    client = ScriptedClient([
        '{"tool_calls": [{"name": "echo", "arguments": {"text": "same"}}]}',
        '{"tool_calls": [{"name": "echo", "arguments": {"text": "same"}}]}',
        "Done after duplicate.",
    ])

    result = await run_chat(client, registry, "dedupe")

    assert result["response"] == "Done after duplicate."
    assert "Returning cached result" in client.prompts[2]


@pytest.mark.asyncio
async def test_run_chat_context_overflow_reports_budget_warning():
    client = ScriptedClient(["Small answer."])

    result = await run_chat(
        client,
        ToolRegistry(),
        "tiny window",
        history=[{"role": "user", "content": "x" * 500}],
        context_window=20,
    )

    assert result["response"] == "Small answer."
    assert result["context"]["warnings"]
