# Phase 05 — Response Formatting & Citation Engine

> **Squad:** Squad-Citations (parallel band, first half) · **Depends on:** P4 · **Tasks:** 7
> **Source of truth:** `plan.md` §5 (rules + post-processing), §7-Phase 5, §9 (key scrubbing)

## Goal

Post-processing pipeline that guarantees every final answer has valid `[n]` citations, hyperlinks
that only point at tool-returned URLs, a Sources section, and zero leaked credentials.

## Preconditions

- Phase 4 `DONE`; `on_final_answer` hook available. Runs in the parallel band — touches ONLY
  `src/harness/citations/` (ownership map, agent.md §5).

## Tasks

| ID | Task | Mode | Owner | Output |
|---|---|---|---|---|
| P5.T1 | `SourceRegistry`: assign sequential IDs to every retrieved item, persist across turns, expose the `[Source n] Title \| URL` reference table injected into the prompt (§5) | `[S]` | IMPLEMENTER-A | `citations/registry.py` |
| P5.T2 | Citation validator: every `[n]` maps to a real source; orphaned citations removed with a logged warning (§5 rule 1) | `[P]` | IMPLEMENTER-A | `citations/validate.py` |
| P5.T3 | URL validator: URLs in the response must exist in the source registry; fabricated ones stripped; per `citation_style` config | `[P]` | IMPLEMENTER-B | `citations/urls.py` |
| P5.T4 | Markdown link formatter: bare URLs wrapped (`https://x.com` → `[x.com](https://x.com)`), respects `link_format: markdown \| html \| plain` | `[P]` | IMPLEMENTER-B | `citations/links.py` |
| P5.T5 | Sources-section generator: auto-append from actually-cited sources when missing; dedupe; cap at `max_sources_per_response` | `[P]` | IMPLEMENTER-C | `citations/sources.py` |
| P5.T6 | Key scrubber: exact-match replace of every resolved key value → `[REDACTED]` + §9 patterns (`Bearer …`, `sk-…`, `key-…`); in-memory key set only, never persisted | `[P]` | IMPLEMENTER-C | `citations/scrubber.py` |
| P5.T7 | Pipeline assembly in the order validate→urls→links→sources→scrub; refine the §5 system-prompt text from P4.T5 with the exact `[Source n]` table format; full pipeline tests incl. §10 Test 9 (key scrubbing) | `[S]` | TESTER | `citations/pipeline.py` + tests |

## Execution Waves

1. **Wave 1 (sequential):** P5.T1 — registry is the dependency of all validators.
2. **Wave 2 (parallel):** P5.T2 + P5.T3 + P5.T4 + P5.T5 + P5.T6 (five sub-agents in sync).
3. **Wave 3 (sequential):** P5.T7 + TEST/REVIEW gates.

## Acceptance Criteria (from plan.md §7-P5)

- [ ] Responses consistently contain `[n]` inline citations validated against real sources
- [ ] Source list at the bottom matches inline citations (auto-generated when missing)
- [ ] Fabricated URLs are stripped; bare URLs get wrapped as markdown links
- [ ] No API key appears in any response (exact-match + pattern scrubbing, §10 Test 9)
- [ ] Orphaned `[n]` citations are removed with a warning in logs, never shown to the user

## Handoff to Phase 6

- `SourceRegistry` (P5.T1) is the object P6.T6 persists for cross-session source references.
- Pipeline entry `citations.pipeline.finalize(text, registry, config)` is called by the loop's
  `on_final_answer` hook — keep the signature stable for Phase 10's streaming work.
