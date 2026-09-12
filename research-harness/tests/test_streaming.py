# P10.T3 — Streaming tests
from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from harness.llm.client import LLMClient, LLMConnectionError, LLMResponseError


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
