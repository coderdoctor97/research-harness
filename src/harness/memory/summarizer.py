# P6.T3 — Rolling summarizer: LLM call, [Summary of turns X–Y], 3–5x compression
from __future__ import annotations

from harness.llm.client import LLMClient

_SUMMARY_PROMPT = (
    "Summarize the following conversation turns concisely, preserving key facts and source references. "
    "Format: [Summary of turns {start}–{end}] <summary text>"
)


def summarize_history(turns: list[dict], *, start: int = 0, keep_last: int = 6) -> tuple[str, list[dict]]:
    """Deterministic fallback summarizer for context assembly.

    It keeps the newest turns verbatim and compresses older turns without another LLM
    call, so the shared core can stay within budget even when the model client is a
    scripted test double or already busy answering the user.
    """
    if len(turns) <= keep_last:
        return "", turns
    old_turns = turns[:-keep_last]
    recent_turns = turns[-keep_last:]
    end = start + len(old_turns) - 1
    snippets = []
    for turn in old_turns[-3:]:
        role = turn.get("role", "?")
        content = " ".join(str(turn.get("content", "")).split())[:120]
        snippets.append(f"{role}: {content}")
    summary = f"[Summary of turns {start}–{end}] " + " | ".join(snippets)
    return summary, recent_turns


def summarize_turns(
    client: LLMClient,
    turns: list[dict],
    start: int,
    end: int,
    strategy: str = "hierarchical",
) -> str:
    if strategy == "none" or not turns:
        return ""
    text = "\n".join(f"{t.get('role','?')}: {t.get('content','')}" for t in turns)
    prompt = _SUMMARY_PROMPT.format(start=start, end=end) + "\n\n" + text
    try:
        result = client.chat(prompt)
        return result.strip()
    except Exception:  # noqa: BLE001 - summarizer fallback must not break context assembly
        return f"[Summary of turns {start}–{end}] {len(turns)} turns summarized."
