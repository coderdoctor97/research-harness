"""Minimal configuration loader for Phase 1.

Phase 2 will replace this with the full Pydantic-based config schema that handles
YAML loading, `${ENV_VAR}` resolution, and template engines.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class HarnessConfig:
    """Minimal harness configuration."""

    base_url: str
    model_name: str
    api_key: str | None
    timeout: float = 120.0

    @property
    def has_auth(self) -> bool:
        return bool(self.api_key) and self.api_key.lower() != "none"


def load_config(
    *,
    env: dict[str, str] | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
    api_key: str | None = None,
) -> HarnessConfig:
    """Load config from CLI flags (highest priority) and environment variables.

    Resolution order: explicit arg → env var → default.
    """
    env_map = env if env is not None else dict(os.environ)

    resolved_base_url = base_url or env_map.get("HARNESS_LLM_BASE_URL") or "http://localhost:11434"
    resolved_model = model_name or env_map.get("HARNESS_LLM_MODEL") or "mistral-7b-instruct"

    api_key_env_name = env_map.get("HARNESS_LLM_API_KEY_ENV", "LOCAL_LLM_API_KEY")
    api_key_name_lower = api_key_env_name.lower()
    if api_key is not None:
        resolved_api_key: str | None = api_key
    elif api_key_name_lower == "none":
        resolved_api_key = None
    else:
        resolved_api_key = env_map.get(api_key_env_name)

    return HarnessConfig(
        base_url=resolved_base_url,
        model_name=resolved_model,
        api_key=resolved_api_key,
    )


__all__ = ["HarnessConfig", "load_config"]
