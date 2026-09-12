# Browser MCP — integration with browsermcp for browser automation
from __future__ import annotations

from typing import Any

from harness.mcp.client import MCPClient, MCPConnectionError


class BrowserMCPTool:
    name = "browser_automation"
    description = "Automate browser interactions (navigate, click, type, screenshot, etc.)"
    parameters = {
        "action": {"type": "string", "description": "Action to perform: navigate, click, type, screenshot, scroll, snapshot"},
        "url": {"type": "string", "description": "URL for navigate action"},
        "selector": {"type": "string", "description": "CSS selector for click/type actions"},
        "text": {"type": "string", "description": "Text to type"},
    }

    def __init__(self, client: MCPClient) -> None:
        self._client = client

    async def run(self, **params) -> dict:
        action = params.get("action", "")
        args = {k: v for k, v in params.items() if k != "action" and v}
        try:
            result = await self._client.call_tool("browser_" + action, args)
            return {"ok": True, "data": result}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


class BrowserMCP:
    """Manager for Browser MCP server connections."""

    def __init__(self) -> None:
        self._client: MCPClient | None = None

    async def start(self, command: str = "npx", args: list[str] | None = None) -> dict:
        args = args or ["-y", "@anthropic/browsermcp"]
        client = MCPClient(command=command, args=args)
        await client.connect()
        tools = await client.list_tools()
        self._client = client
        return {"status": "connected", "tools": [t.get("name", "") for t in tools]}

    async def stop(self) -> None:
        if self._client:
            await self._client.disconnect()
            self._client = None

    def get_tools(self) -> list[BrowserMCPTool]:
        if not self._client:
            return []
        return [BrowserMCPTool(self._client)]
