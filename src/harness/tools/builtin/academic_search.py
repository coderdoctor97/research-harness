# P8.T1 — academic_search: arXiv API, XML parsing
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from harness.registry.executor import HttpExecutor
from harness.registry.tool import Tool, ToolResult


class AcademicSearchTool(Tool):
    name = "academic_search"
    description = "Search arXiv for academic papers"
    parameters = {"query": {"type": "string", "description": "Search query"}, "num_results": {"type": "integer", "description": "Max results", "default": 5}}

    def __init__(self) -> None:
        self._executor = HttpExecutor()

    def run(self, **params) -> ToolResult:
        query = params.get("query", "")
        num = int(params.get("num_results", 5))
        url = f"http://export.arxiv.org/api/query?search_query=all:{query}&max_results={num}"
        r = self._executor.execute("GET", url)
        if not r.ok:
            return r
        try:
            ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
            root = ET.fromstring(r.data if isinstance(r.data, str) else str(r.data))
            entries = root.findall("atom:entry", ns)
            results = []
            for entry in entries[:num]:
                title = entry.findtext("atom:title", default="", namespaces=ns).strip()
                link_el = entry.find("atom:id", ns)
                link = link_el.text if link_el is not None else ""
                authors = [a.findtext("atom:name", default="", namespaces=ns) for a in entry.findall("atom:author", ns)]
                abstract = entry.findtext("atom:summary", default="", namespaces=ns).strip()
                published = entry.findtext("atom:published", default="", namespaces=ns)
                results.append({"title": title, "url": link, "authors": authors[:3], "abstract": abstract[:500], "published": published})
            return ToolResult(ok=True, data={"results": results, "query_used": query, "result_count": len(results)})
        except Exception as exc:
            return ToolResult(ok=False, error=f"Parse error: {exc}")
