# P8.T3 — extract_links: fetch wrapper + link parser + regex filter
from __future__ import annotations

import re
from typing import Any

from harness.registry.tool import Tool, ToolResult
from harness.tools.builtin.fetch_url import FetchUrlTool


_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)|https?://[^\s)>\]\']+')


class ExtractLinksTool(Tool):
    name = "extract_links"
    description = "Extract links from a URL"
    parameters = {"url": {"type": "string", "description": "URL to extract links from", "required": True}, "filter_pattern": {"type": "string", "description": "Regex filter for links", "default": ""}}

    def __init__(self) -> None:
        self._fetcher = FetchUrlTool()

    def run(self, **params) -> ToolResult:
        url = params.get("url", "")
        filter_pat = params.get("filter_pattern", "")
        fetch_result = self._fetcher.run(url=url)
        if not fetch_result.ok:
            return fetch_result
        content = fetch_result.data.get("content", "") if isinstance(fetch_result.data, dict) else str(fetch_result.data)
        links: list[dict[str, str]] = []
        for m in _LINK_RE.finditer(content):
            if m.group(1) and m.group(2):
                text, href = m.group(1), m.group(2)
            else:
                href = m.group(0)
                text = href
            is_internal = href.startswith("/") or href.startswith("#")
            if filter_pat:
                try:
                    if not re.search(filter_pat, href):
                        continue
                except re.error:
                    return ToolResult(ok=False, error=f"Invalid filter_pattern: {filter_pat}")
            links.append({"text": text, "url": href, "internal": is_internal})
        return ToolResult(ok=True, data={"links": links, "url": url, "count": len(links)})
