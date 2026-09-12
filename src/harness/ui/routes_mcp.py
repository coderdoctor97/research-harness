# MCP management routes — server CRUD + tool listing
from __future__ import annotations

from fastapi import FastAPI, HTTPException

from harness.ui._mcp_state import _mcp_servers


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

    @app.get("/api/mcp/tools")
    async def list_mcp_tools():
        tools = []
        for srv in _mcp_servers:
            for t in srv.get("tools", []):
                tools.append(t)
        return {"tools": tools}
