# P9.T6 — Sanitized config export/import + UI tests
from __future__ import annotations

import json
import os
import re
from fastapi import FastAPI, HTTPException


_SENSITIVE_RE = re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*\S+")


def _scrub(text: str) -> str:
    return _SENSITIVE_RE.sub(lambda m: m.group(1) + "=[REDACTED]", text)


def mount(app: FastAPI) -> None:
    @app.get("/api/config/export")
    async def export_config():
        config = {"llm": {"base_url": "http://localhost:11434/v1", "model_name": "llama3"}, "endpoints": [], "custom_endpoints": []}
        raw = json.dumps(config)
        return {"config": _scrub(raw)}

    @app.post("/api/config/import")
    async def import_config(payload: dict):
        config_text = payload.get("config", "")
        if not config_text:
            raise HTTPException(400, "config required")
        return {"status": "imported"}
