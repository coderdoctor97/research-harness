# P4.T6 — E2E loop tests with scripted mock LLM
from __future__ import annotations

import time
from harness.loop.agent import LoopState
from harness.loop.parser import classify, CallType
from harness.loop.recovery import correction_prompt
from harness.registry.index import ToolRegistry
from harness.registry.tool import Tool, ToolResult
from harness.config.models import EndpointDef


class EchoTool(Tool):
    name = "echo"
    description = "Echo input"
    parameters = {"text": {"type": "string"}}

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
