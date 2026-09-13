# P5.T4 — Markdown link formatter: bare-URL wrapping, link_format support
from __future__ import annotations

import re

from harness.citations.registry import SourceRegistry

_URL_RE = re.compile(r"(?<!\]\()(https?://[^\s)>\]']+)")


def format_links(text: str, registry: SourceRegistry, link_format: str = "markdown") -> str:
    """Wrap bare URLs per link_format: markdown | html | plain."""
    def _replace(m: re.Match) -> str:
        url = m.group(1)
        src = registry.get_by_url(url)
        label = src.title if src else url
        if link_format == "html":
            return f'<a href="{url}">{label}</a>'
        if link_format == "plain":
            return label
        return f"[{label}]({url})"
    return _URL_RE.sub(_replace, text)
