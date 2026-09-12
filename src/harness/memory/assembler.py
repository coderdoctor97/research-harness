# P6.T5 — Context assembler: 3-pass eviction (§6)
from __future__ import annotations

from harness.memory.tokens import count
from harness.memory.budget import compute


def build_context(
    system_prompt: str,
    history: list[dict],
    documents: list[dict],
    budget: dict | None = None,
) -> tuple[str, dict]:
    """3-pass eviction: (1) truncate docs, (2) summarize, (3) aggressive eviction."""
    budget = budget or compute()
    system_tokens = count(system_prompt)
    schema_tokens = 300
    available = budget["available"] - system_tokens - schema_tokens
    # Pass 1: truncate documents to ~500-token excerpts
    docs_text = _truncate_docs(documents, max_tokens=min(500, available // 3))
    # Pass 2: rolling summarization (summary replaces oldest turns)
    summary = budget.get("summary", "")
    history_text = "\n".join(f"{t['role']}: {t['content']}" for t in history)
    # Pass 3: aggressive eviction if over budget
    total = count(system_prompt) + count(summary) + count(history_text) + count(docs_text)
    if total > budget["available"]:
        # Keep only last 3 turns
        if len(history) > 3:
            history = history[-3:]
        history_text = "\n".join(f"{t['role']}: {t['content']}" for t in history)
        total = count(system_prompt) + count(history_text) + count(docs_text)
        if total > budget["available"]:
            docs_text = ""
    parts = [system_prompt]
    if summary:
        parts.append(summary)
    parts.append(history_text)
    if docs_text:
        parts.append(docs_text)
    assembled = "\n".join(parts)
    actual_tokens = count(assembled)
    warnings = []
    if actual_tokens > budget["available"]:
        warnings.append(f"Context budget exceeded: {actual_tokens} > {budget['available']}")
    return assembled, {"tokens": actual_tokens, "warnings": warnings}


def _truncate_docs(documents: list[dict], max_tokens: int) -> str:
    parts = []
    total = 0
    for doc in documents:
        content = doc.get("content", "")
        c = count(content)
        if total + c > max_tokens:
            break
        parts.append(content)
        total += c
    return "\n".join(parts)
