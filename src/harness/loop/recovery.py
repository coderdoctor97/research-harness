# P4.T4 — Malformed-output recovery: correction prompt, tools-off at 5 strikes, duplicate-call guard
from __future__ import annotations

from harness.loop.parser import classify, CallType


CORRECTION_PROMPT = (
    "Your previous output could not be parsed as a valid tool call. "
    "Respond with a single tool call in the format:\n"
    '{"tool_calls": [{"function": {"name": "...", "arguments": {...}}}]}'
)

TOOLS_OFF_PROMPT = (
    "Tool calls have been disabled for this turn. "
    "Provide a direct answer based on your training knowledge."
)


def correction_prompt(strikes: int) -> str:
    if strikes >= 5:
        return TOOLS_OFF_PROMPT
    return CORRECTION_PROMPT


def duplicate_guard_key(name: str, params: dict) -> str:
    import hashlib, json
    raw = name + "|" + json.dumps(params, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()
