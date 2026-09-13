"""BF-011 regression tests — model auto-discovery instead of hardcoded IDs."""
from fastapi.testclient import TestClient

from harness.llm.client import LLMClient, LLMResponseError
from harness.ui import routes_chat
from harness.ui._ai_state import update_state
from harness.ui.app import create_application

MODELS = [
    {"id": "whisper-large-v3"},          # utility → skip
    {"id": "meta-llama/prompt-guard"},   # utility → skip
    {"id": "acme/chat-instruct"},        # chat model → pick
    {"id": "embed-3"},                   # utility → skip
]


class _Probe:
    """Duck-typed stand-in for LLMClient in pure discovery tests."""

    def __init__(self, models):
        self._models = models

    def list_models(self):
        return self._models


def test_discovery_prefers_chat_models():
    assert routes_chat._discover_model(_Probe(MODELS)) == "acme/chat-instruct"


def test_discovery_skips_utility_models_but_falls_back():
    only_utility = [{"id": "whisper-large-v3"}, {"id": "embed-3"}]
    assert routes_chat._discover_model(_Probe(only_utility)) == "whisper-large-v3"


def test_discovery_empty_list():
    assert routes_chat._discover_model(_Probe([])) == ""


def test_stale_model_404_triggers_rediscovery(monkeypatch):
    """Saved model 404 → cleared, rediscovered from live /models, retry once."""
    update_state(
        provider="custom", base_url="http://fake", api_key="x", model="gone-model"
    )

    calls = []
    client = LLMClient.__new__(LLMClient)
    client.model_name = "gone-model"
    client.list_models = lambda: MODELS

    def fake_chat(prompt):
        calls.append(client.model_name)
        if client.model_name == "gone-model":
            raise LLMResponseError("HTTP 404: model not found")
        return "recovered"

    client.chat = fake_chat
    monkeypatch.setattr(routes_chat, "_get_client", lambda model: client)

    resp = TestClient(create_application()).post("/api/chat", json={"message": "hi"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["response"] == "recovered"
    assert body["model"] == "acme/chat-instruct"
    assert calls == ["gone-model", "acme/chat-instruct"]

    from harness.ui._ai_state import get_state

    assert get_state()["model"] == "acme/chat-instruct"  # choice persisted


def test_no_model_saved_triggers_discovery_and_persists(monkeypatch):
    update_state(provider="custom", base_url="http://fake", api_key="x", model="")

    client = LLMClient.__new__(LLMClient)
    client.model_name = "llama3"
    client.list_models = lambda: MODELS
    client.chat = lambda prompt: "hello!"
    monkeypatch.setattr(routes_chat, "_get_client", lambda model: client)

    resp = TestClient(create_application()).post("/api/chat", json={"message": "hi"})
    assert resp.status_code == 200
    assert resp.json()["model"] == "acme/chat-instruct"

    from harness.ui._ai_state import get_state

    assert get_state()["model"] == "acme/chat-instruct"
