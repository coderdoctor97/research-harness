# Tests for sidebar chat session history (create / list / load / delete).
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from harness.ui import _chat_state
from harness.ui.app import create_application


@pytest.fixture(autouse=True)
def _reset_sessions():
    _chat_state._sessions.clear()
    yield
    _chat_state._sessions.clear()


@pytest.fixture
def client():
    return TestClient(create_application())


def _mock_llm(reply="Hello there"):
    mock = MagicMock()
    mock.chat.return_value = reply
    mock.model_name = "test-model"
    return mock


class TestChatSessions:
    def test_chat_creates_session(self, client):
        with patch("harness.ui.routes_chat._get_client", return_value=_mock_llm()):
            r = client.post("/api/chat", json={"message": "What is MCP?"})
        assert r.status_code == 200
        sid = r.json()["session_id"]
        assert sid

        listing = client.get("/api/chat/sessions").json()["sessions"]
        assert len(listing) == 1
        assert listing[0]["id"] == sid
        assert "What is MCP?" in listing[0]["title"]
        assert listing[0]["message_count"] == 2  # user + assistant

    def test_chat_continues_existing_session(self, client):
        with patch("harness.ui.routes_chat._get_client", return_value=_mock_llm("first")):
            sid = client.post("/api/chat", json={"message": "one"}).json()["session_id"]
        with patch("harness.ui.routes_chat._get_client", return_value=_mock_llm("second")):
            r = client.post("/api/chat", json={"message": "two", "session_id": sid})
        assert r.json()["session_id"] == sid

        session = client.get(f"/api/chat/sessions/{sid}").json()["session"]
        assert len(session["messages"]) == 4
        assert [m["role"] for m in session["messages"]] == ["user", "assistant", "user", "assistant"]
        assert session["messages"][3]["content"] == "second"

    def test_unknown_session_id_starts_new(self, client):
        with patch("harness.ui.routes_chat._get_client", return_value=_mock_llm()):
            r = client.post("/api/chat", json={"message": "hi", "session_id": "does-not-exist"})
        assert r.status_code == 200
        assert r.json()["session_id"] != "does-not-exist"

    def test_session_lifecycle(self, client):
        created = client.post("/api/chat/sessions", json={"title": "Notes"}).json()["session"]
        sid = created["id"]
        assert created["title"] == "Notes"

        assert client.get(f"/api/chat/sessions/{sid}").status_code == 200
        assert client.delete(f"/api/chat/sessions/{sid}").json()["status"] == "deleted"
        assert client.get(f"/api/chat/sessions/{sid}").status_code == 404
        assert client.delete(f"/api/chat/sessions/{sid}").status_code == 404

    def test_history_route_lists_sessions(self, client):
        with patch("harness.ui.routes_chat._get_client", return_value=_mock_llm()):
            client.post("/api/chat", json={"message": "hello world"})
        history = client.get("/api/chat/history").json()
        assert isinstance(history, list)
        assert history[0]["title"] == "hello world"

    def test_sessions_sorted_by_recency(self, client):
        with patch("harness.ui.routes_chat._get_client", return_value=_mock_llm()):
            first = client.post("/api/chat", json={"message": "older"}).json()["session_id"]
            client.post("/api/chat", json={"message": "newer"})
            client.post("/api/chat", json={"message": "follow-up", "session_id": first})
        listing = client.get("/api/chat/sessions").json()["sessions"]
        assert listing[0]["id"] == first  # bumped by the follow-up
