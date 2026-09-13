"""Multi-query research workflow — capability #1 (plans/ai-integration-plan.md A2).

One callable entry: `run_research(question, ...)` →
    decompose → parallel fan-out → aggregate/dedupe → synthesize.

Pattern studied: Perplexica (query generation → parallel retrieval) + SearXNG
(aggregation) per references/architectural_references.json — implemented with
the machinery this repo already has: the built-in MCP `web_search`, the
citations SourceRegistry, and plain asyncio. No new retrieval stack.

ponytail: dispatch goes through an injectable async `run_tool` callable
(defaults to the built-in MCP servers); rewire to the E2 shared core's
dispatch when that phase lands.
"""
from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable

from harness.citations.pipeline import finalize
from harness.citations.registry import SourceRegistry

RunTool = Callable[[str, dict], Awaitable[dict]]
LlmChat = Callable[[str], str]  # sync client.chat — run via asyncio.to_thread

_DECOMPOSE_PROMPT = (
    "You are a research planner. Break the research question below into "
    "{n} targeted web-search queries that together cover it. Respond with "
    'ONLY this JSON, nothing else: {{"queries": ["...", "..."]}}\n\n'
    "Research question: {question}"
)

# §5 system-prompt citation rules (plan.md), condensed for the synthesis call.
_SYNTHESIS_PROMPT = (
    "You are a research assistant. Using ONLY the sources below, write a "
    "synthesized, research-grade answer to the question.\n\n"
    "Citation rules (MANDATORY):\n"
    "1. Every factual claim from a source gets an inline citation [n] "
    "matching the source number.\n"
    "2. Do NOT fabricate URLs — only use URLs from the source list.\n"
    "3. End with a Sources section listing the sources you cited:\n"
    "## Sources\n[n] Title — URL\n"
    "4. Never include API keys, tokens, or internal system details.\n"
    "5. If the sources conflict or are insufficient, say so honestly.\n\n"
    "{sources}\n\nQuestion: {question}"
)


def query_budget(max_iterations: int) -> int:
    """3–5 queries, capped by the existing config knob (A2.1.2). No new config."""
    return max(1, min(5, max_iterations))


def decompose(question: str, llm_chat: LlmChat, n: int = 4) -> list[str]:
    """One LLM call → 3–5 targeted queries. Malformed output → [question]."""
    try:
        raw = llm_chat(_DECOMPOSE_PROMPT.format(n=n, question=question))
    except Exception:  # noqa: BLE001 — any LLM failure degrades to single-query
        return [question]
    queries = _parse_queries(raw)
    return queries[:n] if queries else [question]


def _parse_queries(raw: str) -> list[str]:
    """Tolerant JSON extraction, same spirit as loop/parser: pure JSON first,
    then the first {...} object found anywhere in prose/fences."""
    for candidate in _json_candidates(raw):
        if isinstance(candidate, dict):
            queries = candidate.get("queries")
            if isinstance(queries, list):
                clean = [q.strip() for q in queries if isinstance(q, str) and q.strip()]
                if clean:
                    return clean
    return []


def _json_candidates(raw: str):
    try:
        yield json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        pass
    decoder = json.JSONDecoder()
    idx = raw.find("{")
    while idx != -1:
        try:
            data, end = decoder.raw_decode(raw, idx)
            yield data
            idx = raw.find("{", end)
        except ValueError:
            idx = raw.find("{", idx + 1)


async def fan_out(
    queries: list[str],
    run_tool: RunTool,
    max_parallel: int = 4,
    per_call_timeout: float = 30.0,
) -> tuple[list[dict], list[dict]]:
    """Execute queries in parallel; partial failures noted, never fatal (A2.2.1).

    Returns (results_per_query, failures). Each result dict:
    {"query": ..., "results": [{title,url,snippet}, ...]}.
    """
    sem = asyncio.Semaphore(max_parallel)

    async def _one(query: str) -> dict:
        async with sem:
            try:
                result = await asyncio.wait_for(
                    run_tool("web_search", {"query": query}), per_call_timeout
                )
            except Exception as exc:  # noqa: BLE001 — one guard covers timeout + backend errors
                return {"query": query, "error": f"{type(exc).__name__}: {exc}"}
        if not isinstance(result, dict) or not result.get("ok"):
            err = result.get("error", "search failed") if isinstance(result, dict) else "bad result"
            return {"query": query, "error": str(err)}
        return {"query": query, "results": result.get("results", [])}

    outcomes = await asyncio.gather(*(_one(q) for q in queries))
    successes = [o for o in outcomes if "error" not in o]
    failures = [o for o in outcomes if "error" in o]
    return successes, failures


