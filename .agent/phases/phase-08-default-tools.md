# Phase 08 — Additional Default Tools

> **Squad:** Squad-Tools (parallel band) · **Depends on:** P3, P4 · **Tasks:** 5
> **Source of truth:** `plan.md` §3.3–3.7, §7-Phase 8

## Goal

The full built-in suite: `academic_search`, `news_search`, `extract_links`, `summarize_page`,
`compute` — each with fixture tests.

## Preconditions

- Phase 3 `DONE` (executor) and Phase 4 `DONE` (`summarize_page` needs the side-channel LLM call).
  Runs in the parallel band — touches ONLY `src/harness/tools/builtin/` (new files, ownership map).

## Tasks

| ID | Task | Mode | Owner | Output |
|---|---|---|---|---|
| P8.T1 | `academic_search` per §3.5: arXiv API (`export.arxiv.org/api/query`), XML parsing via executor's XML mode, fields title/url/authors/abstract/published; params `query`, `num_results`; recorded-fixture tests | `[P]` | IMPLEMENTER-A | `tools/builtin/academic_search.py` + tests |
| P8.T2 | `news_search` per §3.6: NewsAPI-shaped endpoint, params `query`, `num_results`, `recency` (today/this_week/this_month/any → date-range filter applied client-side when the API lacks it); fixture tests | `[P]` | IMPLEMENTER-B | `tools/builtin/news_search.py` + tests |
| P8.T3 | `extract_links` per §3.3: wrapper over `fetch_url` with content discarded; parse links from markdown/HTML; optional `filter_pattern` regex; classify internal vs external; §10 Test 12 special-character URLs | `[P]` | IMPLEMENTER-C | `tools/builtin/extract_links.py` + tests |
| P8.T4 | `summarize_page` per §3.4: compound tool — internal `fetch_url` (cache-aware) → separate LLM call with a summarization prompt (kept OUT of the main loop context); params `url`, `focus`, `max_length` (brief/medium/detailed); returns `summary`, `key_points[]` | `[P]` | IMPLEMENTER-B | `tools/builtin/summarize_page.py` + tests |
| P8.T5 | `compute` per §3.7: AST-based sandboxed evaluator — arithmetic, `^` power, date arithmetic; `import os`, attribute access, names outside an allowlist ⇒ safe rejection (§10 Test 8's security twin) | `[P]` | IMPLEMENTER-A | `tools/builtin/compute.py` + tests |

## Execution Waves

1. **Wave 1 (fully parallel — the cleanest sync demo):** all five tasks, five sub-agents,
   disjoint files, coded against the frozen P3/P4 interfaces.
2. **Wave 2:** INTEGRATOR registers all five in the builtin registry index.
3. **Wave 3:** TEST/REVIEW gates.

## Acceptance Criteria (from plan.md §7-P8)

- [ ] `academic_search("transformer architecture")` returns arXiv papers (fixture + live-flagged)
- [ ] `news_search("climate change")` returns recent articles with dates
- [ ] `extract_links` on a saved Wikipedia page returns valid links; regex filter works
- [ ] `summarize_page` produces a coherent summary honoring `focus` + `max_length`, and the
  summarization call does NOT appear in the main conversation
- [ ] `compute("2^32")` returns the correct result; `compute("import os")` is safely rejected;
  malformed expressions return a tool error, never a crash

## Handoff to the Sync Gate

- All five tools self-register via the `@builtin_tool` decorator — integrator only imports the
  package. Fixture files live under `tests/fixtures/tools/` to avoid merge conflicts.
