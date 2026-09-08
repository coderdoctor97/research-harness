# Phase 06 — Memory & Context Manager

> **Squad:** Squad-Citations (parallel band, second half) · **Depends on:** P5 · **Tasks:** 6
> **Source of truth:** `plan.md` §6 (3-level architecture, budgets, eviction), §7-Phase 6

## Goal

Conversation memory that never overflows the context window: token budgeting, rolling
summarization, TTL document cache, and the three-pass eviction strategy.

## Preconditions

- Phase 5 `DONE` (SourceRegistry exists — P6.T6 persists it). Same squad, sequential after P5.
  Touches ONLY `src/harness/memory/`.

## Tasks

| ID | Task | Mode | Owner | Output |
|---|---|---|---|---|
| P6.T1 | Token counter: tiktoken when available, deterministic fallback estimator (chars/4 heuristic) documented; single `count(text) -> int` API used everywhere | `[S]` | IMPLEMENTER-A | `memory/tokens.py` |
| P6.T2 | Budget calculator per §6: `available = context_window − max_tokens − thinking_budget − system − schemas`; returns the history+docs allowance each turn | `[P]` | IMPLEMENTER-A | `memory/budget.py` |
| P6.T3 | Rolling summarizer: LLM call with the §6 summarization prompt, replace N oldest turns with `[Summary of turns X–Y]`, target 3–5× compression; `hierarchical` + `none` strategies per config | `[P]` | IMPLEMENTER-B | `memory/summarizer.py` |
| P6.T4 | Document cache: in-memory dict keyed by URL + filesystem store keyed by URL hash under `document_cache_dir`; TTL from config; re-serve cached fetches instantly; `content_truncated` respected | `[P]` | IMPLEMENTER-B | `memory/doccache.py` |
| P6.T5 | Context assembler with 3-pass eviction (§6): (1) truncate docs to ~500-token excerpts keeping citation metadata, (2) rolling summarization, (3) aggressive eviction → system + latest summary + last 3 turns; emits budget warnings to logs only | `[P]` | IMPLEMENTER-C | `memory/assembler.py` |
| P6.T6 | Persistence + stress test: SourceRegistry to disk (Level 3), session save/summary/resume (§6 Multi-Session); 20-turn scripted conversation test staying in budget with facts + source refs retained (§10 Tests 5, 10) | `[S]` | TESTER | `memory/sessions.py` + tests |

## Execution Waves

1. **Wave 1 (sequential):** P6.T1 (everyone counts tokens through it).
2. **Wave 2 (parallel):** P6.T2 + P6.T3 + P6.T4 + P6.T5.
3. **Wave 3 (sequential):** P6.T6 + TEST/REVIEW gates.

## Acceptance Criteria (from plan.md §7-P6)

- [ ] A 20-turn conversation stays within context-window limits (budget test)
- [ ] Summarized turns preserve key facts and source references (assertion-checked)
- [ ] Cached URLs are served instantly on re-fetch (no HTTP call — verified by mock counter)
- [ ] Cache entries expire after TTL (fake-clock test)
- [ ] The model can accurately reference sources introduced in earlier turns

## Handoff to the Sync Gate

- `memory.assembler.build_context(session, query)` is the loop's Step 1 — integrator wires it.
- Session store API is what Phase 9's UI and Phase 10's dedup rely on.
