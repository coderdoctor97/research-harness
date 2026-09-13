# P8 — Default Tool Suite tests (P8.T1–T5)
from __future__ import annotations

from unittest.mock import patch

from harness.llm.client import LLMClient
from harness.registry.tool import ToolResult
from harness.tools.builtin.academic_search import AcademicSearchTool
from harness.tools.builtin.compute import ComputeTool
from harness.tools.builtin.extract_links import ExtractLinksTool
from harness.tools.builtin.news_search import NewsSearchTool
from harness.tools.builtin.summarize_page import SummarizePageTool


# --- academic_search ---
def test_academic_search_parses_arxiv_xml():
    tool = AcademicSearchTool()
    xml_response = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Transformer Architecture</title>
    <id>http://arxiv.org/abs/1706.03762</id>
    <author><name>A. Vaswani</name></author>
    <summary>The transformer architecture.</summary>
    <published>2017-06-12</published>
  </entry>
</feed>"""
    fake = ToolResult(ok=True, data=xml_response)
    with patch.object(tool._executor, "execute", return_value=fake):
        r = tool.run(query="transformer", num_results=1)
    assert r.ok
    assert len(r.data["results"]) == 1
    assert "Transformer" in r.data["results"][0]["title"]
    assert any("Vaswani" in a for a in r.data["results"][0]["authors"])


def test_academic_search_connection_error():
    tool = AcademicSearchTool()
    fake = ToolResult(ok=False, error="Connection refused")
    with patch.object(tool._executor, "execute", return_value=fake):
        r = tool.run(query="test")
    assert not r.ok


# --- news_search ---
def test_news_search_parses_articles():
    tool = NewsSearchTool()
    news_data = {"articles": [{"title": "Climate news", "url": "http://news.com/1", "source": {"name": "AP"}, "publishedAt": "2026-09-09", "description": "News about climate."}]}
    fake = ToolResult(ok=True, data=news_data)
    with patch.object(tool._executor, "execute", return_value=fake):
        r = tool.run(query="climate", recency="this_week")
    assert r.ok
    assert r.data["results"][0]["title"] == "Climate news"
    assert r.data["results"][0]["source"] == "AP"


def test_news_search_recency_date_range():
    from harness.tools.builtin.news_search import _recency_to_date
    assert "2026" in _recency_to_date("this_week")
    assert "2026" in _recency_to_date("today")
    assert "2026" in _recency_to_date("this_month")


# --- extract_links ---
def test_extract_links_markdown():
    tool = ExtractLinksTool()
    fake = ToolResult(ok=True, data={"content": "[Google](https://google.com) and [GitHub](https://github.com)"})
    with patch.object(tool._fetcher, "run", return_value=fake):
        r = tool.run(url="https://example.com")
    assert r.ok
    assert r.data["count"] == 2
    assert any(l["url"] == "https://google.com" for l in r.data["links"])


def test_extract_links_filter_pattern():
    tool = ExtractLinksTool()
    fake = ToolResult(ok=True, data={"content": "[Google](https://google.com) [Reddit](https://reddit.com)"})
    with patch.object(tool._fetcher, "run", return_value=fake):
        r = tool.run(url="https://example.com", filter_pattern="reddit")
    assert r.ok
    assert r.data["count"] == 1
    assert r.data["links"][0]["url"] == "https://reddit.com"


# --- summarize_page ---
def test_summarize_page_no_client_error():
    tool = SummarizePageTool(llm_client=None)
    fake = ToolResult(ok=True, data={"content": "Long article content here."})
    with patch.object(tool._fetcher, "run", return_value=fake):
        r = tool.run(url="https://example.com")
    assert not r.ok
    assert "No LLM" in r.error


def test_summarize_page_with_mock_client():
    mock_client = LLMClient.__new__(LLMClient)
    mock_client.chat = lambda prompt: "Summary: key points.\n- point one\n- point two"
    tool = SummarizePageTool(llm_client=mock_client)
    fake = ToolResult(ok=True, data={"content": "Long article about AI." * 100})
    with patch.object(tool._fetcher, "run", return_value=fake):
        r = tool.run(url="https://example.com", focus="AI", max_length="brief")
    assert r.ok
    assert "Summary" in r.data["summary"]
    assert len(r.data["key_points"]) > 0


# --- compute ---
def test_compute_basic_arithmetic():
    tool = ComputeTool()
    assert tool.run(expression="2+3").data["result"] == 5
    assert tool.run(expression="2*3").data["result"] == 6
    assert tool.run(expression="10/3").data["result"] == 10 / 3
    assert tool.run(expression="2**8").data["result"] == 256
    assert tool.run(expression="(1+2)*4").data["result"] == 12


def test_compute_power_operator():
    tool = ComputeTool()
    r = tool.run(expression="2^32")
    assert r.ok
    assert r.data["result"] == 4294967296


def test_compute_rejects_import():
    tool = ComputeTool()
    r = tool.run(expression="import os")
    assert not r.ok
    assert "Disallowed" in r.error or "not allowed" in r.error


def test_compute_rejects_unknown_name():
    tool = ComputeTool()
    r = tool.run(expression="os.system('ls')")
    assert not r.ok


def test_compute_rejects_function_calls():
    tool = ComputeTool()
    r = tool.run(expression="exec('1')")
    assert not r.ok


def test_compute_malformed_expression():
    tool = ComputeTool()
    r = tool.run(expression="2+")
    assert not r.ok
