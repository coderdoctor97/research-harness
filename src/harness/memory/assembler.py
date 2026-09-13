# P6.T5 — Context assembler: 3-pass eviction (§6)
from __future__ import annotations

from harness.memory.budget import compute
from harness.memory.summarizer import summarize_history
from harness.memory.tokens import count


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
    available = max(0, budget["available"] - system_tokens - schema_tokens)

    # Pass 1: truncate documents to fit the document allowance.
    docs_text = _truncate_docs(documents, max_tokens=max(0, min(500, available // 3)))

    # Pass 2: summarize old history once the conversation is long or already over budget.
    summary = budget.get("summary", "")
    working_history = history
    history_text = _render_history(working_history)
    would_overflow = count(system_prompt) + count(summary) + count(history_text) + count(docs_text)
    summarized = False
    if not summary and (len(history) > 12 or would_overflow > budget["available"]):
        summary, working_history = summarize_history(history, keep_last=6)
        history_text = _render_history(working_history)
        summarized = bool(summary)

    # Pass 3: aggressive eviction if still over budget.
    total = count(system_prompt) + count(summary) + count(history_text) + count(docs_text)
    evicted_docs = False
    evicted_turns = 0
    if total > budget["available"]:
        if len(working_history) > 3:
            evicted_turns = len(working_history) - 3
            working_history = working_history[-3:]
        history_text = _render_history(working_history)
        total = count(system_prompt) + count(summary) + count(history_text) + count(docs_text)
        if total > budget["available"]:
            docs_text = ""
            evicted_docs = True

    parts = [system_prompt]
    if summary:
        parts.append(summary)
    if history_text:
        parts.append(history_text)
    if docs_text:
        parts.append(docs_text)
    assembled = "\n".join(parts)
    actual_tokens = count(assembled)
    warnings = []
    if actual_tokens > budget["available"]:
        warnings.append(f"Context budget exceeded: {actual_tokens} > {budget['available']}")
    return assembled, {
        "tokens": actual_tokens,
        "warnings": warnings,
        "summary": {"included": bool(summary), "generated": summarized},
        "eviction": {"turns": evicted_turns, "documents": evicted_docs},
    }


def _render_history(history: list[dict]) -> str:
    return "\n".join(f"{t['role']}: {t['content']}" for t in history)


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
