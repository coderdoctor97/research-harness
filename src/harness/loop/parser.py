# P4.T1 — Tool-call parser: OpenAI native + ReAct text fallback
from __future__ import annotations

import re
from enum import Enum


class CallType(Enum):
    FINAL_ANSWER = "final_answer"
    TOOL_CALL = "tool_call"
    MALFORMED = "malformed"


class ToolCall:
    def __init__(self, name: str, arguments: dict) -> None:
        self.name = name
        self.arguments = arguments


def classify(text: str) -> tuple[CallType, str | ToolCall | None]:
    """Return (type, payload). Payload is final-answer text or ToolCall."""
    # 0) Strip <tool_call>…</tool_call> XML wrappers (Qwen/Anthropic-style
    #    models emit these; they are markup, not answer text).
    text = re.sub(
        r"<\s*/?\s*(?:antml:)?tool_call\s*>", "", text, flags=re.IGNORECASE
    ).strip()
    # 1) Try OpenAI native function_calls JSON
    try:
        import json
        data = json.loads(text)
        calls = data.get("tool_calls") or data.get("function_call")
        if calls:
            if isinstance(calls, dict):
                calls = [calls]
            fc = calls[0].get("function", calls[0])
            name = fc.get("name", "")
            args_raw = fc.get("arguments", "{}")
            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
            except Exception:
                args = {"_raw": args_raw}
            return CallType.TOOL_CALL, ToolCall(name=name, arguments=args)
    except Exception:
        pass
    # 2) ReAct text fallback
    if "Action:" in text and "Action Input:" in text:
        m_name = re.search(r"Action:\s*(\w+)", text)
        m_args = re.search(r"Action Input:\s*(\{.*?\})", text, re.DOTALL)
        if m_name:
            try:
                args = json.loads(m_args.group(1)) if m_args else {}
            except Exception:
                args = {}
            return CallType.TOOL_CALL, ToolCall(name=m_name.group(1), arguments=args)
        return CallType.MALFORMED, None
    # 3) Final answer
    if text.strip():
        return CallType.FINAL_ANSWER, text.strip()
    return CallType.MALFORMED, None
