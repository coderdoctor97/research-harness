# P5.T7 — Citation pipeline: validate→urls→links→sources→scrub
from __future__ import annotations

from harness.citations.links import format_links
from harness.citations.registry import SourceRegistry
from harness.citations.scrubber import scrub
from harness.citations.sources import ensure_sources_section
from harness.citations.urls import validate_urls
from harness.citations.validate import validate as validate_cites


def finalize(
    text: str,
    registry: SourceRegistry,
    config: dict | None = None,
) -> tuple[str, dict]:
    """Run the full post-processing pipeline. Returns (clean_text, report)."""
    config = config or {}
    link_format = config.get("link_format", "markdown")
    max_sources = int(config.get("max_sources_per_response", 10))
    key_set = set(config.get("key_set", []))

    text, warnings = validate_cites(text, registry)
    text, stripped = validate_urls(text, registry)
    text = format_links(text, registry, link_format)
    text = ensure_sources_section(text, registry, max_sources)
    text, redacted = scrub(text, key_set)

    report = {
        "warnings": warnings,
        "stripped_urls": stripped,
        "redacted_keys": redacted,
    }
    return text, report
