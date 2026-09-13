"""Built-in, in-process MCP servers — free browsing capabilities with zero setup.

These implement the same surface as MCPClient (list_tools / call_tool) but run
inside the harness process: no npx, no API keys, works out of the box.

Default services provided:
  - builtin-fetcher : fetch_url, extract_links  (endpoint fetcher for browsing)
  - builtin-search  : web_search                (DuckDuckGo HTML — free, no key)
"""
from __future__ import annotations

import asyncio
import html as _html
import json
import re
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import httpx

from harness.registry.index import ToolRegistry
from harness.registry.tool import Tool, ToolResult

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 llm-research-harness/0.1"
)

<<<<<<< HEAD
# A4.1.1 (Crawl4AI pattern): also strip structural noise — nav, footer,
# header, aside, form — so page chrome/banners never reach the LLM.
_TAG_RE = re.compile(
    r"<(script|style|noscript|svg|head|nav|footer|header|aside|form|iframe)[^>]*>.*?</\1>",
    re.S | re.I,
)
=======
_TAG_RE = re.compile(r"<(script|style|noscript|svg|head)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
>>>>>>> master
_ANY_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_NL_RE = re.compile(r"\n{3,}")
_HREF_RE = re.compile(r"""<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>(.*?)</a>""", re.DOTALL | re.IGNORECASE)


def strip_html(raw: str) -> str:
    """Crush HTML to readable plain text (no external deps)."""
    text = _TAG_RE.sub(" ", raw)
    text = re.sub(r"<(br|/p|/div|/li|/h[1-6]|/tr)\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = _ANY_TAG_RE.sub(" ", text)
    text = _html.unescape(text)
    text = _WS_RE.sub(" ", text)
    text = _NL_RE.sub("\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def _text_content(content: list[dict]) -> str:
    """MCP content list -> plain JSON payload (dict when possible)."""
    for block in content or []:
        if isinstance(block, dict) and block.get("type") == "text":
            try:
                return json.loads(block["text"])
            except (json.JSONDecodeError, KeyError, TypeError):
                return block.get("text", "")
    return content


# ---------------------------------------------------------------------------
# Endpoint fetcher — browse any URL
# ---------------------------------------------------------------------------

async def _fetch_url(args: dict) -> dict:
    url = (args.get("url") or "").strip()
    max_chars = int(args.get("max_chars") or 8000)
    if not url:
        return {"ok": False, "error": "url is required"}
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        async with httpx.AsyncClient(
            timeout=20.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}
        ) as client:
            r = await client.get(url)
        content_type = r.headers.get("content-type", "")
        body = r.text or ""
        text = strip_html(body) if "html" in content_type.lower() or body.lstrip().startswith("<") else body
        truncated = len(text) > max_chars
        return {
            "ok": True,
            "url": url,
            "final_url": str(r.url),
            "status": r.status_code,
            "content_type": content_type,
            "content": text[:max_chars],
            "truncated": truncated,
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "url": url, "error": f"{type(exc).__name__}: {exc}"}


async def _extract_links(args: dict) -> dict:
    url = (args.get("url") or "").strip()
    limit = int(args.get("limit") or 30)
    if not url:
        return {"ok": False, "error": "url is required"}
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        async with httpx.AsyncClient(
            timeout=20.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}
        ) as client:
            r = await client.get(url)
        links = []
        for href, inner in _HREF_RE.findall(r.text or ""):
            if href.startswith(("javascript:", "mailto:", "#")):
                continue
            absolute = urljoin(str(r.url), unquote(href))
            title = strip_html(inner)[:120]
            links.append({"href": absolute, "text": title})
            if len(links) >= limit:
                break
        return {"ok": True, "url": str(r.url), "links": links, "count": len(links)}
    except httpx.HTTPError as exc:
        return {"ok": False, "url": url, "error": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------------------
# DuckDuckGo search — free, no API key
# ---------------------------------------------------------------------------

_DDG_RESULT_RE = re.compile(
    r"""<a[^>]*class=["']result__a["'][^>]*href=["']([^"']+)["'][^>]*>(.*?)</a>"""
    r""".*?"""
    r"""<a[^>]*class=["']result__snippet["'][^>]*>(.*?)</a>""",
    re.DOTALL,
)

# DuckDuckGo Lite markup (fallback endpoint, single-quoted attributes)
_DDG_LITE_RE = re.compile(
    r"""<a[^>]*href=["']([^"']+)["'][^>]*class=["']result-link["'][^>]*>(.*?)</a>"""
    r""".*?"""
    r"""<td[^>]*class=["']result-snippet["'][^>]*>(.*?)</td>""",
    re.DOTALL,
)
_DDG_LITE_RE_ALT = re.compile(
    r"""<a[^>]*class=["']result-link["'][^>]*href=["']([^"']+)["'][^>]*>(.*?)</a>"""
    r""".*?"""
    r"""<td[^>]*class=["']result-snippet["'][^>]*>(.*?)</td>""",
    re.DOTALL,
)


def _resolve_ddg_href(href: str) -> str:
    """DDG wraps results in //duckduckgo.com/l/?uddg=<encoded> redirects."""
    if href.startswith("//"):
        href = "https:" + href
    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        uddg = parse_qs(parsed.query).get("uddg", [""])[0]
        if uddg:
            return uddg
    return href


def parse_ddg_html(raw: str, max_results: int = 5) -> list[dict]:
    """Parse results from either the /html/ or /lite/ DuckDuckGo endpoints."""
    matches = _DDG_RESULT_RE.findall(raw)
    if not matches:
        matches = _DDG_LITE_RE.findall(raw) or _DDG_LITE_RE_ALT.findall(raw)
    results = []
    for href, title_html, snippet_html in matches:
        results.append({
            "title": strip_html(title_html),
            "url": _resolve_ddg_href(_html.unescape(href)),
            "snippet": strip_html(snippet_html)[:400],
        })
        if len(results) >= max_results:
            break
    return results


async def _web_search(args: dict) -> dict:
    query = (args.get("query") or "").strip()
    max_results = int(args.get("max_results") or 5)
    if not query:
        return {"ok": False, "error": "query is required"}
    targets = ("https://lite.duckduckgo.com/lite/", "https://duckduckgo.com/html/")
    last_error = ""
    try:
        async with httpx.AsyncClient(
            timeout=20.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}
        ) as client:
            for target in targets:
                try:
                    r = await client.post(target, data={"q": query})
                    r.raise_for_status()
                except httpx.HTTPError as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                    continue
                results = parse_ddg_html(r.text or "", max_results)
                if results:
                    return {
                        "ok": True,
                        "query_used": query,
                        "result_count": len(results),
                        "results": results,
                        "endpoint": target,
                    }
                last_error = f"no parseable results from {target}"
        return {"ok": False, "query_used": query, "result_count": 0, "error": last_error or "no results"}
    except httpx.HTTPError as exc:
        return {"ok": False, "query_used": query, "error": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------------------
# Server registry
# ---------------------------------------------------------------------------

class BuiltinServer:
    """An in-process MCP-compatible server."""

    transport = "builtin"

    def __init__(self, name: str, description: str, tools: dict[str, dict]) -> None:
        self.name = name
        self.description = description
        self._tools = tools  # tool name -> {description, inputSchema, handler}

    def list_tools(self) -> list[dict]:
        return [
            {"name": n, "description": t["description"], "inputSchema": t["inputSchema"]}
            for n, t in self._tools.items()
        ]

    async def call_tool(self, name: str, arguments: dict) -> Any:
        tool = self._tools.get(name)
        if tool is None:
            return {"ok": False, "error": f"unknown tool: {name}"}
        return await tool["handler"](arguments or {})


FETCHER_SERVER = BuiltinServer(
    name="builtin-fetcher",
    description="Built-in endpoint fetcher — browse and read any URL. Free, no API key, no setup.",
    tools={
        "fetch_url": {
            "description": "Fetch a URL and return its readable text content (HTML stripped).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Target URL"},
                    "max_chars": {"type": "integer", "description": "Max characters to return (default 8000)"},
                },
                "required": ["url"],
            },
            "handler": _fetch_url,
        },
        "extract_links": {
            "description": "Fetch a URL and return its outgoing links (href + text).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Target URL"},
                    "limit": {"type": "integer", "description": "Max links (default 30)"},
                },
                "required": ["url"],
            },
            "handler": _extract_links,
        },
    },
)

