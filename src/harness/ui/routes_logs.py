# P9.T5 — Tool execution log viewer: timing + result preview, no auth headers/keys
from __future__ import annotations

import time

from fastapi import FastAPI

_log: list[dict] = []


def log_call(tool_name: str, params: dict, result, duration_ms: float) -> None:
    _log.append({"tool": tool_name, "params": _sanitize(params), "ok": result.ok if hasattr(result, "ok") else True, "duration_ms": duration_ms, "ts": time.time()})


def _sanitize(params: dict) -> dict:
    sanitized = {}
    for k, v in params.items():
        if any(s in k.lower() for s in ("key", "token", "secret", "password", "auth")):
            sanitized[k] = "***"
        else:
            sanitized[k] = v
    return sanitized


def mount(app: FastAPI) -> None:
    @app.get("/api/logs")
    async def get_logs():
        return _log[-100:]

    @app.delete("/api/logs")
    async def clear_logs():
        _log.clear()
        return {"status": "cleared"}
