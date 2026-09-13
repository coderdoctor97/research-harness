# P9.T3 — Key management routes: masked keys, never echo values
from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from harness.ui._ai_state import load_section, persist_section

# Key store — persisted to .harness-state.json (bugfix.json BF-010) so keys
# survive restarts. Values are also pushed into os.environ so tools/clients
# can resolve them by env-var name; GET responses only ever expose masks.
_key_store: dict[str, str] = dict(load_section("keys") or {})
for _name, _value in _key_store.items():
    if isinstance(_value, str) and _value:
        os.environ.setdefault(_name, _value)

_TRACKED_DEFAULTS = ("API_KEY", "BRAVE_API_KEY", "HARNESS_LLM_API_KEY")


def _persist_keys() -> None:
    persist_section("keys", dict(_key_store))


def _mask(value: str) -> str:
    if not value or len(value) <= 4:
        return "****"
    return value[-4:].rjust(len(value), "*")


def mount(app: FastAPI) -> None:
    @app.get("/api/keys")
    async def list_keys():
        seen: set[str] = set()
        entries: list[dict] = []
        # Tracked defaults first (API_KEY stays first for backwards compat).
        for name in _TRACKED_DEFAULTS:
            value = _key_store.get(name) or os.environ.get(name, "")
            entries.append({"name": name, "masked": _mask(value), "set": bool(value)})
            seen.add(name)
        for name, value in _key_store.items():
            if name in seen:
                continue
            entries.append({"name": name, "masked": _mask(value), "set": bool(value)})
        return entries

    @app.post("/api/keys/{name}")
    async def set_key(name: str, payload: dict):
        value = payload.get("value", "")
        if not value:
            raise HTTPException(400, "value required")
        _key_store[name] = value
        os.environ[name] = value  # resolvable by env name immediately
        _persist_keys()
        return {"name": name, "masked": _mask(value), "set": True}

    @app.delete("/api/keys/{name}")
    async def delete_key(name: str):
        _key_store.pop(name, None)
        os.environ.pop(name, None)
        _persist_keys()
        return {"name": name, "set": False}
