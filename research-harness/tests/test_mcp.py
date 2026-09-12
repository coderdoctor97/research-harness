# Tests for MCP client, browser, search, and registry modules
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from harness.mcp.client import MCPClient, MCPConnectionError
from harness.mcp.registry import MCPToolRegistry, MCPToolDefinition
from harness.ui._mcp_state import _mcp_servers


# ---- helpers ----

def _reset_mcp_state():
    _mcp_servers.clear()


# ---- MCPClient tests ----

class TestMCPClient:
    def test_init_stdio(self):
        client = MCPClient(command="npx", args=["-y", "server"])
        assert client.command == "npx"
        assert client.args == ["-y", "server"]
        assert client._sse_mode is False
        assert client._url is None

    def test_init_sse_mode(self):
        client = MCPClient(command="https://example.com/mcp")
        assert client._sse_mode is True
        assert client._url == "https://example.com/mcp/sse"

    def test_init_http_sse(self):
        client = MCPClient(command="http://example.com/mcp")
        assert client._sse_mode is True
        assert client._url == "http://example.com/mcp/sse"

    @pytest.mark.asyncio
    async def test_connect_sse(self):
        client = MCPClient(command="https://example.com/mcp")
        await client.connect()
        assert client._sse_mode is True
        assert client._url == "https://example.com/mcp/sse"

    @pytest.mark.asyncio
    async def test_connect_stdio(self):
        mock_process = AsyncMock()
        mock_process.stdin = AsyncMock()
        mock_process.stdout = AsyncMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            client = MCPClient(command="python", args=["-m", "server"])
            await client.connect()
            assert client._process is mock_process

    @pytest.mark.asyncio
    async def test_connect_stdio_file_not_found(self):
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError("not found")):
            client = MCPClient(command="nonexistent")
            with pytest.raises(MCPConnectionError, match="Command not found"):
                await client.connect()

    @pytest.mark.asyncio
    async def test_initialize_sse(self):
        client = MCPClient(command="https://example.com/mcp")
        with patch.object(client, "_request_sse", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"protocolVersion": "2024-11-05", "capabilities": {}}
            result = await client.initialize()
        assert result["protocolVersion"] == "2024-11-05"
        call = mock_req.call_args[0][0]
        assert call["method"] == "initialize"
        assert call["jsonrpc"] == "2.0"

    @pytest.mark.asyncio
    async def test_list_tools_sse(self):
        client = MCPClient(command="https://example.com/mcp")
        with patch.object(client, "_request_sse", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"tools": [{"name": "tool1", "description": "desc"}]}
            tools = await client.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "tool1"

    @pytest.mark.asyncio
    async def test_call_tool_sse(self):
        client = MCPClient(command="https://example.com/mcp")
        with patch.object(client, "_request_sse", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"content": [{"type": "text", "text": "result"}]}
            result = await client.call_tool("search", {"query": "test"})
        assert result == [{"type": "text", "text": "result"}]
        call = mock_req.call_args[0][0]
        assert call["method"] == "tools/call"
        assert call["params"]["name"] == "search"

    @pytest.mark.asyncio
    async def test_disconnect_sse(self):
        client = MCPClient(command="https://example.com/mcp")
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_ping_true(self):
        client = MCPClient(command="https://example.com/mcp")
        with patch.object(client, "_request_sse", new_callable=AsyncMock):
            result = await client.ping()
        assert result is True

    @pytest.mark.asyncio
    async def test_ping_false(self):
        client = MCPClient(command="https://example.com/mcp")
        with patch.object(client, "_request_sse", side_effect=MCPConnectionError("fail")):
            result = await client.ping()
        assert result is False

    @pytest.mark.asyncio
    async def test_request_stdio_timeout(self):
        client = MCPClient(command="python", args=["server"])
        mock_process = AsyncMock()
        mock_process.stdin = AsyncMock()
        mock_process.stdout = AsyncMock()

        async def fake_readline():
            raise asyncio.TimeoutError()

        mock_process.stdout.readline = fake_readline

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            await client.connect()
            with pytest.raises(MCPConnectionError):
                await client._request_stdio({"jsonrpc": "2.0", "id": 1, "method": "test", "params": {}})

    @pytest.mark.asyncio
    async def test_disconnect_stdio(self):
        client = MCPClient(command="python", args=["server"])
        mock_process = AsyncMock()
        mock_process.stdin = AsyncMock()
        client._process = mock_process
        await client.disconnect()
        assert client._process is None


# ---- MCPToolDefinition tests ----

class TestMCPToolDefinition:
    def test_run_success(self):
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(return_value={"result": "ok"})

        tool = MCPToolDefinition({"name": "search", "description": "Search", "inputSchema": {}}, mock_client)
        result = tool.run(query="test")
        assert result.ok is True
        assert result.data == {"result": "ok"}

    def test_run_failure(self):
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(side_effect=MCPConnectionError("connection lost"))

        tool = MCPToolDefinition({"name": "search", "description": "Search", "inputSchema": {}}, mock_client)
        result = tool.run(query="test")
        assert result.ok is False
        assert "connection lost" in result.error

    def test_schema(self):
        tool = MCPToolDefinition({"name": "web_search", "description": "Search web", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}}, MagicMock())
        schema = tool.schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "web_search"
        assert schema["function"]["description"] == "Search web"

    def test_base_class_schema(self):
        """Tool base class should produce correct function schema."""
        from harness.registry.tool import Tool
        tool = Tool()
        tool.name = "compute"
        tool.description = "Calculate"
        tool.parameters = {"expr": {"type": "string"}}
        schema = tool.schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "compute"


