# MCP tools registry — exposes MCP tools as harness tools
from __future__ import annotations

import asyncio
from typing import Any

from harness.mcp.client import MCPClient, MCPConnectionError
from harness.mcp.browser import BrowserMCP
from harness.mcp.search import SearchMCP
from harness.registry.tool import Tool, ToolResult


class MCPToolDefinition(Tool):
    """Wraps an MCP tool as a harness Tool."""

    def __init__(self, mcp_tool: dict, client: MCPClient) -> None:
        super().__init__()
        self.name = mcp_tool.get("name", "unknown")
        self.description = mcp_tool.get("description", "")
        self.parameters = mcp_tool.get("inputSchema", {"type": "object", "properties": {}})
        self._client = client
        self._mcp_name = self.name

    def run(self, **params) -> ToolResult:
        try:
            coro = self._client.call_tool(self._mcp_name, params)
            try:
                result = asyncio.run(coro)
            except RuntimeError:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    result = pool.submit(asyncio.run, coro).result()
            return ToolResult(ok=True, data=result)
        except MCPConnectionError as exc:
            return ToolResult(ok=False, error=str(exc))
        except Exception as exc:
            return ToolResult(ok=False, error=str(exc))


class MCPToolRegistry:
    """Manages MCP server connections and their tool registrations."""

    def __init__(self) -> None:
        self._clients: dict[str, MCPClient] = {}
        self._tools_by_server: dict[str, list[MCPToolDefinition]] = {}
        self._browser: BrowserMCP | None = None
        self._search: SearchMCP | None = None

    async def connect_server(self, name: str, command: str, args: list[str], env: dict | None = None) -> dict:
        client = MCPClient(command=command, args=args, env=env)
        await client.connect()
        try:
            init_result = await client.initialize()
            tools_data = await client.list_tools()
        except Exception as exc:
            await client.disconnect()
            raise MCPConnectionError(f"Init failed: {exc}") from exc

        tool_defs = []
        server_tools = []
        for t in tools_data:
            td = MCPToolDefinition(t, client)
            server_tools.append(td)
            tool_defs.append(td.name)

        self._tools_by_server[name] = server_tools
        self._clients[name] = client
        return {"status": "connected", "server": name, "tools": tool_defs}

    async def disconnect_server(self, name: str) -> None:
        client = self._clients.pop(name, None)
        if client:
            await client.disconnect()
        self._tools_by_server.pop(name, None)

    def get_tools(self) -> list[MCPToolDefinition]:
        out = []
        for tools in self._tools_by_server.values():
            out.extend(tools)
        return out

    def get_tool(self, name: str) -> MCPToolDefinition | None:
        for tools in self._tools_by_server.values():
            for t in tools:
                if t.name == name:
                    return t
        return None

    async def connect_browser(self, command: str = "npx", args: list[str] | None = None) -> dict:
        self._browser = BrowserMCP()
        return await self._browser.start(command, args)

    async def connect_search(self, command: str = "npx", args: list[str] | None = None) -> dict:
        self._search = SearchMCP()
        return await self._search.start(command, args)

    def get_browser_tools(self) -> list[BrowserMCP]:
        if self._browser:
            return self._browser.get_tools()
        return []

    def get_search_tool(self) -> SearchMCPTool | None:
        if self._search:
            return self._search.get_tool()
        return None

    async def shutdown(self) -> None:
        for name in list(self._clients.keys()):
            await self.disconnect_server(name)
