# P5.T5 — Sources-section generator: auto-append when missing, dedupe, cap
from __future__ import annotations

import re

from harness.citations.registry import SourceRegistry

_CITE_RE = re.compile(r"\[(\d+)\]")
_SOURCES_HDR = re.compile(r"^## Sources\s*$", re.MULTILINE | re.IGNORECASE)


def ensure_sources_section(text: str, registry: SourceRegistry, max_sources: int = 10) -> str:
    """Append Sources section if missing; use only actually-cited sources, deduped."""
    cited_ids = sorted({int(n) for n in _CITE_RE.findall(text)})
    cited = [registry.get(sid) for sid in cited_ids if registry.get(sid)]
    if not cited:
        return text
    if _SOURCES_HDR.search(text):
        return text
    lines = [text.strip(), "", "## Sources"]
    for src in cited[:max_sources]:
        lines.append(f"[{src.id}] {src.title} — {src.url}")
    return "\n".join(lines)
