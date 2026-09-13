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


def _mock_llm(reply: str):
    from unittest.mock import MagicMock
    mock = MagicMock()
    mock.model_name = "mock-model"
    mock.chat.return_value = reply
    return mock


# ---------------------------------------------------------------------------
# U2.3 — /api/chat/inspect (reactive text inspection)
# ---------------------------------------------------------------------------

def test_inspect_define_single_hop(client):
    from unittest.mock import patch
    mock = _mock_llm("A stromberg is a technical noun.")
    with patch("harness.ui.routes_chat._get_client", return_value=mock):
        r = client.post("/api/chat/inspect", json={
            "phrase": "stromberg",
            "context": "The stromberg was unusual in 1998.",
            "sources": [{"title": "T", "url": "https://e.x/1"}],
            "mode": "define",
        })
    assert r.status_code == 200
    body = r.json()
    assert body["response"] == "A stromberg is a technical noun."
    assert body["sources"] == [{"title": "T", "url": "https://e.x/1"}]
    assert body["model"] == "mock-model"
    # single hop: exactly one LLM call; prompt carries phrase + context + numbered refs
    assert mock.chat.call_count == 1
    prompt = mock.chat.call_args[0][0]
    assert "stromberg" in prompt
    assert "The stromberg was unusual in 1998." in prompt
    assert "[1] T — https://e.x/1" in prompt
    assert "Define the phrase" in prompt


def test_inspect_breakdown_prompt(client):
    from unittest.mock import patch
    mock = _mock_llm("Deeper analysis.")
    with patch("harness.ui.routes_chat._get_client", return_value=mock):
        r = client.post("/api/chat/inspect", json={
            "phrase": "qubit", "context": "qubits decohere.", "mode": "breakdown",
        })
    assert r.status_code == 200
    prompt = mock.chat.call_args[0][0]
    assert "deeper contextual breakdown" in prompt
    assert "(none — do not use [n] markers)" in prompt  # no sources → no invented cites


def test_inspect_rejects_bad_mode(client):
    r = client.post("/api/chat/inspect", json={"phrase": "x", "mode": "hack"})
    assert r.status_code == 422


def test_inspect_requires_phrase(client):
    r = client.post("/api/chat/inspect", json={"phrase": "   ", "mode": "define"})
    assert r.status_code == 422


def test_inspect_caps_inputs(client):
    from unittest.mock import patch
    mock = _mock_llm("ok")
    with patch("harness.ui.routes_chat._get_client", return_value=mock):
        r = client.post("/api/chat/inspect", json={
            "phrase": "P" * 5000, "context": "C" * 9000, "mode": "define",
        })
    assert r.status_code == 200
    prompt = mock.chat.call_args[0][0]
    assert "P" * 300 in prompt and "P" * 301 not in prompt
    assert "C" * 4000 in prompt and "C" * 4001 not in prompt


def test_inspect_does_not_pollute_sessions(client):
    from unittest.mock import patch
    import harness.ui._chat_state as cs
    before = len(cs.list_sessions())
    mock = _mock_llm("ok")
    with patch("harness.ui.routes_chat._get_client", return_value=mock):
        r = client.post("/api/chat/inspect", json={"phrase": "term", "context": "ctx", "mode": "define"})
    assert r.status_code == 200
    assert len(cs.list_sessions()) == before  # ephemeral loupe, not conversation history


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
