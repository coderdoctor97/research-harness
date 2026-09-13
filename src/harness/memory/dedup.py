# P10.T4 — Request deduplication: session-level (tool, params_hash) cache
from __future__ import annotations

import hashlib
import json

from harness.registry.tool import ToolResult


def params_hash(params: dict) -> str:
    """Deterministic hash of tool params for dedup matching."""
    try:
        raw = json.dumps(params, sort_keys=True, default=str)
    except TypeError:
        raw = str(sorted(params.items()))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class DedupCache:
    """Session-level cache: (tool_name, params_hash) → result."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], ToolResult] = {}

    def get(self, tool_name: str, params: dict) -> ToolResult | None:
        key = (tool_name, params_hash(params))
        return self._store.get(key)

    def put(self, tool_name: str, params: dict, result: ToolResult) -> None:
        key = (tool_name, params_hash(params))
        self._store[key] = result

    def clear(self) -> None:
        self._store.clear()
