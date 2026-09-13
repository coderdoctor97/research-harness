# P8.T4 — summarize_page: fetch → side-channel LLM summarization
from __future__ import annotations

from typing import ClassVar

from harness.llm.client import LLMClient
from harness.registry.tool import Tool, ToolResult
from harness.tools.builtin.fetch_url import FetchUrlTool

_SUMMARY_PROMPT = (
    "Summarize the following content{focus}. Keep it {length}.\n\n{content}"
)


class SummarizePageTool(Tool):
    name = "summarize_page"
    description = "Fetch a URL and produce a focused summary via LLM"
    parameters: ClassVar[dict] = {"url": {"type": "string", "description": "URL to summarize", "required": True}, "focus": {"type": "string", "description": "Focus topic", "default": ""}, "max_length": {"type": "string", "description": "brief/medium/detailed", "default": "medium"}}

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._client = llm_client
        self._fetcher = FetchUrlTool()

    def run(self, **params) -> ToolResult:
        url = params.get("url", "")
        focus = params.get("focus", "")
        max_length = params.get("max_length", "medium")
        length_map = {"brief": "under 100 words", "medium": "under 300 words", "detailed": "under 600 words"}
        length_desc = length_map.get(max_length, "under 300 words")
        fetch_result = self._fetcher.run(url=url)
        if not fetch_result.ok:
            return fetch_result
        content = fetch_result.data.get("content", "") if isinstance(fetch_result.data, dict) else str(fetch_result.data)
        content = content[:4000]
        focus_text = f" focusing on {focus}" if focus else ""
        prompt = _SUMMARY_PROMPT.format(focus=focus_text, length=length_desc, content=content)
        if self._client:
            try:
                summary = self._client.chat(prompt)
                return ToolResult(ok=True, data={"summary": summary, "url": url, "focus": focus, "max_length": max_length, "key_points": _extract_points(summary)})
            except Exception as exc:  # noqa: BLE001 - side-channel LLM failure becomes ToolResult
                return ToolResult(ok=False, error=f"Summarization failed: {exc}")
        return ToolResult(ok=False, error="No LLM client configured for summarization")


def _extract_points(text: str) -> list[str]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return [l for l in lines if l.startswith(("- ", "* "))][:5] or [lines[0]] if lines else []
