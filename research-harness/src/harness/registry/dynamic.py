# P7.T1 + P7.T2 — Dynamic tool generator + parameter-schema inference
from __future__ import annotations

import re
from typing import Any

from harness.config.models import CustomEndpointDef
from harness.registry.executor import HttpExecutor
from harness.registry.tool import Tool, ToolResult
from harness.config.templates import render as render_template
from harness.config.resolver import resolve


_TMPL_RE = re.compile(r"\{\{([^}]+)\}\}")


def build_dynamic_tool(ep: CustomEndpointDef) -> Tool | None:
    """Build a Tool from a CustomEndpointDef config entry."""
    name = ep.name or ""
    if not name:
        return None
    url = resolve(render_template(ep.endpoint.url)) if ep.endpoint.url else ""
    if not url or "MISSING" in url:
        return None
    params = _infer_schema(ep)
    instance = _DynamicTool(
        name=name,
        description=ep.description or f"Dynamic tool: {name}",
        parameters=params,
        endpoint=ep.endpoint,
        url_template=ep.endpoint.url,
    )
    return instance


def _infer_schema(ep: CustomEndpointDef) -> dict:
    """Scan templates for {{placeholders}} → JSON-schema properties."""
    properties: dict[str, Any] = {}
    required: list[str] = []
    seen: set[str] = set()
    for template_str in _collect_templates(ep):
        for m in _TMPL_RE.finditer(template_str):
            expr = m.group(1).strip()
            name, type_hint, default_val, is_required = _parse_placeholder(expr)
            if name in seen:
                continue
            seen.add(name)
            prop: dict[str, Any] = {"type": type_hint}
            if default_val is not None:
                prop["default"] = default_val
            if is_required:
                required.append(name)
            properties[name] = prop
    return {"type": "object", "properties": properties, "required": required}


def _collect_templates(ep: CustomEndpointDef) -> list[str]:
    templates: list[str] = []
    if ep.endpoint and ep.endpoint.url:
        templates.append(ep.endpoint.url)
    if ep.parameters:
        body = ep.parameters.get("body_template", "")
        if body:
            templates.append(str(body))
        qp = ep.parameters.get("query_params_template", "")
        if qp:
            templates.append(str(qp))
    return templates


def _parse_placeholder(expr: str) -> tuple[str, str, Any, bool]:
    """Parse {{name|type:int|default:5}} → (name, type, default, is_required).

    Only default:null makes a param optional; numeric/string defaults are hints (still required).
    """
    parts = [p.strip() for p in expr.split("|")]
    name = parts[0]
    type_hint = "string"
    default_val: Any = None
    is_required = True
    for part in parts[1:]:
        if part.startswith("default:"):
            raw = part[len("default:"):]
            if raw.lower() == "null":
                default_val = None
                is_required = False
            else:
                try:
                    default_val = int(raw)
                    type_hint = "integer"
                except ValueError:
                    try:
                        default_val = float(raw)
                        type_hint = "number"
                    except ValueError:
                        default_val = raw
                        type_hint = "string"
        elif part.startswith("type:"):
            type_hint = part[len("type:"):] or "string"
    return name, type_hint, default_val, is_required


class _DynamicTool(Tool):
    def __init__(self, name: str, description: str, parameters: dict,
                 endpoint: Any, url_template: str) -> None:
        super().__init__()
        self.name = name
        self.description = description
        self.parameters = parameters
        self._endpoint = endpoint
        self._url_template = url_template
        self._executor = HttpExecutor()

    def run(self, **params) -> ToolResult:
        url = resolve(render_template(self._url_template))
        for k, v in params.items():
            url = url.replace("{{" + k + "}}", str(v))
        headers = {}
        if self._endpoint.api_key_env and self._endpoint.api_key_env != "none":
            import os
            val = os.environ.get(self._endpoint.api_key_env)
            if val:
                headers["Authorization"] = f"Bearer {val}"
        body = {}
        if self._endpoint.method and self._endpoint.method.upper() == "POST":
            body = params
        return self._executor.execute(self._endpoint.method or "GET", url, body=body or None, headers=headers or None)
