# P5.T2 — Citation validator: every [n] maps to a real source; orphans removed + warning
from __future__ import annotations

import logging
import re

from harness.citations.registry import SourceRegistry

log = logging.getLogger(__name__)
_CITE_RE = re.compile(r"\[(\d+)\]")


def validate(text: str, registry: SourceRegistry) -> tuple[str, list[str]]:
    """Remove orphaned [n] citations; keep valid ones. Returns (clean_text, warnings)."""
    warnings: list[str] = []

    def _replace(m: re.Match) -> str:
        n = int(m.group(1))
        if registry.get(n) is None:
            warnings.append(f"orphan citation [{n}]")
            return ""
        return m.group(0)

    clean = _CITE_RE.sub(_replace, text)
    for w in warnings:
        log.warning(w)
    return clean, warnings
