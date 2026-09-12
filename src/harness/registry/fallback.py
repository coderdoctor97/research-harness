# P7.T4 — Fallback chain execution for custom endpoints
from __future__ import annotations

from harness.config.models import CustomEndpointDef
from harness.registry.tool import ToolResult


def execute_with_fallback(
    endpoints: list[CustomEndpointDef],
    params: dict,
    executor=None,
) -> ToolResult:
    """Try endpoints in order; return first success or last error."""
    last_error: ToolResult | None = None
    for ep in endpoints:
        from harness.registry.dynamic import build_dynamic_tool
        tool = build_dynamic_tool(ep)
        if tool is None:
            continue
        result = tool.run(**params)
        if result.ok:
            return result
        last_error = result
    if last_error:
        return last_error
    return ToolResult(ok=False, error="No enabled endpoints available")
