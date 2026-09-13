# P4.T5 — System prompt builder + per-model profiles (P10.T5)
from __future__ import annotations

from harness.registry.index import ToolRegistry

FALLBACK_INSTRUCTION = (
    "If the user's question can be answered from your training knowledge "
    "without external tools, answer directly without calling any tools."
)

_MODEL_PROFILES = {
    "llama3": {
        "name": "Llama 3",
        "system_prefix": "You are a helpful research assistant.",
        "tool_style": "Use tools naturally without over-explaining.",
        "citation_style": "Provide inline sources.",
    },
    "mistral": {
        "name": "Mistral",
        "system_prefix": "You are an accurate research assistant.",
        "tool_style": "Be concise; call tools efficiently.",
        "citation_style": "Include source URLs.",
    },
}
_DEFAULT_PROFILE = {
    "name": "Llama 3",
    "system_prefix": "You are a thorough research assistant.",
    "tool_style": "Show reasoning before calling tools.",
    "citation_style": "Cite with [n] format.",
}


def get_profile(model_name: str) -> dict:
    key = model_name.lower().split("-")[0].split("/")[-1]
    return _MODEL_PROFILES.get(key, _DEFAULT_PROFILE)


def build_system_prompt(
    registry: ToolRegistry,
    citation_rules: str = "",
    fallback_to_training: bool = True,
    model_name: str = "llama3",
) -> str:
    profile = get_profile(model_name)
    parts = [profile["system_prefix"]]
    schemas = registry.list_schemas()
    if schemas:
        parts.append("Available tools:")
        for s in schemas:
            fn = s.get("function", {})
            parts.append(f"- {fn['name']}: {fn.get('description','')}")
    parts.append(f"\n{profile['tool_style']}")
    if citation_rules:
        parts.append(f"\nCitation style: {profile['citation_style']}")
        parts.append(f"\n{citation_rules}")
    if fallback_to_training:
        parts.append("\n" + FALLBACK_INSTRUCTION)
    return "\n".join(parts)
