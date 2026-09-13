# P9.T2 — Endpoint manager routes (optional manual endpoints)
from __future__ import annotations

import re

import httpx
from fastapi import FastAPI, HTTPException

_endpoints: list[dict] = []


def _find(name: str) -> dict | None:
    for ep in _endpoints:
        if ep["name"] == name:
            return ep
    return None


def mount(app: FastAPI) -> None:
    @app.get("/api/endpoints")
    async def list_endpoints():
        return list(_endpoints)

    @app.post("/api/endpoints")
    async def add_endpoint(payload: dict):
        name = (payload.get("name") or "").strip()
        url = (payload.get("url") or "").strip()
        if not name or not url:
            raise HTTPException(400, "name and url required")
        entry = {
            "name": name,
            "url": url,
            "method": payload.get("method") or "GET",
            "api_key_env": payload.get("api_key_env") or "none",
        }
        existing = _find(name)
        if existing:
            existing.update(entry)
        else:
            _endpoints.append(entry)
        return {"status": "added", "endpoint": entry}

    @app.post("/api/endpoints/{name}/test")
    async def test_endpoint(name: str, payload: dict):
        ep = _find(name)
        if ep is None:
            raise HTTPException(404, f"endpoint not found: {name}")
        import os
        url = re.sub(r"\{\{\s*\w+\s*\}\}", "test", ep["url"])
        headers = {}
        if ep.get("api_key_env") and ep["api_key_env"] != "none":
            value = os.environ.get(ep["api_key_env"], "")
            if value:
                headers["X-API-KEY"] = value
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                if ep["method"].upper() == "POST":
                    r = await client.post(url, json=payload or {"query": "test"}, headers=headers)
                else:
                    r = await client.get(url, headers=headers)
            result = "ok" if r.status_code < 500 else f"http {r.status_code}"
            return {"name": name, "result": result, "status_code": r.status_code}
        except httpx.HTTPError as exc:
            return {"name": name, "result": f"error: {type(exc).__name__}", "status_code": None}

    @app.delete("/api/endpoints/{name}")
    async def remove_endpoint(name: str):
        _endpoints[:] = [ep for ep in _endpoints if ep["name"] != name]
        return list(_endpoints)
