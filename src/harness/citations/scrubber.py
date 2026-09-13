# P5.T6 — Key scrubber: exact-match resolved keys + §9 regex patterns, in-memory only
from __future__ import annotations

import logging
import re

log = logging.getLogger(__name__)

# §9 patterns
_BEARER_RE = re.compile(r"(?i)Bearer\s+\S+")
_SK_RE = re.compile(r"(?i)sk-[A-Za-z0-9]{16,}")
_KEY_RE = re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+")


def scrub(text: str, key_set: set[str]) -> tuple[str, list[str]]:
    """Replace exact keys + §9 patterns with [REDACTED]. Never persists key_set."""
    redactions: list[str] = []
    clean = text
    for key in key_set:
        if key and key in clean:
            clean = clean.replace(key, "[REDACTED]")
            redactions.append(key)
    clean = _BEARER_RE.sub("[REDACTED]", clean)
    clean = _SK_RE.sub("[REDACTED]", clean)
    clean = _KEY_RE.sub(lambda m: m.group(1) + "=[REDACTED]", clean)
    if redactions:
        log.info(f"Scrubbed {len(redactions)} keys from response")
    return clean, redactions
