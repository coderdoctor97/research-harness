# P6.T2 — Budget calculator per §6
from __future__ import annotations


def compute(
    context_window: int = 8192,
    max_response_tokens: int = 512,
    thinking_budget: int = 0,
    system_tokens: int = 200,
    schema_tokens: int = 300,
) -> dict:
    available = context_window - max_response_tokens - thinking_budget - system_tokens - schema_tokens
    history_allowance = max(available // 2, 256)
    doc_allowance = max(available - history_allowance, 0)
    return {
        "context_window": context_window,
        "max_response_tokens": max_response_tokens,
        "available": available,
        "history_allowance": history_allowance,
        "doc_allowance": doc_allowance,
    }
