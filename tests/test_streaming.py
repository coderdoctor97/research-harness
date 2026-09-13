# P10.T3 — Streaming tests
from __future__ import annotations

from typing import ClassVar
from unittest.mock import MagicMock

import pytest

from harness.llm.client import LLMClient, LLMConnectionError
from harness.loop.agent import run_chat_stream
from harness.registry.index import ToolRegistry
from harness.registry.tool import Tool, ToolResult


def test_stream_yields_tokens():
    c = LLMClient.__new__(LLMClient)
    c.base_url = "http://test"
    c.model_name = "x"
    c.api_key_env = "none"
    c.timeout = 5.0
    lines = ["data: {\"choices\":[{\"delta\":{\"content\":\"Hello\"}}]}", "data: {\"choices\":[{\"delta\":{\"content\":\" world\"}}]}", "data: [DONE]"]
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.text = "\n".join(lines)
    c.client = type("C", (), {"post": lambda *a, **k: mock_resp})()
    tokens = list(c.stream_chat("hi"))
    assert "".join(tokens) == "Hello world"


def test_stream_stops_at_done():
    c = LLMClient.__new__(LLMClient)
    c.base_url = "http://test"
    c.model_name = "x"
    c.api_key_env = "none"
    c.timeout = 5.0
    lines = ["data: {\"choices\":[{\"delta\":{\"content\":\"A\"}}]}", "data: {\"choices\":[{\"delta\":{\"content\":\"B\"}}]}", "data: [DONE]", "data: {\"choices\":[{\"delta\":{\"content\":\"C\"}}]}"]
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.text = "\n".join(lines)
    c.client = type("C", (), {"post": lambda *a, **k: mock_resp})()
    tokens = list(c.stream_chat("hi"))
    assert "".join(tokens) == "AB"


def test_stream_connection_error():
    c = LLMClient(base_url="http://127.0.0.1:1", model_name="x", timeout=0.5)
    with pytest.raises(LLMConnectionError):
        list(c.stream_chat("hi"))


class StreamingSearchTool(Tool):
    name = "web_search"
    description = "Search web"
    parameters: ClassVar[dict] = {"query": {"type": "string"}}

    def run(self, **params):
        return ToolResult(
            ok=True,
            data={
                "results": [
                    {
                        "title": "Stream Source",
                        "url": "https://example.com/stream",
                        "snippet": params.get("query", ""),
                    }
                ]
            },
        )


class ScriptedStreamClient:
    model_name = "stream-model"

    def __init__(self, replies):
        self.replies = list(replies)

    def stream_chat(self, prompt):
        yield from self.replies.pop(0)


@pytest.mark.asyncio
async def test_core_stream_events_interleave_tokens_tools_and_final():
    registry = ToolRegistry()
    registry.register(StreamingSearchTool())
    client = ScriptedStreamClient([
        [
            '{"tool_calls": [{"name": "web_search", ',
            '"arguments": {"query": "stream"}}]}',
        ],
        ["Final ", "answer [1]. https://example.com/stream"],
    ])

    events = [event async for event in run_chat_stream(client, registry, "stream it")]

    assert [event["type"] for event in events] == [
        "token",
        "token",
        "tool_call",
        "tool_result",
        "token",
        "token",
        "final",
    ]
    assert "".join(event["text"] for event in events if event["type"] == "token").startswith(
        '{"tool_calls"'
    )
    assert events[2]["name"] == "web_search"
    assert events[3]["result"]["data"]["results"][0]["url"] == "https://example.com/stream"
    assert events[-1]["response"].startswith("Final answer")
    assert events[-1]["sources"][0]["url"] == "https://example.com/stream"


@pytest.mark.asyncio
async def test_non_streaming_run_chat_stays_opt_in():
    class PlainClient:
        model_name = "plain-model"

        def __init__(self):
            self.stream_used = False

        def chat(self, prompt):
            return "Plain answer."

        def stream_chat(self, prompt):
            self.stream_used = True
            yield "unexpected"

    from harness.loop.agent import run_chat

    client = PlainClient()
    result = await run_chat(client, ToolRegistry(), "plain")

    assert result["response"] == "Plain answer."
    assert client.stream_used is False


@pytest.mark.asyncio
async def test_cli_stream_prints_tokens(capsys):
    from harness.cli.repl import _print_streaming_response

    client = ScriptedStreamClient([["Hello", " stream"]])

    await _print_streaming_response(client, ToolRegistry(), "hi")

    assert capsys.readouterr().out == "Hello stream\n"


def test_sse_chat_stream_route_emits_core_events():
    from unittest.mock import patch

    from fastapi.testclient import TestClient

    from harness.ui import _chat_state
    from harness.ui.app import create_application

    _chat_state._sessions.clear()
    registry = ToolRegistry()
    registry.register(StreamingSearchTool())
    client = ScriptedStreamClient([
        ['{"tool_calls": [{"name": "web_search", "arguments": {"query": "sse"}}]}'],
        ["SSE final [1]. https://example.com/stream"],
    ])

    with patch("harness.ui.routes_chat._get_client", return_value=client), patch(
        "harness.ui.routes_chat.builtin_tool_registry", return_value=registry
    ):
        response = TestClient(create_application()).post(
            "/api/chat/stream", json={"message": "sse"}
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "event: token" in body
    assert "event: tool_call" in body
    assert "event: tool_result" in body
    assert "event: final" in body
    assert "SSE final" in body
    assert _chat_state.list_sessions()[0]["message_count"] == 2


def test_sse_chat_stream_get_route():
    from unittest.mock import patch

    from fastapi.testclient import TestClient

    from harness.ui.app import create_application

    client = ScriptedStreamClient([["GET stream"]])
    with patch("harness.ui.routes_chat._get_client", return_value=client):
        response = TestClient(create_application()).get("/api/chat/stream?message=hello")

    assert response.status_code == 200
    assert "event: final" in response.text
