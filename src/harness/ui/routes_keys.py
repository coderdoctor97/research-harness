# P9.T3 — Key management routes: masked keys, never echo values
from __future__ import annotations

import re
from fastapi import FastAPI, HTTPException


def _mask(value: str) -> str:
    if not value or len(value) <= 4:
        return "****"
    return value[-4:].rjust(len(value), "*")


def mount(app: FastAPI) -> None:
    @app.get("/api/keys")
    async def list_keys():
        return [{"name": "API_KEY", "masked": "****", "set": False}]

    @app.post("/api/keys/{name}")
    async def set_key(name: str, payload: dict):
        value = payload.get("value", "")
        if not value:
            raise HTTPException(400, "value required")
        return {"name": name, "masked": _mask(value), "set": True}
