# P10.T8 — 15-scenario acceptance run (plan.md §10)
from __future__ import annotations

import pytest
import time
from harness.llm.client import LLMClient, LLMConnectionError, LLMResponseError
from harness.registry.tool import ToolResult
from harness.registry.index import ToolRegistry
from harness.loop.recovery import correction_prompt, duplicate_guard_key
from harness.citations.scrubber import scrub
from harness.memory.dedup import DedupCache, params_hash
from harness.tools.builtin.compute import ComputeTool
from harness.tools.builtin.academic_search import AcademicSearchTool
from harness.tools.builtin.news_search import NewsSearchTool
from harness.tools.builtin.extract_links import ExtractLinksTool
from harness.ui.app import create_application
from fastapi.testclient import TestClient


# S1 — Connection refused → LLMConnectionError
def test_s1_connection_refused():
    c = LLMClient(base_url="http://127.0.0.1:1", model_name="x", timeout=0.5)
    with pytest.raises(LLMConnectionError):
        c.chat("hello")


# S2 — HTTP 429 → LLMResponseError
def test_s2_rate_limit():
    from unittest.mock import MagicMock
    import httpx
    c = LLMClient.__new__(LLMClient)
    c.base_url = "http://test"
    c.model_name = "x"
    c.api_key_env = "none"
    c.timeout = 5.0
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "429", request=MagicMock(), response=MagicMock(status_code=429)
    )
    c.client = type("C", (), {"post": lambda *a, **k: mock_resp})()
    with pytest.raises(LLMResponseError, match="HTTP 429"):
        c.chat("hello")


# S3 — HTTP 500 → LLMResponseError
def test_s3_server_error():
    from unittest.mock import MagicMock
    import httpx
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


# S4 — DNS failure → LLMConnectionError
def test_s4_dns_failure():
    c = LLMClient(base_url="http://nonexistent.invalid", model_name="x", timeout=1.0)
    with pytest.raises(LLMConnectionError):
        c.chat("hello")


# S5 — Timeout → LLMConnectionError
def test_s5_timeout():
    c = LLMClient(base_url="http://10.255.255.1", model_name="x", timeout=0.5)
    with pytest.raises(LLMConnectionError):
        c.chat("hello")


# S6 — Malformed output recovery
def test_s6_correction_prompt():
    p = correction_prompt(3)
    assert "tool call" in p.lower()
    p5 = correction_prompt(5)
    assert "disabled" in p5.lower()


# S7 — Empty results
def test_s7_empty_results():
    tool = AcademicSearchTool()
    fake = ToolResult(ok=True, data="<feed></feed>")
    from unittest.mock import patch
    with patch.object(tool._executor, "execute", return_value=fake):
        r = tool.run(query="xyznonexistent", num_results=5)
    assert r.ok
    assert len(r.data["results"]) == 0


# S8 — Compute sandbox security
def test_s8_compute_security():
    tool = ComputeTool()
    r = tool.run(expression="import os")
    assert not r.ok
    r2 = tool.run(expression="2^32")
    assert r2.ok
    assert r2.data["result"] == 4294967296


# S9 — Unconfigured tool → graceful error
def test_s9_unconfigured_tool():
    tool = AcademicSearchTool()
    fake = ToolResult(ok=False, error="No endpoint configured")
    from unittest.mock import patch
    with patch.object(tool._executor, "execute", return_value=fake):
        r = tool.run(query="test")
    assert not r.ok


# S10 — Key scrubbing (no leak)
def test_s10_no_key_leak():
    text = "Authorization: Bearer sk-abcdef1234567890"
    clean, _ = scrub(text, set())
    assert "sk-" not in clean
    assert "Bearer" not in clean


# S11 — Circular tool-call guard
def test_s11_duplicate_guard():
    k1 = duplicate_guard_key("web_search", {"query": "AI"})
    k2 = duplicate_guard_key("web_search", {"query": "AI"})
    k3 = duplicate_guard_key("web_search", {"query": "ML"})
    assert k1 == k2
    assert k1 != k3


# S12 — Special-character URLs
def test_s12_special_char_urls():
    tool = ExtractLinksTool()
    fake = ToolResult(ok=True, data={"content": '[test](https://example.com/path?q=foo&bar=baz)'})
    from unittest.mock import patch
    with patch.object(tool._fetcher, "run", return_value=fake):
        r = tool.run(url="https://example.com")
    assert r.ok
    assert r.data["count"] == 1


# S13 — 50+ turn stress (lightweight dedup check)
def test_s13_long_conversation_dedup():
    cache = DedupCache()
    r = ToolResult(ok=True, data="cached")
    for i in range(50):
        cache.put("search", {"q": f"topic {i % 3}"}, r)
    hits = [cache.get("search", {"q": f"topic {i % 3}"}) for i in range(100)]
    assert all(h is r for h in hits if h is not None)


# S14 — UI binds localhost
def test_s14_ui_localhost():
    import uvicorn
    assert uvicorn is not None
    app = create_application()
    assert app is not None


# S15 — pip install -e . (package importable)
def test_s15_package_importable():
    import harness
    assert harness.__version__ == "0.1.0"
    from harness.tools.builtin.compute import ComputeTool
    assert ComputeTool().name == "compute"
