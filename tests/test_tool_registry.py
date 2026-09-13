# P3.T5 + P3.T6 fixture tests
from unittest.mock import patch

from harness.config.models import EndpointDef
from harness.registry.index import ToolRegistry
from harness.registry.ratelimit import RateLimiter
from harness.registry.tool import ToolResult
from harness.tools.builtin.fetch_url import FetchUrlTool
from harness.tools.builtin.web_search import WebSearchTool


# --- web_search ---
def test_web_search_returns_structured_results():
    ep = EndpointDef(url="https://test.example/search")
    tool = WebSearchTool(ep)
    fake = ToolResult(ok=True, data={"organic": [{"title": "A", "link": "http://a"}]})
    with patch.object(tool.executor, "execute", return_value=fake):
        r = tool.run(query="AI", num_results=1)
    assert r.ok
    assert len(r.data["results"]) == 1
    assert r.data["query_used"] == "AI"


def test_web_search_connection_error():
    ep = EndpointDef(url="http://dead.example")
    tool = WebSearchTool(ep)
    r = tool.run(query="x")
    assert not r.ok
    assert "Connection" in r.error or "HTTP" in r.error


# --- fetch_url ---
def test_fetch_url_returns_content():
    ep = EndpointDef(url="https://r.jina.ai/{{target_url}}")
    tool = FetchUrlTool(ep)
    fake = ToolResult(ok=True, data={"data": "hello world"})
    with patch.object(tool.executor, "execute", return_value=fake):
        r = tool.run(url="https://example.com")
    assert r.ok
    assert "hello world" in r.data["content"]


def test_fetch_url_special_chars():
    ep = EndpointDef(url="https://r.jina.ai/{{target_url}}")
    tool = FetchUrlTool(ep)
    fake = ToolResult(ok=True, data={"data": "page"})
    with patch.object(tool.executor, "execute", return_value=fake):
        r = tool.run(url="https://example.com/path?a=1&b=2")
    assert r.ok
    assert r.data["url"] == "https://example.com/path?a=1&b=2"


def test_fetch_url_truncation():
    ep = EndpointDef(url="https://r.jina.ai/{{target_url}}")
    tool = FetchUrlTool(ep, max_content_tokens=4)
    big = "x" * 50000
    fake = ToolResult(ok=True, data={"data": big})
    with patch.object(tool.executor, "execute", return_value=fake):
        r = tool.run(url="https://example.com")
    assert r.ok
    assert r.data.get("content_truncated") is True


# --- rate limiter ---
def test_rate_limiter_allows_within_limit():
    limiter = RateLimiter(requests_per_minute=5, requests_per_day=100)
    for _ in range(5):
        assert limiter.allow() is True


def test_rate_limiter_blocks_when_exhausted():
    limiter = RateLimiter(requests_per_minute=2, requests_per_day=100)
    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is False


# --- registry ---
def test_registry_list_schemas():
    reg = ToolRegistry()
    reg.register(WebSearchTool())
    schemas = reg.list_schemas()
    assert any(s["function"]["name"] == "web_search" for s in schemas)


def test_registry_failover():
    reg = ToolRegistry()
    primary = WebSearchTool(EndpointDef(url="http://dead1"))
    fallback = WebSearchTool(EndpointDef(url="http://dead2"))
    reg._tools["web_search"] = [primary, fallback]
    r = reg.dispatch("web_search", query="x")
    assert not r.ok
    assert "All endpoints" in r.error or "Connection" in r.error or "HTTP" in r.error


def test_registry_unknown_tool():
    reg = ToolRegistry()
    r = reg.dispatch("nonexistent")
    assert not r.ok
    assert "Unknown" in r.error