SEARCH_SERVER = BuiltinServer(
    name="builtin-search",
    description="Built-in DuckDuckGo web search — free, no API key.",
    tools={
        "web_search": {
            "description": "Search the web with DuckDuckGo. Returns titles, URLs, snippets.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Max results (default 5)"},
                },
                "required": ["query"],
            },
            "handler": _web_search,
        },
    },
)

BUILTIN_SERVERS: dict[str, BuiltinServer] = {
    FETCHER_SERVER.name: FETCHER_SERVER,
    SEARCH_SERVER.name: SEARCH_SERVER,
}


class BuiltinTool(Tool):
    def __init__(self, server: BuiltinServer, tool: dict) -> None:
        self.name = tool["name"]
        self.description = tool.get("description", "")
        self.parameters = tool.get("inputSchema", {"type": "object", "properties": {}})
        self._server = server

    def run(self, **params) -> ToolResult:
        result = asyncio.run(self._server.call_tool(self.name, params))
        return ToolResult(ok=bool(result.get("ok")), data=result, error=result.get("error"))


def builtin_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for server in BUILTIN_SERVERS.values():
        for tool in server.list_tools():
            registry.register(BuiltinTool(server, tool))
    return registry


def server_entries() -> list[dict]:
    """_mcp_state-shaped entries for the built-in servers."""
    return [
        {
            "name": srv.name,
            "description": srv.description,
            "command": "builtin",
            "args": [],
            "env": {},
            "transport": "builtin",
            "builtin": True,
            "free": True,
            "status": "ready",
            "tools": srv.list_tools(),
        }
        for srv in BUILTIN_SERVERS.values()
    ]