# ---- MCPToolRegistry tests ----

class TestMCPToolRegistry:
    @pytest.mark.asyncio
    async def test_connect_server_sse(self):
        registry = MCPToolRegistry()
        mock_client = AsyncMock()
        mock_client.initialize.return_value = {"protocolVersion": "2024-11-05"}
        mock_client.list_tools.return_value = [
            {"name": "search_tool", "description": "Search", "inputSchema": {}},
            {"name": "calc_tool", "description": "Calculate", "inputSchema": {}},
        ]

        with patch("harness.mcp.registry.MCPClient", return_value=mock_client):
            result = await registry.connect_server("test-server", "https://example.com", [])

        assert result["status"] == "connected"
        assert result["server"] == "test-server"
        assert len(result["tools"]) == 2
        assert "search_tool" in result["tools"]
        assert "calc_tool" in result["tools"]
        assert len(registry.get_tools()) == 2

    @pytest.mark.asyncio
    async def test_get_tool(self):
        registry = MCPToolRegistry()
        mock_client = AsyncMock()
        mock_client.initialize.return_value = {}
        mock_client.list_tools.return_value = [
            {"name": "my_tool", "description": "desc", "inputSchema": {}},
        ]

        with patch("harness.mcp.registry.MCPClient", return_value=mock_client):
            await registry.connect_server("srv", "https://example.com", [])

        tool = registry.get_tool("my_tool")
        assert tool is not None
        assert tool.name == "my_tool"
        assert tool.description == "desc"

    @pytest.mark.asyncio
    async def test_disconnect_server(self):
        registry = MCPToolRegistry()
        mock_client = AsyncMock()
        mock_client.initialize.return_value = {}
        mock_client.list_tools.return_value = [
            {"name": "t1", "description": "", "inputSchema": {}},
        ]

        with patch("harness.mcp.registry.MCPClient", return_value=mock_client):
            await registry.connect_server("srv", "https://example.com", [])
            assert len(registry.get_tools()) == 1
            await registry.disconnect_server("srv")
            assert len(registry.get_tools()) == 0
        mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown(self):
        registry = MCPToolRegistry()
        mock_client = AsyncMock()
        mock_client.initialize.return_value = {}
        mock_client.list_tools.return_value = [
            {"name": "t1", "description": "", "inputSchema": {}},
        ]

        with patch("harness.mcp.registry.MCPClient", return_value=mock_client):
            await registry.connect_server("srv1", "https://example.com", [])
            await registry.connect_server("srv2", "https://example.com", [])
            assert len(registry.get_tools()) == 2
            await registry.shutdown()
            assert len(registry.get_tools()) == 0

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        registry = MCPToolRegistry()
        mock_client = AsyncMock()
        mock_client.initialize.side_effect = Exception("init failed")

        with patch("harness.mcp.registry.MCPClient", return_value=mock_client):
            with pytest.raises(MCPConnectionError, match="Init failed"):
                await registry.connect_server("srv", "https://example.com", [])

    @pytest.mark.asyncio
    async def test_connect_browser(self):
        registry = MCPToolRegistry()

        with patch("asyncio.create_subprocess_exec", side_effect=OSError("no npx")):
            with patch("harness.mcp.browser.MCPClient") as MockClient:
                mock_client = AsyncMock()
                mock_client.initialize.return_value = {}
                mock_client.list_tools.return_value = [
                    {"name": "browser_navigate", "description": "Navigate browser", "inputSchema": {}},
                ]
                MockClient.return_value = mock_client
                result = await registry.connect_browser("npx", ["-y", "@anthropic/browsermcp"])

        assert result["status"] == "connected"
        browser_tools = registry.get_browser_tools()
        assert len(browser_tools) == 1

    @pytest.mark.asyncio
    async def test_connect_search(self):
        registry = MCPToolRegistry()

        with patch("asyncio.create_subprocess_exec", side_effect=OSError("no npx")):
            with patch("harness.mcp.search.MCPClient") as MockClient:
                mock_client = AsyncMock()
                mock_client.initialize.return_value = {}
                mock_client.list_tools.return_value = [
                    {"name": "web_search", "description": "Web search", "inputSchema": {}},
                ]
                MockClient.return_value = mock_client
                result = await registry.connect_search("npx", ["-y", "server-ddgs"])

        assert result["status"] == "connected"
        search_tool = registry.get_search_tool()
        assert search_tool is not None
        assert search_tool.name == "web_search_mcp"

    def test_get_tool_not_found(self):
        registry = MCPToolRegistry()
        assert registry.get_tool("nonexistent") is None
        assert registry.get_tools() == []

    @pytest.mark.asyncio
    async def test_multiple_servers(self):
        registry = MCPToolRegistry()
        mock1 = AsyncMock()
        mock1.initialize.return_value = {}
        mock1.list_tools.return_value = [{"name": "tool_a", "description": "", "inputSchema": {}}]

        mock2 = AsyncMock()
        mock2.initialize.return_value = {}
        mock2.list_tools.return_value = [{"name": "tool_b", "description": "", "inputSchema": {}}]

        with patch("harness.mcp.registry.MCPClient", side_effect=[mock1, mock2]):
            await registry.connect_server("srv1", "https://a.com", [])
            await registry.connect_server("srv2", "https://b.com", [])

        assert len(registry.get_tools()) == 2
        assert registry.get_tool("tool_a") is not None
        assert registry.get_tool("tool_b") is not None