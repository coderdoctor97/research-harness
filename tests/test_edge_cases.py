# P10.T1 — Error-handling audit: every §8 row has a test
from __future__ import annotations

import pytest
import httpx
from unittest.mock import MagicMock
from harness.llm.client import LLMClient, LLMConnectionError, LLMResponseError
from harness.loop.recovery import correction_prompt
from harness.citations.scrubber import scrub


# --- §8 connection errors ---
def test_connection_refused_no_traceback():
    c = LLMClient(base_url="http://127.0.0.1:1", model_name="x", timeout=0.5)
    with pytest.raises(LLMConnectionError):
        c.chat("hello")


def test_timeout_no_traceback():
    c = LLMClient(base_url="http://10.255.255.1", model_name="x", timeout=0.5)
    with pytest.raises(LLMConnectionError):
        c.chat("hello")


# --- §8 HTTP errors ---
def test_5xx_returns_response_error():
    c = LLMClient.__new__(LLMClient)
    c.base_url = "http://test"
    c.model_name = "x"
    c.api_key_env = "none"
    c.timeout = 5.0
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500", request=MagicMock(), response=MagicMock(status_code=500)
    )
    c.client = type("C", (), {"post": lambda *a, **k: mock_resp})()
    with pytest.raises(LLMResponseError, match="HTTP 500"):
        c.chat("hello")


def test_4xx_returns_response_error():
    c = LLMClient.__new__(LLMClient)
    c.base_url = "http://test"
    c.model_name = "x"
    c.api_key_env = "none"
    c.timeout = 5.0
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404", request=MagicMock(), response=MagicMock(status_code=404)
    )
    c.client = type("C", (), {"post": lambda *a, **k: mock_resp})()
    with pytest.raises(LLMResponseError, match="HTTP 404"):
        c.chat("hello")


# --- §8 empty/malformed responses ---
def test_empty_choices_returns_error():
    c = LLMClient.__new__(LLMClient)
    c.base_url = "http://test"
    c.model_name = "x"
    c.api_key_env = "none"
    c.timeout = 5.0
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"choices": []}
    c.client = type("C", (), {"post": lambda *a, **k: mock_resp})()
    with pytest.raises(LLMResponseError, match="Empty"):
        c.chat("hello")


# --- §8 duplicate tool calls ---
def test_duplicate_call_guard():
    from harness.loop.recovery import duplicate_guard_key
    k1 = duplicate_guard_key("web_search", {"query": "AI"})
    k2 = duplicate_guard_key("web_search", {"query": "AI"})
    k3 = duplicate_guard_key("web_search", {"query": "ML"})
    assert k1 == k2
    assert k1 != k3


# --- §8 malformed output recovery ---
def test_correction_prompt_3_strikes():
    p = correction_prompt(3)
    assert "tool call" in p.lower()


def test_tools_off_5_strikes():
    p = correction_prompt(5)
    assert "disabled" in p.lower()


# --- §8 key scrubbing ---
def test_key_scrubbing_no_leak():
    text = "Authorization: Bearer sk-abcdef1234567890"
    clean, _ = scrub(text, set())
    assert "Bearer" not in clean
    assert "sk-" not in clean
