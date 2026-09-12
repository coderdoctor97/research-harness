# Search MCP — integration with DuckDuckGo MCP for web search
from __future__ import annotations

from typing import Any

from harness.mcp.client import MCPClient, MCPConnectionError


class SearchMCPTool:
    name = "web_search_mcp"
    description = "Search the web using DuckDuckGo via MCP"
    parameters = {
        "query": {"type": "string", "description": "Search query"},
        "max_results": {"type": "integer", "description": "Max results (default 5)", "default": 5},
    }

    def __init__(self, client: MCPClient) -> None:
        self._client = client

    async def run(self, **params) -> dict:
        query = params.get("query", "")
        max_results = params.get("max_results", 5)
        try:
            result = await self._client.call_tool("web_search", {"query": query, "max_results": max_results})
            return {"ok": True, "data": result, "query": query}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


class SearchMCP:
    """Manager for DuckDuckGo MCP server."""

    def __init__(self) -> None:
        self._client: MCPClient | None = None

    async def start(self, command: str = "npx", args: list[str] | None = None) -> dict:
        args = args or ["-y", "@modelcontextprotocol/server-duckduckgo"]
        client = MCPClient(command=command, args=args)
        await client.connect()
        tools = await client.list_tools()
        self._client = client
        return {"status": "connected", "tools": [t.get("name", "") for t in tools]}

    async def stop(self) -> None:
        if self._client:
            await self._client.disconnect()
            self._client = None

    def get_tool(self) -> SearchMCPTool | None:
        if not self._client:
            return None
        return SearchMCPTool(self._client)
