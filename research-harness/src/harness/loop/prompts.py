# P4.T5 — System prompt builder
from __future__ import annotations

from harness.registry.index import ToolRegistry


FALLBACK_INSTRUCTION = (
    "If the user's question can be answered from your training knowledge "
    "without external tools, answer directly without calling any tools."
)


def build_system_prompt(
    registry: ToolRegistry,
    citation_rules: str = "",
    fallback_to_training: bool = True,
) -> str:
    parts = ["You are a research assistant."]
    schemas = registry.list_schemas()
    if schemas:
        parts.append("Available tools:")
        for s in schemas:
            fn = s.get("function", {})
            parts.append(f"- {fn['name']}: {fn.get('description','')}")
    if citation_rules:
        parts.append("\nCitation rules:")
        parts.append(citation_rules)
    if fallback_to_training:
        parts.append("\n" + FALLBACK_INSTRUCTION)
    return "\n".join(parts)
