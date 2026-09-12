# P3.T3 — Generic HTTP executor: template fill → async request → JSON/XML parse → ToolResult
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import httpx

from harness.registry.tool import ToolResult


class HttpExecutor:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=30.0)

    def execute(self, method: str, url: str, body: dict | None = None, headers: dict | None = None) -> ToolResult:
        try:
            r = self.client.request(method, url, json=body, headers=headers)
            r.raise_for_status()
        except httpx.ConnectError as exc:
            return ToolResult(ok=False, error=f"Connection refused: {exc}")
        except httpx.TimeoutException as exc:
            return ToolResult(ok=False, error=f"Timeout: {exc}")
        except httpx.HTTPStatusError as exc:
            return ToolResult(ok=False, error=f"HTTP {exc.response.status_code}")
        try:
            data = r.json()
        except Exception:
            try:
                data = _parse_xml(r.text)
            except Exception:
                return ToolResult(ok=False, error="Empty or unparseable response body")
        return ToolResult(ok=True, data=data)


def _parse_xml(text: str) -> dict:
    root = ET.fromstring(text)
    return {root.tag: _elem_to_dict(root)}


def _elem_to_dict(el: ET.Element) -> dict | str:
    children = list(el)
    if not children:
        return el.text or ""
    out: dict[str, Any] = {}
    for child in children:
        out[child.tag] = _elem_to_dict(child)
    return out
