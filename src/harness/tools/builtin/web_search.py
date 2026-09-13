# P3.T5 — web_search tool (Serper-shaped) + fixture tests
from __future__ import annotations

from typing import ClassVar

from harness.config.models import CustomEndpointDef, EndpointDef
from harness.registry.executor import HttpExecutor
from harness.registry.tool import Tool, ToolResult


class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web for a query"
    parameters: ClassVar[dict] = {
        "query": {"type": "string", "description": "Search query"},
        "num_results": {"type": "integer", "description": "Max results", "default": 5},
        "country_code": {"type": "string", "description": "Country code", "default": "us"},
    }

    def __init__(self, endpoint: EndpointDef | None = None) -> None:
        self.endpoint = endpoint or EndpointDef(url="https://serper.dev/search")
        self.executor = HttpExecutor()

    def run(self, **params) -> ToolResult:
        url = self.endpoint.url
        headers = {}
        if self.endpoint.api_key_env and self.endpoint.api_key_env != "none":
            import os
            val = os.environ.get(self.endpoint.api_key_env)
            if val:
                headers["X-API-KEY"] = val
        r = self.executor.execute("POST", url, body=params, headers=headers)
        if not r.ok:
            return r
        results = r.data.get("organic", []) if isinstance(r.data, dict) else []
        return ToolResult(ok=True, data={"results": results[: params.get("num_results", 5)], "query_used": params.get("query", ""), "result_count": len(results)})


def build_web_search(ep: CustomEndpointDef) -> WebSearchTool:
    return WebSearchTool(ep.endpoint if ep.endpoint else None)
