# P4.T1 — Tool-call parser: OpenAI native + ReAct text fallback
from __future__ import annotations

import json
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


_TOOL_BLOCK_RE = re.compile(r"<\s*/?\s*(?:antml:)?tool_call\s*>", re.IGNORECASE)
_TOOL_BLOCK_PAIR_RE = re.compile(
    r"<\s*(?:antml:)?tool_call\s*>.*?<\s*/\s*(?:antml:)?tool_call\s*>",
    re.IGNORECASE | re.DOTALL,
)


def classify(text: str) -> tuple[CallType, str | ToolCall | None]:
    """Return (type, payload). Payload is final-answer text or first ToolCall."""
    calls = extract_tool_calls(text)
    if calls:
        call = calls[0]
        return CallType.TOOL_CALL, ToolCall(call["name"], call.get("arguments") or {})
    text = _TOOL_BLOCK_RE.sub("", text or "").strip()
    if "Action:" in text and "Action Input:" in text:
        return CallType.MALFORMED, None
    if text:
        return CallType.FINAL_ANSWER, text
    return CallType.MALFORMED, None


def extract_tool_calls(text: str) -> list[dict]:
    """Extract tool calls from JSON, XML wrappers, fenced blocks, or prose."""
    found: list[dict] = []

    def accept(data: object) -> bool:
        if not isinstance(data, dict):
            return False
        calls = data.get("tool_calls") or data.get("function_call")
        if calls:
            if isinstance(calls, dict):
                calls = [calls]
            for call in calls:
                if not isinstance(call, dict):
                    continue
                fc = call.get("function", call)
                name = fc.get("name", "")
                if name:
                    found.append({"name": name, "arguments": _arguments(fc.get("arguments", {}))})
            return bool(found)
        if data.get("name") and "arguments" in data:
            found.append({"name": data["name"], "arguments": _arguments(data.get("arguments") or {})})
            return True
        return False

    scan = _TOOL_BLOCK_RE.sub("", text or "").strip()
    try:
        if accept(json.loads(scan)):
            return found
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    if "Action:" in scan and "Action Input:" in scan:
        m_name = re.search(r"Action:\s*(\w+)", scan)
        m_args = re.search(r"Action Input:\s*(\{.*?\})", scan, re.DOTALL)
        if m_name:
            found.append({"name": m_name.group(1), "arguments": _arguments(m_args.group(1) if m_args else {})})
            return found

    decoder = json.JSONDecoder()
    idx = scan.find("{")
    while idx != -1 and len(found) < 8:
        try:
            data, end = decoder.raw_decode(scan, idx)
        except ValueError:
            idx = scan.find("{", idx + 1)
            continue
        idx = scan.find("{", end) if accept(data) else scan.find("{", idx + 1)
    return found


def clean_final_text(text: str) -> str:
    """Strip tool-call XML tags and raw tool-call JSON from visible answers."""
    if not text:
        return ""
    cleaned = _TOOL_BLOCK_PAIR_RE.sub("", text)
    cleaned = _TOOL_BLOCK_RE.sub("", cleaned)
    cleaned = _strip_tool_call_json(cleaned)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def _arguments(raw: object) -> dict:
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError, ValueError):
            return {"_raw": raw}
    return raw if isinstance(raw, dict) else {}


def _strip_tool_call_json(text: str) -> str:
    decoder = json.JSONDecoder()
    out = text
    idx = out.find("{")
    while idx != -1:
        try:
            data, end = decoder.raw_decode(out, idx)
        except ValueError:
            idx = out.find("{", idx + 1)
            continue
        if _is_tool_json(data):
            out = out[:idx] + out[end:]
            idx = out.find("{")
        else:
            idx = out.find("{", idx + 1)
    return out


def _is_tool_json(data: object) -> bool:
    if not isinstance(data, dict):
        return False
    calls = data.get("tool_calls") or data.get("function_call")
    return bool(calls) or bool(data.get("name") and "arguments" in data)
