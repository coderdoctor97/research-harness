# P3.T6 — fetch_url tool (Jina-reader-shaped) + truncation + URL encoding
from __future__ import annotations

import os
from urllib.parse import quote
from typing import Any

from harness.config.models import EndpointDef, CustomEndpointDef
from harness.registry.executor import HttpExecutor
from harness.registry.tool import Tool, ToolResult


class FetchUrlTool(Tool):
    name = "fetch_url"
    description = "Fetch and return the content of a URL"
    parameters = {
        "url": {"type": "string", "description": "Target URL", "required": True},
        "extract_links": {"type": "boolean", "description": "Return only links", "default": False},
    }

    def __init__(self, endpoint: EndpointDef | None = None, max_content_tokens: int = 8000) -> None:
        self.endpoint = endpoint or EndpointDef(url="https://r.jina.ai/{{target_url}}")
        self.max_content_tokens = max_content_tokens
        self.executor = HttpExecutor()

    def run(self, **params) -> ToolResult:
        raw_url = params.get("url", "")
        encoded = quote(raw_url, safe=":/?#[]@!$&'()*+,;=")
        url = self.endpoint.url.replace("{{target_url}}", encoded)
        headers = {}
        if self.endpoint.api_key_env and self.endpoint.api_key_env != "none":
            val = os.environ.get(self.endpoint.api_key_env)
            if val:
                headers["Authorization"] = f"Bearer {val}"
        r = self.executor.execute("GET", url, headers=headers)
        if not r.ok:
            return r
        content = r.data.get("data", r.data) if isinstance(r.data, dict) else r.data
        content_str = str(content)
        truncated = len(content_str) > self.max_content_tokens * 4
        content_str = content_str[: self.max_content_tokens * 4]
        return ToolResult(ok=True, data={"content": content_str, "url": raw_url, "content_truncated": truncated})


def build_fetch_url(ep: CustomEndpointDef) -> FetchUrlTool:
    return FetchUrlTool(ep.endpoint if ep.endpoint else None)
