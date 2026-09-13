# P3.T2 — Registry auto-discovery + primary/fallback + list_schemas
from __future__ import annotations

from harness.config.models import EndpointDef
from harness.registry.tool import Tool, ToolResult


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, list[Tool]] = {}

    def register(self, tool: Tool) -> None:
        self._tools.setdefault(tool.name, []).append(tool)

    def from_endpoints(self, endpoints: list[EndpointDef]) -> None:
        for ep in endpoints:
            if not ep.url or "MISSING" in ep.url:
                continue
            tool = self._build_from_endpoint(ep)
            if tool:
                self.register(tool)

    def _build_from_endpoint(self, ep: EndpointDef) -> Tool | None:
        return None

    def get(self, name: str) -> list[Tool]:
        return self._tools.get(name, [])

    def primary(self, name: str) -> Tool | None:
        tools = self._tools.get(name)
        return tools[0] if tools else None

    def list_schemas(self) -> list[dict]:
        out: list[dict] = []
        seen: set[str] = set()
        for tools in self._tools.values():
            for t in tools:
                if t.name not in seen:
                    seen.add(t.name)
                    out.append(t.schema())
        return out

    def dispatch(self, name: str, **params) -> ToolResult:
        tools = self._tools.get(name)
        if not tools:
            return ToolResult(ok=False, error=f"Unknown tool: {name}")
        for tool in tools:
            try:
                return tool.run(**params)
            except Exception:  # noqa: BLE001, S112 - fallback tool chain tries next endpoint
                continue
        return ToolResult(ok=False, error=f"All endpoints failed for {name}")
