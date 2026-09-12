# P9.T2 — Endpoint manager routes
from __future__ import annotations

from fastapi import FastAPI, HTTPException


def mount(app: FastAPI) -> None:
    @app.get("/api/endpoints")
    async def list_endpoints():
        return []

    @app.post("/api/endpoints")
    async def add_endpoint(payload: dict):
        return {"status": "added"}

    @app.post("/api/endpoints/{name}/test")
    async def test_endpoint(name: str, payload: dict):
        return {"name": name, "result": "ok"}
