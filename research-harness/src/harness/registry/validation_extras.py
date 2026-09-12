# P7.T3 — Config validation extras: tool_mapping, enabled toggle, friendly errors
from __future__ import annotations

from harness.config.models import CustomEndpointDef


class CustomEndpointError(Exception):
    pass


def validate_custom_endpoint(ep: CustomEndpointDef) -> None:
    """Raise friendly error on malformed custom endpoint entry."""
    if not ep.name:
        raise CustomEndpointError("custom_endpoint missing required field: name")
    if not ep.endpoint or not ep.endpoint.url:
        raise CustomEndpointError(f"custom_endpoint '{ep.name}': endpoint.url is required")
    if not ep.endpoint.url.startswith("http"):
        raise CustomEndpointError(f"custom_endpoint '{ep.name}': endpoint.url must be a valid URL")


def group_by_mapping(endpoints: list[CustomEndpointDef]) -> dict[str, list[CustomEndpointDef]]:
    """Group endpoints by tool_mapping; unmapped get their own name as key."""
    groups: dict[str, list[CustomEndpointDef]] = {}
    for ep in endpoints:
        if not ep.enabled:
            continue
        key = ep.tool_mapping or ep.name
        groups.setdefault(key, []).append(ep)
    return groups
