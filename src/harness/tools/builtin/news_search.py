# P8.T2 — news_search: NewsAPI-shaped, recency parameter
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import ClassVar

from harness.registry.executor import HttpExecutor
from harness.registry.tool import Tool, ToolResult


class NewsSearchTool(Tool):
    name = "news_search"
    description = "Search for recent news articles"
    parameters: ClassVar[dict] = {"query": {"type": "string", "description": "Search query"}, "num_results": {"type": "integer", "description": "Max results", "default": 5}, "recency": {"type": "string", "description": "today/this_week/this_month/any", "default": "this_week"}}

    def __init__(self, base_url: str = "https://newsapi.org/v2/everything") -> None:
        self.base_url = base_url
        self._executor = HttpExecutor()

    def run(self, **params) -> ToolResult:
        query = params.get("query", "")
        num = int(params.get("num_results", 5))
        recency = params.get("recency", "this_week")
        date_from = _recency_to_date(recency)
        url = f"{self.base_url}?q={query}&pageSize={num}&from={date_from}&sortBy=publishedAt"
        r = self._executor.execute("GET", url)
        if not r.ok:
            return r
        try:
            data = r.data if isinstance(r.data, dict) else {}
            articles = data.get("articles", [])
            results = []
            for a in articles[:num]:
                results.append({"title": a.get("title", ""), "url": a.get("url", ""), "source": a.get("source", {}).get("name", ""), "published_at": a.get("publishedAt", ""), "description": a.get("description", "")})
            return ToolResult(ok=True, data={"results": results, "query_used": query, "result_count": len(results)})
        except (AttributeError, TypeError) as exc:
            return ToolResult(ok=False, error=f"Parse error: {exc}")


def _recency_to_date(recency: str) -> str:
    now = datetime.now(UTC).replace(tzinfo=None)
    if recency == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif recency == "this_week":
        start = now - timedelta(days=7)
    elif recency == "this_month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now - timedelta(days=365)
    return start.strftime("%Y-%m-%dT%H:%M:%SZ")
