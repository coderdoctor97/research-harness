# P2.T4 — Config validation + friendly errors
from __future__ import annotations

from harness.config.models import HarnessConfig


class ConfigError(Exception):
    pass


def validate(raw: dict) -> HarnessConfig:
    try:
        return HarnessConfig(**raw)
    except Exception as exc:
        raise ConfigError(f"Invalid config: {exc}") from exc
