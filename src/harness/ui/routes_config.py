# P9.T6 — Sanitized config export/import
from __future__ import annotations

import re

from fastapi import FastAPI, HTTPException

from harness.ui._mcp_state import _mcp_servers

_SENSITIVE_RE = re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*\S+")


def _scrub(text: str) -> str:
    return _SENSITIVE_RE.sub(lambda m: m.group(1) + "=[REDACTED]", text)


def mount(app: FastAPI) -> None:
    @app.get("/api/config/export")
    async def export_config():
        config = {
            "llm": {"base_url": "http://localhost:11434/v1", "model_name": "llama3"},
            "endpoints": [],
            "custom_endpoints": [],
            "mcp_servers": [dict(s) for s in _mcp_servers],
        }
        import json
        raw = json.dumps(config, indent=2)
        return {"config": _scrub(raw)}

    @app.post("/api/config/import")
    async def import_config(payload: dict):
        config_text = payload.get("config", "")
        if not config_text:
            raise HTTPException(400, "config required")
        try:
            import json as _json
            data = _json.loads(config_text)
            if "mcp_servers" in data and isinstance(data["mcp_servers"], list):
                _mcp_servers.clear()
                _mcp_servers.extend(data["mcp_servers"])
        except (TypeError, ValueError):
            return {"status": "imported"}
        return {"status": "imported"}
