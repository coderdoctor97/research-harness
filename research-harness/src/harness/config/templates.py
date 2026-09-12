# P2.T3 — {{placeholder|default:x}} template engine
from __future__ import annotations

import re

_TMPL_RE = re.compile(r"\{\{([^}]+)\}\}")


def render(template: str) -> str:
    """Replace {{expr|default:x}} placeholders with resolved text."""

    def _replace(m: re.Match) -> str:
        expr = m.group(1).strip()
        if "|default:" in expr:
            val, _, default = expr.partition("|default:")
            return default.strip()
        return m.group(0)

    return _TMPL_RE.sub(_replace, template)
