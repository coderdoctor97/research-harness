# MCP management routes — server CRUD, free presets, tool listing + built-in calls
from __future__ import annotations

import asyncio

from fastapi import FastAPI, HTTPException

from harness.mcp.builtin import BUILTIN_SERVERS
from harness.ui._mcp_state import _mcp_servers, restore_defaults

# Optional free/community MCP servers users can install with one click.
# Built-ins (builtin-fetcher, builtin-search) need nothing; presets may need
# Node/uvx on PATH and (for Brave) a free API key.
MCP_PRESETS: dict[str, dict] = {
    "builtin-fetcher": {
        "label": "Endpoint Fetcher",
        "description": "Browse and read any URL (fetch_url, extract_links). Built in — free, no setup.",
        "free": True, "requires_key": False, "builtin": True,
    },
    "builtin-search": {
        "label": "DuckDuckGo Search",
        "description": "Web search via DuckDuckGo (web_search). Built in — free, no API key.",
        "free": True, "requires_key": False, "builtin": True,
    },
    "brave-search": {
        "label": "Brave Search",
        "description": "Brave Search MCP server. Free-tier API key required (BRAVE_API_KEY).",
        "free": True, "requires_key": True, "key_env": "BRAVE_API_KEY", "builtin": False,
        "command": "npx", "args": ["-y", "@modelcontextprotocol/server-brave-search"],
    },
    "fetch-stdio": {
        "label": "Fetch (official stdio)",
        "description": "Official Model Context Protocol fetch server via uvx.",
        "free": True, "requires_key": False, "builtin": False,
        "command": "uvx", "args": ["mcp-server-fetch"],
    },
    "ddg-stdio": {
        "label": "DuckDuckGo (stdio)",
        "description": "DuckDuckGo MCP server as a separate process via uvx.",
        "free": True, "requires_key": False, "builtin": False,
        "command": "uvx", "args": ["duckduckgo-mcp-server"],
    },
}


def mount(app: FastAPI) -> None:
    @app.get("/api/mcp/servers")
    async def list_mcp_servers():
        return {"servers": list(_mcp_servers)}

    @app.post("/api/mcp/servers")
    async def add_mcp_server(payload: dict):
        name = payload.get("name", "").strip()
        command = payload.get("command", "").strip()
        args = payload.get("args", [])
        env = payload.get("env", {})
        if not name or not command:
            raise HTTPException(400, "name and command required")
        for s in _mcp_servers:
            if s.get("name") == name:
                s["command"] = command
                s["args"] = list(args)
                s["env"] = dict(env)
                return {"servers": list(_mcp_servers)}
        entry = {"name": name, "command": command, "args": list(args), "env": dict(env), "tools": []}
        _mcp_servers.append(entry)
        return {"servers": list(_mcp_servers)}

    @app.delete("/api/mcp/servers/{name}")
    async def remove_mcp_server(name: str):
        _mcp_servers[:] = [s for s in _mcp_servers if s.get("name") != name]
        return {"servers": list(_mcp_servers)}

    @app.get("/api/mcp/presets")
    async def list_mcp_presets():
        installed = {s.get("name") for s in _mcp_servers}
        presets = []
        for preset_id, preset in MCP_PRESETS.items():
            entry = dict(preset)
            entry["id"] = preset_id
            entry["installed"] = preset_id in installed or preset.get("builtin", False)
            presets.append(entry)
        return {"presets": presets}

    @app.post("/api/mcp/presets/{preset_id}/install")
    async def install_mcp_preset(preset_id: str, payload: dict | None = None):
        preset = MCP_PRESETS.get(preset_id)
        if preset is None:
            raise HTTPException(404, f"unknown preset: {preset_id}")
        if preset.get("builtin"):
            restore_defaults()
            return {"status": "ready", "servers": list(_mcp_servers)}
        import os
        if preset.get("requires_key"):
            key_env = preset.get("key_env", "")
            provided = (payload or {}).get("api_key", "") if payload else ""
            if provided:
                os.environ[key_env] = provided
            if not os.environ.get(key_env):
                raise HTTPException(400, f"{key_env} required — set it in Keys or pass api_key")
        entry = {
            "name": preset_id,
            "command": preset["command"],
            "args": list(preset.get("args", [])),
            "env": {preset.get("key_env", ""): "env"} if preset.get("requires_key") else {},
            "tools": [],
            "preset": True,
        }
        for s in _mcp_servers:
            if s.get("name") == preset_id:
                s.update(entry)
                return {"status": "installed", "servers": list(_mcp_servers)}
        _mcp_servers.append(entry)
        return {"status": "installed", "servers": list(_mcp_servers)}

    @app.get("/api/mcp/tools")
    async def list_mcp_tools():
        tools = []
        for srv in _mcp_servers:
            for t in srv.get("tools", []):
                item = dict(t) if isinstance(t, dict) else {"name": str(t)}
                item.setdefault("server", srv.get("name"))
                tools.append(item)
        return {"tools": tools}

    @app.post("/api/mcp/tools/call")
    async def call_mcp_tool(payload: dict):
        """Call a tool on a built-in server. Stdio/SSE servers are reached by the
        agent loop via MCPClient instead."""
        server_name = payload.get("server", "")
        tool_name = payload.get("tool", "")
        arguments = payload.get("arguments", {})
        server = BUILTIN_SERVERS.get(server_name)
        if server is None:
            raise HTTPException(400, f"not a built-in server: {server_name}")
        try:
            result = await asyncio.wait_for(server.call_tool(tool_name, arguments), timeout=30)
        except asyncio.TimeoutError:
            raise HTTPException(504, "tool call timed out")
        return {"server": server_name, "tool": tool_name, "result": result}
