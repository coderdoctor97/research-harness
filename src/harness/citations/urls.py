# P5.T3 — URL validator: only tool-seen URLs; fabricated URLs stripped
from __future__ import annotations

import re

from harness.citations.registry import SourceRegistry

_URL_RE = re.compile(r"https?://[^\s)>\]']+")


def validate_urls(text: str, registry: SourceRegistry) -> tuple[str, list[str]]:
    """Strip URLs not present in the source registry. Returns (clean_text, stripped)."""
    stripped: list[str] = []
    def _replace(m: re.Match) -> str:
        url = m.group(0)
        if registry.get_by_url(url) is None:
            stripped.append(url)
            return ""
        return url
    clean = _URL_RE.sub(_replace, text)
    return clean, stripped
