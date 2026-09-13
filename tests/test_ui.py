# P9.T6 — UI tests with FastAPI TestClient
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from harness.ui.app import create_application


@pytest.fixture
def client():
    app = create_application()
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_index(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "LLM Research Harness" in r.text


def test_keys_masked(client):
    r = client.get("/api/keys")
    assert r.status_code == 200
    data = r.json()
    assert data[0]["masked"] == "****"


def test_keys_set_and_masked(client):
    r = client.post("/api/keys/MY_KEY", json={"value": "secret1234"})
    assert r.status_code == 200
    assert "secret" not in r.json()["masked"]
    assert r.json()["masked"] == "******1234"  # last 4 chars shown, rest masked


def test_chat_endpoint(client):
    from unittest.mock import patch, MagicMock
    mock_client = MagicMock()
    mock_client.model_name = "mock-model"
    mock_client.chat.return_value = "Echo: hello"
    with patch("harness.ui.routes_chat._get_client", return_value=mock_client):
        r = client.post("/api/chat", json={"message": "hello"})
    assert r.status_code == 200
    assert "hello" in r.json()["response"]


def test_tool_call_extraction_wrapped_in_xml_tags():
    from harness.ui.routes_chat import _extract_tool_calls, _clean_final_text
    raw = (
        "<tool_call>\n"
        '{"tool_calls": [{"name": "fetch_url", "arguments": '
        '{"url": "https://en.wikipedia.org/wiki/Strobilanthes_kunthiana", '
        '"max_chars": 5000}}]}\n'
        "</tool_call>"
    )
    calls = _extract_tool_calls(raw)
    assert len(calls) == 1
    assert calls[0]["name"] == "fetch_url"
    assert calls[0]["arguments"]["url"].endswith("Strobilanthes_kunthiana")
    # the wrapper + JSON must not survive into the visible reply
    assert _clean_final_text(raw) == ""


def test_tool_call_extraction_shorthand_tag():
    from harness.ui.routes_chat import _extract_tool_calls
    raw = '<tool_call>{"name": "web_search", "arguments": {"query": "x"}}</tool_call>'
    calls = _extract_tool_calls(raw)
    assert len(calls) == 1
    assert calls[0]["name"] == "web_search"
    assert calls[0]["arguments"] == {"query": "x"}


def test_clean_final_text_strips_payload_and_tags():
    from harness.ui.routes_chat import _clean_final_text
    raw = (
        "Here is some prose.\n"
        '<tool_call>{"tool_calls": [{"name": "web_search", "arguments": {"query": "x"}}]}</tool_call>\n'
        "The answer follows."
    )
    out = _clean_final_text(raw)
    assert "tool_call" not in out
    assert "web_search" not in out
    assert "The answer follows." in out


def test_clean_final_text_strips_bare_json():
    from harness.ui.routes_chat import _clean_final_text
    raw = '{"tool_calls": [{"name": "web_search", "arguments": {"query": "x"}}]}'
    assert _clean_final_text(raw) == ""


def test_fit_context_no_window_returns_unchanged():
    from harness.ui.routes_chat import _fit_context
    lines = ["[system] prompt", "[user] question", "[tool:x] result"]
    assert _fit_context(lines, None) == lines
    assert _fit_context(lines, 0) == lines


def test_fit_context_keeps_head_and_trims_oldest():
    from harness.ui.routes_chat import _fit_context
    lines = [
        "[system] prompt",
        "[user] question",
        "[tool:a] " + "A" * 100,   # oldest tool result → trimmed first
        "[tool:b] " + "B" * 100,   # most recent → kept fully
    ]
    out = _fit_context(lines, context_window=40)  # 160 char budget
    assert out[0] == "[system] prompt"
    assert out[1] == "[user] question"
    joined = "\n".join(out)
    # newest tool result survives intact; oldest is truncated to fit the budget
    assert "B" * 100 in joined
    assert "A" * 100 not in joined


def test_logs_endpoint(client):
    r = client.get("/api/logs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_config_export_sanitized(client):
    r = client.get("/api/config/export")
    assert r.status_code == 200
    raw = r.json()["config"]
    assert "[REDACTED]" in raw or "api_key" not in raw


def test_config_import(client):
    r = client.post("/api/config/import", json={"config": "{}"})
    assert r.status_code == 200
    assert r.json()["status"] == "imported"


def test_config_import_empty(client):
    r = client.post("/api/config/import", json={"config": ""})
    assert r.status_code == 400
