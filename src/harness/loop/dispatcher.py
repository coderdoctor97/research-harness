# P4.T3 — Parallel dispatch engine
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from harness.registry.index import ToolRegistry
from harness.registry.tool import ToolResult


def dispatch(
    registry: ToolRegistry,
    calls: list[dict],
    max_parallel: int = 4,
    per_call_timeout: float = 30.0,
) -> list[ToolResult]:
    """Dispatch tool calls; parallel when independent, sequential when <=1."""
    if len(calls) <= 1:
        return [_call_one(registry, c, per_call_timeout) for c in calls]
    results: list[ToolResult] = []
    with ThreadPoolExecutor(max_workers=max_parallel) as pool:
        futures = {pool.submit(_call_one, registry, c, per_call_timeout): c for c in calls}
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


def _call_one(registry: ToolRegistry, call: dict, timeout: float) -> ToolResult:
    name = call.get("name", "")
    params = call.get("arguments", {})
    try:
        return registry.dispatch(name, **params)
    except Exception as exc:
        return ToolResult(ok=False, error=str(exc))
