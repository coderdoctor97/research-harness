# P3.T1 — Tool base class + OpenAI function-calling schema + ToolResult
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error: str | None = None
    meta: dict = field(default_factory=dict)


class Tool:
    name: str = ""
    description: str = ""
    parameters: dict = field(default_factory=dict)

    def run(self, **params) -> ToolResult:
        raise NotImplementedError

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": [k for k, v in self.parameters.items() if v.get("required") or "default" not in v],
                },
            },
        }
