# Tests for /api/models endpoint and MCP management routes
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from harness.llm.client import LLMConnectionError, LLMResponseError
from harness.ui._mcp_state import _mcp_servers
from harness.ui.app import create_application


@pytest.fixture(autouse=True)
def _reset_mcp_state():
    """Reset MCP server list before each test to ensure isolation."""
    _mcp_servers.clear()
    yield


@pytest.fixture
def client():
    app = create_application()
    return TestClient(app)


def _mock_llm_client(json_data):
    mock = MagicMock()
    mock.list_models.return_value = json_data
    return mock


class TestModelsEndpoint:
    def test_models_success(self, client):
        mock_models = [
            {"id": "llama3", "name": "Llama 3", "owned_by": "meta"},
            {"id": "mistral", "name": "Mistral", "owned_by": "mistralai"},
        ]
        with patch("harness.ui.routes_models.LLMClient") as MockClient:
            MockClient.return_value = _mock_llm_client(mock_models)
            r = client.get("/api/models?base_url=http://localhost:11434/v1")

        assert r.status_code == 200
        data = r.json()
        assert "models" in data
        assert len(data["models"]) == 2
        assert data["models"][0]["id"] == "llama3"

    def test_models_connection_error(self, client):
        with patch("harness.ui.routes_models.LLMClient") as MockClient:
            mock = MagicMock()
            mock.list_models.side_effect = LLMConnectionError("Connection refused")
            MockClient.return_value = mock
            r = client.get("/api/models")

        assert r.status_code == 503

    def test_models_http_error(self, client):
        with patch("harness.ui.routes_models.LLMClient") as MockClient:
            mock = MagicMock()
            mock.list_models.side_effect = LLMResponseError("HTTP 500")
            MockClient.return_value = mock
            r = client.get("/api/models")

        assert r.status_code == 502

    def test_models_empty(self, client):
        with patch("harness.ui.routes_models.LLMClient") as MockClient:
            MockClient.return_value = _mock_llm_client([])
            r = client.get("/api/models")

        assert r.status_code == 200
        assert r.json()["models"] == []


class TestMcpRoutes:
    def test_list_mcp_servers_empty(self, client):
        r = client.get("/api/mcp/servers")
        assert r.status_code == 200
        assert r.json()["servers"] == []

    def test_add_mcp_server(self, client):
        r = client.post("/api/mcp/servers", json={
            "name": "test-server",
            "command": "npx",
            "args": ["-y", "server-test"],
        })
        assert r.status_code == 200
        data = r.json()
        assert len(data["servers"]) == 1
        assert data["servers"][0]["name"] == "test-server"
        assert data["servers"][0]["command"] == "npx"

    def test_add_mcp_server_duplicate(self, client):
        client.post("/api/mcp/servers", json={"name": "dup", "command": "npx", "args": []})
        r = client.post("/api/mcp/servers", json={"name": "dup", "command": "node", "args": ["x"]})
        assert r.status_code == 200
        data = r.json()
        assert len(data["servers"]) == 1
        assert data["servers"][0]["command"] == "node"

    def test_add_mcp_server_missing_fields(self, client):
        r = client.post("/api/mcp/servers", json={})
        assert r.status_code == 400

    def test_remove_mcp_server(self, client):
        client.post("/api/mcp/servers", json={"name": "to-remove", "command": "npx"})
        r = client.delete("/api/mcp/servers/to-remove")
        assert r.status_code == 200
        assert r.json()["servers"] == []

    def test_remove_nonexistent(self, client):
        r = client.delete("/api/mcp/servers/nonexistent")
        assert r.status_code == 200
        assert r.json()["servers"] == []

    def test_list_mcp_tools_empty(self, client):
        r = client.get("/api/mcp/tools")
        assert r.status_code == 200
        assert r.json()["tools"] == []

    def test_mcp_tools_with_env(self, client):
        client.post("/api/mcp/servers", json={
            "name": "env-server",
            "command": "python",
            "args": ["-m", "server"],
            "env": {"KEY": "val"},
        })
        r = client.get("/api/mcp/tools")
        assert r.status_code == 200


class TestMcpInConfig:
    def test_config_export_includes_mcp(self, client):
        from harness.ui._mcp_state import _mcp_servers
        _mcp_servers.clear()
        client.post("/api/mcp/servers", json={
            "name": "ddg", "command": "npx", "args": ["-y", "ddgs"]
        })
        r = client.get("/api/config/export")
        assert r.status_code == 200
        config = json.loads(r.json()["config"])
        assert "mcp_servers" in config
        assert len(config["mcp_servers"]) == 1

    def test_config_import_mcp(self, client):
        config = json.dumps({"mcp_servers": [{"name": "imported", "command": "go", "args": ["run"]}]})
        r = client.post("/api/config/import", json={"config": config})
        assert r.status_code == 200
        r2 = client.get("/api/config/export")
        config2 = json.loads(r2.json()["config"])
        assert len(config2["mcp_servers"]) == 1
        assert config2["mcp_servers"][0]["name"] == "imported"