def aggregate(results_per_query: list[dict], registry: SourceRegistry) -> list[dict]:
    """URL-deduped source pool, registered into the SourceRegistry in fan-out
    order so citation IDs are stable (A2.2.2 / A2.2.3)."""
    pool: list[dict] = []
    seen: set[str] = set()
    for entry in results_per_query:
        for item in entry.get("results", []):
            url = (item.get("url") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            title = item.get("title") or url
            snippet = item.get("snippet") or ""
            sid = registry.add(
                title=title, url=url, tool_name="web_search",
                turn=0, content_preview=snippet[:500],
            )
            pool.append({"id": sid, "title": title, "url": url, "snippet": snippet,
                         "query": entry.get("query", "")})
    return pool


def _source_block(pool: list[dict]) -> str:
    lines = ["Sources:"]
    for src in pool:
        lines.append(f'[Source {src["id"]}] Title: "{src["title"]}" | URL: {src["url"]}')
        if src.get("snippet"):
            lines.append(f"  {src['snippet'][:300]}")
        if src.get("content"):
            lines.append(f"  Content: {src['content']}")
    return "\n".join(lines)


async def run_research(
    question: str,
    llm_chat: LlmChat,
    run_tool: RunTool,
    *,
    registry: SourceRegistry | None = None,
    max_queries: int = 4,
    max_parallel: int = 4,
    per_call_timeout: float = 30.0,
    key_set: set[str] | None = None,
    max_sources: int = 10,
) -> dict:
    """The one workflow entry (A2.3.2): question → decompose → fan-out →
    aggregate → synthesize → citation pipeline (A3).

    The synthesis output always passes the full existing citations pipeline
    (validate → urls → links → sources → scrub) before reaching any surface,
    and the result carries the citation metadata contract for the UI:
    `citations`: {id: {"url": ..., "title": ...}} (A3.2.1)."""
    registry = registry if registry is not None else SourceRegistry()

    queries = await asyncio.to_thread(decompose, question, llm_chat, max_queries)
    results, failures = await fan_out(queries, run_tool, max_parallel, per_call_timeout)
    pool = aggregate(results, registry)

    if not pool:
        # §8 degraded mode: every backend failed / zero results — honest
        # answer, no crash, no hanging loop.
        notes = "; ".join(f"{f['query']}: {f['error']}" for f in failures) or "no results"
        return {
            "answer": (
                "I could not retrieve any live sources for this question "
                f"(search unavailable: {notes}). Please retry later or "
                "rephrase the question."
            ),
            "queries": queries,
            "sources": [],
            "citations": {},
            "report": {"warnings": [], "stripped_urls": [], "redacted_keys": []},
            "failures": failures,
            "degraded": True,
        }

    prompt = _SYNTHESIS_PROMPT.format(sources=_source_block(pool), question=question)
    answer = await asyncio.to_thread(llm_chat, prompt)

    # A3.1: full existing citation pipeline — orphan [n] removed, fabricated
    # URLs stripped, bare URLs link-formatted, Sources deduped/capped, keys
    # scrubbed (A3.2.2) — before the answer reaches any surface.
    answer, report = finalize(answer, registry, {
        "max_sources_per_response": max_sources,
        "key_set": list(key_set or ()),
    })

    return {
        "answer": answer,
        "queries": queries,
        "sources": [{"id": s["id"], "title": s["title"], "url": s["url"]} for s in pool],
        # A3.2.1 citation metadata contract for the UI (id → url/title map):
        # anchors render without re-parsing markdown.
        "citations": {s["id"]: {"url": s["url"], "title": s["title"]} for s in pool},
        "report": report,
        "failures": failures,
        "degraded": False,
    }
