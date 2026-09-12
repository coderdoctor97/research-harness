# MCP client — connect to MCP servers via stdio or SSE
from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import httpx


class MCPConnectionError(Exception):
    pass


class MCPClient:
    """Minimal MCP client supporting stdio and SSE transports."""

    def __init__(self, command: str, args: list[str] | None = None, env: dict | None = None) -> None:
        self.command = command
        self.args = args or []
        self.env = env or {}
        self._process: Any = None
        self._request_id = 0
        self._url: str | None = None
        self._sse_mode = command.startswith("http://") or command.startswith("https://")
        if self._sse_mode:
            self._url = self.command.rstrip("/") + "/sse"

    async def connect(self) -> None:
        if self.command.startswith("http://") or self.command.startswith("https://"):
            self._sse_mode = True
            self._url = self.command.rstrip("/") + "/sse"
            return
        try:
            merged_env = {**os.environ, **self.env}
            self._process = await asyncio.create_subprocess_exec(
                self.command, *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=merged_env,
            )
        except FileNotFoundError:
            raise MCPConnectionError(f"Command not found: {self.command}")
        except Exception as exc:
            raise MCPConnectionError(f"Failed to start: {exc}") from exc

    async def disconnect(self) -> None:
        if self._process:
            try:
                self._process.stdin.close()
                await self._process.wait()
            except Exception:
                pass
            self._process = None

    async def initialize(self) -> dict:
        return await self._request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "llm-harness", "version": "0.1.0"},
        })

    async def list_tools(self) -> list[dict]:
        resp = await self._request("tools/list", {})
        return resp.get("tools", [])

    async def call_tool(self, name: str, arguments: dict) -> Any:
        resp = await self._request("tools/call", {"name": name, "arguments": arguments})
        return resp.get("content", [])

    async def _request(self, method: str, params: dict) -> dict:
        self._request_id += 1
        payload = {"jsonrpc": "2.0", "id": self._request_id, "method": method, "params": params}
        if self._sse_mode or self._url:
            return await self._request_sse(payload)
        return await self._request_stdio(payload)

    async def _request_stdio(self, payload: dict) -> dict:
        if not self._process or not self._process.stdin:
            raise MCPConnectionError("Not connected")
        try:
            line = json.dumps(payload) + "\n"
            self._process.stdin.write(line.encode())
            await self._process.stdin.drain()
            raw = await asyncio.wait_for(self._process.stdout.readline(), timeout=30)
            if not raw:
                raise MCPConnectionError("Server closed connection")
            return json.loads(raw.decode()).get("result", {})
        except asyncio.TimeoutError:
            raise MCPConnectionError("Timeout waiting for response")
        except MCPConnectionError:
            raise
        except Exception as exc:
            raise MCPConnectionError(f"Request failed: {exc}") from exc

    async def _request_sse(self, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                self._url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            r.raise_for_status()
            data = r.json()
            return data.get("result", {})

    async def ping(self) -> bool:
        try:
            await self.initialize()
            return True
        except Exception:
            return False
