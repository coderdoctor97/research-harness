# Tests for the simple AI integration: OpenAI-compatible provider flow
# (provider -> key -> test connection -> fetch models), free default MCP
# services (built-in fetcher + DuckDuckGo), and optional manual endpoints.
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from harness.llm.client import LLMClient, LLMConnectionError
from harness.mcp import builtin as mcp_builtin
from harness.ui._mcp_state import _mcp_servers, restore_defaults
from harness.ui.app import create_application


@pytest.fixture(autouse=True)
def _reset_state():
    from harness.ui import _ai_state as ai_state_mod
    _mcp_servers.clear()
    restore_defaults()
    ai_state_mod._ai_state.update({
        "provider": "ollama",
        "base_url": "http://localhost:11434/v1",
        "api_key": "",
        "api_key_env": "none",
        "model": "",
        "max_tokens": None,
        "context_window": None,
    })
    yield


@pytest.fixture
def client():
    return TestClient(create_application())


# ---------------------------------------------------------------------------
# Provider flow
# ---------------------------------------------------------------------------

class TestProviderFlow:
    def test_get_provider_presets_and_masked_state(self, client):
        r = client.get("/api/ai/provider")
        assert r.status_code == 200
        data = r.json()
        assert "ollama" in data["presets"]
        assert data["presets"]["openai"]["base_url"] == "https://api.openai.com/v1"
        assert data["provider"]["api_key"] == ""  # never echoed back

    def test_save_provider_masks_key(self, client):
        r = client.post("/api/ai/provider", json={
            "provider": "openai",
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-secret-key-1234",
        })
        assert r.status_code == 200
        provider = r.json()["provider"]
        assert provider["api_key"] == ""
        assert provider["api_key_masked"].endswith("1234")
        assert "sk-" not in provider["api_key_masked"]

    def test_save_provider_requires_base_url(self, client):
        r = client.post("/api/ai/provider", json={"base_url": "   "})
        assert r.status_code == 400

    def test_save_provider_generation_settings(self, client):
        r = client.post("/api/ai/provider", json={
            "base_url": "https://api.example.com/v1",
            "max_tokens": 2048,
            "context_window": 8192,
        })
        assert r.status_code == 200
        provider = r.json()["provider"]
        assert provider["max_tokens"] == 2048
        assert provider["context_window"] == 8192
        # persisted to state
        from harness.ui._ai_state import get_state
        assert get_state()["max_tokens"] == 2048
        assert get_state()["context_window"] == 8192

    def test_save_provider_generation_settings_clear(self, client):
        # set, then clear via explicit nulls
        client.post("/api/ai/provider", json={
            "base_url": "https://api.example.com/v1",
            "max_tokens": 2048, "context_window": 8192,
        })
        r = client.post("/api/ai/provider", json={"max_tokens": None, "context_window": None})
        assert r.status_code == 200
        assert r.json()["provider"]["max_tokens"] is None
        assert r.json()["provider"]["context_window"] is None

    def test_save_provider_generation_settings_partial(self, client):
        # saving only max_tokens must not clobber context_window
        client.post("/api/ai/provider", json={
            "base_url": "https://api.example.com/v1", "context_window": 8192,
        })
        r = client.post("/api/ai/provider", json={"max_tokens": 4096})
        assert r.status_code == 200
        provider = r.json()["provider"]
        assert provider["max_tokens"] == 4096
        assert provider["context_window"] == 8192

    def test_test_connection_success(self, client):
        mock = MagicMock()
        mock.list_models.return_value = [{"id": "llama3", "name": "llama3", "owned_by": ""}]
        with patch("harness.ui.routes_models.LLMClient", return_value=mock):
            r = client.post("/api/ai/test", json={"base_url": "http://localhost:11434/v1"})
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert data["models_count"] == 1
        assert data["latency_ms"] >= 0

    def test_test_connection_refused(self, client):
        mock = MagicMock()
        mock.list_models.side_effect = LLMConnectionError("Connection refused")
        with patch("harness.ui.routes_models.LLMClient", return_value=mock):
            r = client.post("/api/ai/test", json={"base_url": "http://localhost:1/v1"})
        assert r.status_code == 200
        assert r.json()["ok"] is False
        assert "refused" in r.json()["error"].lower()

    def test_models_accepts_direct_api_key(self, client):
        mock = MagicMock()
        mock.list_models.return_value = []
        with patch("harness.ui.routes_models.LLMClient", return_value=mock) as ctor:
            r = client.get("/api/models?base_url=http://x/v1&api_key=sk-abc")
        assert r.status_code == 200
        assert ctor.call_args.kwargs.get("api_key") == "sk-abc"

    def test_client_prefers_direct_key_over_env(self):
        c = LLMClient(base_url="http://x/v1", model_name="m", api_key_env="NOPE", api_key="sk-direct")
        assert c._headers()["Authorization"] == "Bearer sk-direct"


