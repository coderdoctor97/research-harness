# P4.T3 — Parallel dispatch engine
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from harness.registry.index import ToolRegistry
from harness.registry.tool import ToolResult


def dispatch(
    registry: ToolRegistry,
    calls: list[dict],
    max_parallel: int = 4,
    per_call_timeout: float = 30.0,
) -> list[ToolResult]:
    """Sync compatibility wrapper; core paths use async_dispatch."""
    if len(calls) <= 1:
        return [_call_one(registry, c) for c in calls]
    results: list[ToolResult] = []
    with ThreadPoolExecutor(max_workers=max_parallel) as pool:
        futures = {pool.submit(_call_one, registry, c): c for c in calls}
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


async def async_dispatch(
    registry: ToolRegistry,
    calls: list[dict],
    max_parallel: int = 4,
    per_call_timeout: float = 30.0,
) -> list[ToolResult]:
    """Dispatch with asyncio.gather, max_parallel cap, timeout, and partial failure."""
    sem = asyncio.Semaphore(max(1, max_parallel))

    async def run(call: dict) -> ToolResult:
        async with sem:
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(_call_one, registry, call), timeout=per_call_timeout
                )
            except TimeoutError:
                return ToolResult(
                    ok=False,
                    error=f"Tool call timed out after {per_call_timeout:g} seconds.",
                )

    return list(await asyncio.gather(*(run(call) for call in calls)))


def _call_one(registry: ToolRegistry, call: dict) -> ToolResult:
    name = call.get("name", "")
    params = call.get("arguments", {})
    try:
        return registry.dispatch(name, **params)
    except Exception as exc:  # noqa: BLE001 - tool boundary returns failures to the model
        return ToolResult(ok=False, error=str(exc))
