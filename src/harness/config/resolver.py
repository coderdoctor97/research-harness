# P2.T2 — ${ENV_VAR} resolver + .env load
from __future__ import annotations

import os
import re
from pathlib import Path

_ENV_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def resolve(value: str) -> str:
    """Resolve ${VAR} tokens in value against os.environ; leave unknown as-is with warning."""

    def _replace(m: re.Match) -> str:
        var = m.group(1)
        val = os.environ.get(var)
        if val is None:
            return f"${{MISSING:{var}}}"
        return val

    return _ENV_RE.sub(_replace, value)


def load_dotenv(path: str | Path | None = None) -> None:
    """Load KEY=VALUE pairs from .env into os.environ (non-destructive)."""
    target = Path(path) if path else Path(".env")
    if not target.is_file():
        return
    for line in target.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if key and val and key not in os.environ:
            os.environ[key] = val