# ---------------------------------------------------------------------------
# Built-in free MCP services
# ---------------------------------------------------------------------------

DDG_HTML = """
<div class="result"><a rel="nofollow" class="result__a"
 href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpaper&rut=abc">Example <b>Paper</b></a>
 <a class="result__snippet" href="#">A very <b>relevant</b> snippet.</a></div>
<div class="result"><a rel="nofollow" class="result__a"
 href="https://other.org/page">Other Org</a>
 <a class="result__snippet" href="#">Second snippet here.</a></div>
"""


class TestBuiltinServices:
    def test_defaults_seeded(self, client):
        r = client.get("/api/mcp/servers")
        names = [s["name"] for s in r.json()["servers"]]
        assert "builtin-fetcher" in names
        assert "builtin-search" in names
        fetcher = next(s for s in r.json()["servers"] if s["name"] == "builtin-fetcher")
        assert fetcher["free"] is True
        assert {t["name"] for t in fetcher["tools"]} == {"fetch_url", "extract_links"}

    def test_strip_html(self):
        html = "<html><head><style>x{}</style></head><body><p>Hello <b>world</b></p><script>evil()</script></body></html>"
        text = mcp_builtin.strip_html(html)
        assert "Hello world" in text
        assert "evil" not in text and "<" not in text

    def test_parse_ddg_html(self):
        results = mcp_builtin.parse_ddg_html(DDG_HTML, max_results=5)
        assert len(results) == 2
        assert results[0]["url"] == "https://example.com/paper"  # uddg redirect resolved
        assert results[0]["title"] == "Example Paper"
        assert "relevant" in results[0]["snippet"]

    def test_parse_ddg_lite_html(self):
        lite = """
        <tr><td><a rel="nofollow" href="https://en.wikipedia.org/wiki/Large_language_model"
          class='result-link'>Large language model - Wikipedia</a></td></tr>
        <tr><td class='result-snippet'>A <b>large language model</b> is...</td></tr>
        """
        results = mcp_builtin.parse_ddg_html(lite, max_results=5)
        assert len(results) == 1
        assert results[0]["url"] == "https://en.wikipedia.org/wiki/Large_language_model"
        assert results[0]["title"] == "Large language model - Wikipedia"
        assert "large language model" in results[0]["snippet"].lower()

    @pytest.mark.asyncio
    async def test_fetch_url_tool(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "text/html"}
        mock_resp.text = "<html><body><h1>Title</h1><p>Body text</p></body></html>"
        mock_resp.url = "https://example.com/"
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__.return_value = mock_client
        with patch("harness.mcp.builtin.httpx.AsyncClient", return_value=mock_client):
            result = await mcp_builtin.FETCHER_SERVER.call_tool("fetch_url", {"url": "example.com"})
        assert result["ok"] is True
        assert result["status"] == 200
        assert "Title" in result["content"] and "<h1>" not in result["content"]

    @pytest.mark.asyncio
    async def test_web_search_tool(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = DDG_HTML
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client.__aenter__.return_value = mock_client
        with patch("harness.mcp.builtin.httpx.AsyncClient", return_value=mock_client):
            result = await mcp_builtin.SEARCH_SERVER.call_tool("web_search", {"query": "test"})
        assert result["ok"] is True
        assert result["result_count"] == 2
        assert result["results"][0]["url"] == "https://example.com/paper"

    def test_call_tool_route(self, client):
        async def fake_call(name, arguments):
            return {"ok": True, "echo": arguments}
        with patch.object(mcp_builtin.SEARCH_SERVER, "call_tool", side_effect=fake_call):
            r = client.post("/api/mcp/tools/call", json={
                "server": "builtin-search", "tool": "web_search", "arguments": {"query": "q"},
            })
        assert r.status_code == 200
        assert r.json()["result"]["ok"] is True

    def test_call_tool_unknown_server(self, client):
        r = client.post("/api/mcp/tools/call", json={"server": "nope", "tool": "x"})
        assert r.status_code == 400

    def test_mcp_tools_route_includes_builtins(self, client):
        r = client.get("/api/mcp/tools")
        names = {t["name"] for t in r.json()["tools"]}
        assert {"fetch_url", "extract_links", "web_search"} <= names


class TestMcpPresets:
    def test_presets_listed_with_status(self, client):
        r = client.get("/api/mcp/presets")
        presets = {p["id"]: p for p in r.json()["presets"]}
        assert presets["builtin-fetcher"]["installed"] is True
        assert presets["brave-search"]["requires_key"] is True
        assert presets["brave-search"]["free"] is True

    def test_brave_requires_key(self, client):
        import os
        os.environ.pop("BRAVE_API_KEY", None)
        r = client.post("/api/mcp/presets/brave-search/install", json={})
        assert r.status_code == 400

    def test_brave_install_with_key(self, client):
        r = client.post("/api/mcp/presets/brave-search/install", json={"api_key": "BSA123"})
        assert r.status_code == 200
        names = [s["name"] for s in r.json()["servers"]]
        assert "brave-search" in names

    def test_restore_builtin_after_removal(self, client):
        client.delete("/api/mcp/servers/builtin-fetcher")
        names = [s["name"] for s in client.get("/api/mcp/servers").json()["servers"]]
        assert "builtin-fetcher" not in names
        client.post("/api/mcp/presets/builtin-fetcher/install", json={})
        names = [s["name"] for s in client.get("/api/mcp/servers").json()["servers"]]
        assert "builtin-fetcher" in names

    def test_unknown_preset(self, client):
        r = client.post("/api/mcp/presets/does-not-exist/install", json={})
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Optional manual endpoints + keys
# ---------------------------------------------------------------------------

class TestEndpointsAndKeys:
    def test_endpoint_add_list_remove(self, client):
        r = client.post("/api/endpoints", json={"name": "serper", "url": "https://google.serper.dev/search", "method": "POST"})
        assert r.status_code == 200
        listing = client.get("/api/endpoints").json()
        assert len(listing) == 1 and listing[0]["name"] == "serper"
        client.delete("/api/endpoints/serper")
        assert client.get("/api/endpoints").json() == []

    def test_endpoint_requires_fields(self, client):
        assert client.post("/api/endpoints", json={"name": "x"}).status_code == 400

    def test_endpoint_test_ok(self, client):
        client.post("/api/endpoints", json={"name": "ep", "url": "https://api.test/{query}"})
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__.return_value = mock_client
        with patch("harness.ui.routes_endpoints.httpx.AsyncClient", return_value=mock_client):
            r = client.post("/api/endpoints/ep/test", json={})
        assert r.status_code == 200
        assert r.json()["result"] == "ok"

    def test_keys_stored_masked_and_in_env(self, client):
        r = client.post("/api/keys/SERPER_API_KEY", json={"value": "supersecret99"})
        assert r.status_code == 200
        assert r.json()["masked"] == "*********et99"  # last 4 shown, rest masked
        import os
        assert os.environ.get("SERPER_API_KEY") == "supersecret99"
        listing = client.get("/api/keys").json()
        names = [k["name"] for k in listing]
        assert names[0] == "API_KEY"  # stable first entry
        assert "SERPER_API_KEY" in names
        entry = next(k for k in listing if k["name"] == "SERPER_API_KEY")
        assert entry["set"] is True
        assert "supersecret99" not in entry["masked"]


# ---------------------------------------------------------------------------
# Chat tool loop over built-in services
# ---------------------------------------------------------------------------

class TestChatToolLoop:
    def test_chat_runs_tool_then_answers(self, client):
        tool_call_json = json.dumps({
            "tool_calls": [{"name": "web_search", "arguments": {"query": "test"}}]
        })
        mock_llm = MagicMock()
        mock_llm.chat.side_effect = [tool_call_json, "The answer is 42. [1] https://example.com/paper"]
        mock_llm.model_name = "llama3"

        async def fake_run_tool(name, arguments):
            return {"ok": True, "results": [{"title": "Example Paper", "url": "https://example.com/paper", "snippet": "s"}]}

        with patch("harness.ui.routes_chat._get_client", return_value=mock_llm), \
             patch("harness.ui.routes_chat._run_tool", side_effect=fake_run_tool):
            r = client.post("/api/chat", json={"message": "find the answer"})

        assert r.status_code == 200
        data = r.json()
        assert "42" in data["response"]
        assert [t["name"] for t in data["tool_calls"]] == ["web_search"]
        assert data["sources"][0]["url"] == "https://example.com/paper"
        assert mock_llm.chat.call_count == 2

    def test_chat_plain_answer_no_tools(self, client):
        mock_llm = MagicMock()
        mock_llm.chat.return_value = "Just a plain answer."
        mock_llm.model_name = "llama3"
        with patch("harness.ui.routes_chat._get_client", return_value=mock_llm):
            r = client.post("/api/chat", json={"message": "hi"})
        assert r.status_code == 200
        assert r.json()["tool_calls"] == []
        assert mock_llm.chat.call_count == 1

    def test_chat_tool_loop_bounded(self, client):
        tool_call_json = json.dumps({
            "tool_calls": [{"name": "web_search", "arguments": {"query": "loop"}}]
        })
        mock_llm = MagicMock()
        mock_llm.chat.return_value = tool_call_json  # never stops asking for tools
        mock_llm.model_name = "llama3"

        async def fake_run_tool(name, arguments):
            return {"ok": True, "results": []}

        with patch("harness.ui.routes_chat._get_client", return_value=mock_llm), \
             patch("harness.ui.routes_chat._run_tool", side_effect=fake_run_tool):
            r = client.post("/api/chat", json={"message": "loop forever"})
        assert r.status_code == 200
        # MAX_TOOL_ROUNDS tool rounds + one BF-014 "force final answer" call.
        from harness.ui.routes_chat import MAX_TOOL_ROUNDS
        assert mock_llm.chat.call_count <= MAX_TOOL_ROUNDS + 2

    def test_chat_forces_final_answer_when_model_keeps_asking(self, client):
        # The model returns a tool call on every turn but, when explicitly told
        # to finish, produces a real answer — the BF-014 finalize step surfaces it.
        tool_call_json = json.dumps({
            "tool_calls": [{"name": "web_search", "arguments": {"query": "loop"}}]
        })
        mock_llm = MagicMock()
        mock_llm.chat.side_effect = [tool_call_json, tool_call_json, tool_call_json,
                                     tool_call_json, "Final answer at last."]
        mock_llm.model_name = "llama3"

        async def fake_run_tool(name, arguments):
            return {"ok": True, "results": []}

        with patch("harness.ui.routes_chat._get_client", return_value=mock_llm), \
             patch("harness.ui.routes_chat._run_tool", side_effect=fake_run_tool):
            r = client.post("/api/chat", json={"message": "loop forever"})
        assert r.status_code == 200
        assert "Final answer at last." in r.json()["response"]
        assert "couldn't produce" not in r.json()["response"]


# ---------------------------------------------------------------------------
# A1 — Provider & Key Pipeline Hardening (plans/ai-integration-plan.md)
# ---------------------------------------------------------------------------

class TestRestartResilience:
    """A1.1.1 / A1.1.2 — BF-010 + BF-005: configured state survives restarts."""

    def test_provider_survives_restart(self, client, monkeypatch, tmp_path):
        """Configure provider → simulate restart (state reload) → /api/models 200."""
        import importlib

        from harness.ui import _ai_state as ai_state_mod

        state_file = tmp_path / "state.json"
        monkeypatch.setenv("HARNESS_STATE_FILE", str(state_file))
        client.post("/api/ai/provider", json={
            "provider": "groq",
            "base_url": "https://api.groq.com/openai/v1",
            "api_key": "gsk_test_key_9876",
        })
        assert state_file.exists()

        # Restart = module reload: memory wiped, state re-read from disk.
        importlib.reload(ai_state_mod)
        assert ai_state_mod.get_state()["base_url"] == "https://api.groq.com/openai/v1"
        assert ai_state_mod.get_state()["api_key"] == "gsk_test_key_9876"

        # /api/models with NO params resolves the saved provider (BF-010).
        mock = MagicMock()
        mock.list_models.return_value = [{"id": "llama3", "name": "llama3", "owned_by": ""}]
        fresh = TestClient(create_application())
        with patch("harness.ui.routes_models.LLMClient", return_value=mock) as ctor:
            r = fresh.get("/api/models")
        assert r.status_code == 200
        assert ctor.call_args.kwargs.get("base_url") == "https://api.groq.com/openai/v1"
        assert ctor.call_args.kwargs.get("api_key") == "gsk_test_key_9876"

        # Restore the shared module state for other tests.
        monkeypatch.undo()
        importlib.reload(ai_state_mod)

    def test_chat_reads_saved_provider_no_inline_params(self, client):
        """BF-005: chat works with zero inline params — saved provider only."""
        client.post("/api/ai/provider", json={
            "provider": "custom",
            "base_url": "https://saved.example/v1",
            "api_key": "sk-saved-key-000111",
            "model": "saved-model",
        })
        captured: dict = {}
        real_init = LLMClient.__init__

        def spy_init(self, **kwargs):  # real class kept — isinstance checks intact
            captured.update(kwargs)
            real_init(self, **kwargs)

        with patch.object(LLMClient, "__init__", spy_init), \
             patch.object(LLMClient, "chat", return_value="answer from saved provider"):
            r = client.post("/api/chat", json={"message": "hi"})  # NO model/base_url/key
        assert r.status_code == 200
        assert r.json()["response"] == "answer from saved provider"
        assert captured["base_url"] == "https://saved.example/v1"
        assert captured["api_key"] == "sk-saved-key-000111"
        assert captured["model_name"] == "saved-model"

    def test_keys_survive_restart(self, client, monkeypatch, tmp_path):
        """BF-010: Keys-tab keys reload from .harness-state.json on restart."""
        from harness.ui._ai_state import load_section

        state_file = tmp_path / "state.json"
        monkeypatch.setenv("HARNESS_STATE_FILE", str(state_file))
        client.post("/api/keys/RESTART_TEST_KEY", json={"value": "persist-me-1234"})
        assert (load_section("keys") or {}).get("RESTART_TEST_KEY") == "persist-me-1234"
        import os
        os.environ.pop("RESTART_TEST_KEY", None)


class TestModelDiscoveryFallbacks:
    """A1.1.3 — discovery never returns hardcoded cloud IDs; falls back sanely."""

    def test_no_hardcoded_cloud_models_in_state(self):
        from harness.ui._ai_state import _DEFAULT_STATE
        assert _DEFAULT_STATE["model"] == ""  # BF-011: discovered, never hardcoded

    def test_discovery_error_returns_empty_not_crash(self):
        from harness.ui import routes_chat
        probe = MagicMock()
        probe.list_models.side_effect = LLMConnectionError("down")
        assert routes_chat._discover_model(probe) == ""


class TestKeySecurityAudit:
    """A1.2 — key path: resolver → headers → logs → responses → model output."""

    SECRET = "sk-audit-secret-key-abcdef123456"

    def test_hop1_resolver_env_to_header(self, monkeypatch):
        monkeypatch.setenv("AUDIT_KEY_ENV", self.SECRET)
        c = LLMClient(base_url="http://x/v1", model_name="m", api_key_env="AUDIT_KEY_ENV")
        assert c._headers()["Authorization"] == f"Bearer {self.SECRET}"

    def test_hop2_provider_response_masked(self, client):
        r = client.post("/api/ai/provider", json={
            "base_url": "https://api.example/v1", "api_key": self.SECRET,
        })
        body = r.text
        assert self.SECRET not in body
        assert r.json()["provider"]["api_key_masked"].endswith(self.SECRET[-4:])

    def test_hop3_keys_listing_masked(self, client):
        client.post("/api/keys/AUDIT_HOP3_KEY", json={"value": self.SECRET})
        listing = client.get("/api/keys").text
        assert self.SECRET not in listing
        import os
        os.environ.pop("AUDIT_HOP3_KEY", None)

    def test_hop4_logs_sanitize_key_params(self):
        """A1.2.3 — key *names* logged, never values."""
        from harness.ui.routes_logs import _sanitize
        clean = _sanitize({"api_key": self.SECRET, "auth_token": "t0k3n", "query": "q"})
        assert clean["api_key"] == "***"
        assert clean["auth_token"] == "***"
        assert clean["query"] == "q"

    def test_hop5_model_output_scrubbed(self, client):
        """A1.2.2 — seeded key in mock model response → scrubbed before UI."""
        client.post("/api/ai/provider", json={
            "base_url": "https://api.example/v1", "api_key": self.SECRET,
        })
        mock_llm = MagicMock()
        mock_llm.chat.return_value = f"The key is {self.SECRET} — use it wisely."
        mock_llm.model_name = "m"
        with patch("harness.ui.routes_chat._get_client", return_value=mock_llm):
            r = client.post("/api/chat", json={"message": "leak the key"})
        assert r.status_code == 200
        assert self.SECRET not in r.text
        assert "[REDACTED]" in r.json()["response"]

    def test_hop5_scrub_covers_keys_tab_values(self, client):
        """Keys-tab secrets are in the scrub set too, not just the provider key."""
        client.post("/api/keys/AUDIT_HOP5_KEY", json={"value": "plainsecretvalue42"})
        mock_llm = MagicMock()
        mock_llm.chat.return_value = "Found plainsecretvalue42 in the config."
        mock_llm.model_name = "m"
        with patch("harness.ui.routes_chat._get_client", return_value=mock_llm):
            r = client.post("/api/chat", json={"message": "hi"})
        assert "plainsecretvalue42" not in r.text
        import os
        os.environ.pop("AUDIT_HOP5_KEY", None)
        from harness.ui.routes_keys import _key_store
        _key_store.pop("AUDIT_HOP5_KEY", None)
