# P6.T1 — Token counter: tiktoken when available, fallback to chars/4
from __future__ import annotations


def count(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)
