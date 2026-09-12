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
    r = client.post("/api/chat", json={"message": "hello"})
    assert r.status_code == 200
    assert "hello" in r.json()["response"]


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
