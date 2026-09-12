# P6.T3 — Rolling summarizer: LLM call, [Summary of turns X–Y], 3–5x compression
from __future__ import annotations

from harness.llm.client import LLMClient

_SUMMARY_PROMPT = (
    "Summarize the following conversation turns concisely, preserving key facts and source references. "
    "Format: [Summary of turns {start}–{end}] <summary text>"
)


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
    except Exception:
        return f"[Summary of turns {start}–{end}] {len(turns)} turns summarized."
