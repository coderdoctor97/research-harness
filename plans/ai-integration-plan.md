# AI Integration Plan

**Domain:** AI workflows · integration pipelines · dedicated research capabilities
**Vision baseline:** `plan.md` §2 (providers/keys) · §3 (tool registry) · §5 (citations & hyperlinks) · §10 (validation) — and the product identity: an **autonomous academic/deep-research engine** whose four declared capabilities include multi-query search fan-out (#1), live-content ingestion (#2), and research-grade synthesis with verified inline citations (#3). Capabilities #1 and #3 are *declared but not yet realized in code* — completing them is vision alignment, not feature addition.
**Depends on:** E2 (the research workflow runs on the consolidated core; A1 is independent and can start immediately). **Blocks:** U2.3 (popover breakdown calls the research workflow), U3 (rendering its output).
**Architectural references (study the pattern, adopt natively — no new dependencies):** Perplexica (multi-query generation + citation linking) · SearXNG (metasearch aggregation) · Crawl4AI (HTML→clean markdown) · MCP reference servers — per `references/architectural_references.json`.
**Efficiency doctrine:** ponytail ladder on every task (reuse existing tools/registry/MCP built-ins first — rung 2); `ponytail-review` at gates; adhd-format reports with state restated.

## Baseline findings this plan closes

| # | Finding (2026-09-13 review) | Phase |
|---|---|---|
| F4 | No query decomposition / multi-query fan-out anywhere in `src/` (capability #1 gap) | A2 |
| F5 | Citation pipeline (`citations/`) is complete but only exercised as post-processing of single-turn chat — not integrated into a research-grade synthesis workflow (capability #3 gap) | A3 |
| — | Provider flow exists (presets, two key forms, model fetch, `.harness-state.json` persistence) but its restart-resilience invariants (BF-010, BF-005) need a verification pass after engine changes | A1 |
| — | Ingestion quality (fetch → clean markdown, link harvesting) exists via built-ins; needs a quality pass against the Crawl4AI pattern inside the workflow | A4 |

---

## Phase A1 — Provider & Key Pipeline Hardening *(independent; ~0.5 day)*

> Entry: none (parallel-safe with E1/E2). Exit: provider → key → model-discovery pipeline demonstrably survives restarts and never leaks keys.

### Sub-phase A1.1 — Provider resolution resilience (~2 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A1.1.1 | Verify BF-010 end-to-end: configure provider in UI → restart server → `curl /api/models` (no params) returns 200 | `[S]` | Check scripted into `test_ai_integration.py`; green | docs/connection-guide.md; bugfix.json BF-010 |
| A1.1.2 | Verify BF-005: chat reads the SAVED provider (not inline params); auto-save on Fetch-models still holds after E2 rewiring | `[S]` | Test asserts chat works with zero inline params post-restart | bugfix.json BF-005 |
| A1.1.3 | Model discovery fallbacks: unknown provider → profile fallback (never empty string, never hardcoded cloud model lists) | `[P]` | `test_model_discovery.py` green; fallback dict documented | §2 config-driven; BF "MODELS" rule |

### Sub-phase A1.2 — Key security audit (~2 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A1.2.1 | Trace every key path: `.env` → resolver → headers → logs → responses → model output; confirm masking (last-4) and scrubbing at each hop | `[S]` | Path table in PROGRESS.md; each hop has a test | §9 Security — full section |
| A1.2.2 | Confirm `citations/scrubber.py` runs on **all** model-facing outputs including new workflow outputs (A2/A3 hook-in point reserved) | `[S]` | Unit test: seeded key in mock response → scrubbed | §9 "Preventing Key Leakage" |
| A1.2.3 | Audit logging check: key *names* logged, never values | `[P]` | Log sample inspected; assertion in tests | §9 Audit Logging |

### Sub-phase A1.3 — Gate (~30 min)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A1.3.1 | TEST + REVIEW gates; `ponytail-review` diff (expect near-zero new code — this phase is verification) | `[S]` | Green; if the phase produced >100 new lines, justify or cut | Efficiency doctrine |

---

## Phase A2 — Multi-Query Research Workflow *(capability #1; ~1–2 days)*

> Entry: E2 done (workflow rides the shared core). Exit: one research question fans out into N targeted queries, executes in parallel via existing tools, and aggregates into one source pool.
> Reference pattern: **Perplexica** (query generation → parallel retrieval → re-rank) and **SearXNG** (aggregation) — studied per the references registry, implemented with the tools that already exist (`web_search`, `academic_search`, `news_search`, MCP built-ins). Ladder rung 2: no new retrieval stack.

### Sub-phase A2.1 — Query decomposition (~3 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A2.1.1 | Add a decompose step to the workflow: one LLM call turns the research question into 3–5 targeted queries (structured JSON output; parser reuses `loop/parser` conventions) | `[S]` | Mock-LLM test: question → valid query list; malformed output → single-query fallback (never crash) | agent.md §0 capability #1 — "fan out a single research question into several targeted queries" |
| A2.1.2 | Query budget from existing config (`max_iterations`/tool-budget knobs); no new config system — extend `config.yaml` schema only if a knob is genuinely missing | `[S]` | Config validation tests green; defaults sane offline | §2 design principles |

### Sub-phase A2.2 — Parallel fan-out & aggregation (~4 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A2.2.1 | Execute queries in parallel through the consolidated core's dispatch (`asyncio.gather`, `max_parallel`, per-call timeout, partial-failure injection) | `[S]` | E2E mock test: 3 queries, 1 fails → 2 results aggregated, failure noted | §4 Multi-Tool Call Strategy |
| A2.2.2 | Aggregate + dedupe results: URL-level dedupe via existing `memory/dedup` + `doccache` (re-fetch of same URL is instant) | `[S]` | Test: overlapping result sets → single source pool; second fetch served from cache | §6 Document Cache |
| A2.2.3 | Register every fetched URL/content into `citations/SourceRegistry` during aggregation (so A3 can validate against real, tool-seen sources) | `[S]` | Source IDs assigned in fan-out order; registry persistence test green | §5 + §6 Cross-Turn Source Registry |

### Sub-phase A2.3 — Synthesis stage (~3 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A2.3.1 | Final synthesis call: aggregated source pool → single research-grade answer using the §5 system-prompt citation rules (inline `[n]`, anchors, Sources section) | `[S]` | Mock-LLM test: output passes the citation validator with ≥1 real source | §5 Response Formatting verbatim; capability #3 |
| A2.3.2 | Workflow exposed as one callable entry (used by CLI command and later by UI/popover): `question → decompose → fan-out → synthesize` | `[S]` | One function, one test through all four stages | §1 data-flow summary, steps 1–9 |

### Sub-phase A2.4 — Gate (~1 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A2.4.1 | TEST + REVIEW gates; `ponytail-review` (watch for speculative re-ranking/ML — cut anything the mock tests don't demand) | `[S]` | Green; net-LOC recorded | Efficiency doctrine |
| A2.4.2 | SYNC: `ponytail-debt` + adhd PROGRESS entry ("Phase A2 of 5 done — fan-out works end-to-end on mocks. Next: A3 citations on live path") | `[S]` | Ledger + entry committed | Efficiency doctrine |

---

## Phase A3 — Citation & Anchor Pipeline Integration *(capability #3; ~0.5–1 day)*

> Entry: A2 done. Exit: the research workflow's output is citation-enforced by the *existing* `citations/` pipeline — validated `[n]` refs, tool-seen URLs only, clickable anchors, deduped Sources section, scrubbed keys.
> Principle: the pipeline (registry, validate, urls, links, sources, scrubber) already exists and passed 14 tests — this phase **wires**, not builds (ladder rung 2).

### Sub-phase A3.1 — Wire the pipeline into the workflow (~3 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A3.1.1 | Run the synthesis output through the full citation pipeline (`citations/pipeline.py`) before it reaches any surface | `[S]` | Integration test: raw mock answer with orphan `[7]` → orphan removed + warning logged | §5 Post-Processing Rules; Key Design Decision "post-processing citation validation" |
| A3.1.2 | URL validation against the SourceRegistry populated in A2.2.3: fabricated URLs stripped, real ones link-formatted with anchors | `[S]` | Test: answer containing an unseen URL → stripped; seen URL → clickable `[n](url)` | §5; capability #3 "verified inline citations and clickable anchor hyperlinks" |
| A3.1.3 | Auto Sources section: dedupe, respect `max_sources_per_response` | `[P]` | Existing `test_citations.py` extended to workflow output; green | §5 |

### Sub-phase A3.2 — Contract for UI consumption (~2 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A3.2.1 | Emit citation metadata alongside the answer (source id → url/title map) so U3.1 can render anchors without re-parsing markdown | `[S]` | JSON contract documented in `docs/ai-integration.md`; test asserts map completeness | §5 Example Output; enables capability #4 (U2) |
| A3.2.2 | Scrubber final pass on workflow output (keys never reach UI) | `[S]` | A1.2.2 test extended to workflow path | §9 |

### Sub-phase A3.3 — Gate (~30 min)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A3.3.1 | TEST + REVIEW gates; `ponytail-review` | `[S]` | Green; findings resolved | Efficiency doctrine |

---

## Phase A4 — Live Ingestion & Tool Surface in the Workflow *(capability #2; ~0.5 day)*

> Entry: A2 done (parallel-safe with A3). Exit: page ingestion inside the research workflow matches the Crawl4AI pattern's *outcomes* (clean markdown, noise stripped, links harvested) using the existing built-in fetcher — and every configured tool (MCP, custom endpoints) is uniformly reachable from fan-out.

### Sub-phase A4.1 — Ingestion quality pass (~3 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A4.1.1 | Audit `fetch_url`/builtin-fetcher output against the Crawl4AI pattern checklist (noise stripping: nav/footer/banner; markdown fidelity; raw link harvesting) — fix gaps in the existing extractor, don't add a crawler | `[S]` | Fixture test: noisy HTML → clean markdown + harvested links; DDG `/lite/` fallback intact (BF-003) | references registry `content_extraction`; capability #2 |
| A4.1.2 | Truncation + budget behavior on long pages verified inside fan-out (per-source token cap so one huge page can't blow the synthesis budget) | `[S]` | Test: oversized page → truncated with marker; budget math from `memory/budget` respected | §6 Token Budget |

### Sub-phase A4.2 — Uniform tool availability (~2 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A4.2.1 | Confirm fan-out can dispatch MCP built-ins (`web_search` DDG, `fetch_url`, `extract_links`) and user custom-endpoint tools through the same registry path | `[S]` | Test: custom mock endpoint registered → reachable as a query tool in the workflow | §3.8 custom endpoints; §1 "plug-and-play" |
| A4.2.2 | `summarize_page` usable as an aggregation-side compression step when the source pool exceeds budget (side-channel LLM call already implemented — wire, don't rebuild) | `[P]` | Test: over-budget pool → summaries replace raw content; citations still resolve | §6 eviction; §3 compound tools |

### Sub-phase A4.3 — Gate (~30 min)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A4.3.1 | TEST + REVIEW gates; `ponytail-review`; `ponytail-debt` sync | `[S]` | Green; ledger updated | Efficiency doctrine |

---

## Phase A5 — Research Validation & Tuning *(~0.5 day)*

> Entry: A2–A4 done. Exit: the harness demonstrably behaves as a research engine on the plan.md §10 regime plus dedicated research scenarios, across ≥2 model profiles.

### Sub-phase A5.1 — Acceptance scenarios (~3 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A5.1.1 | Write research acceptance scenario R1: full question → fan-out (mock backends) → synthesized answer with ≥3 distinct verified sources, zero fabricated URLs, zero leaked keys | `[S]` | Scenario added to Final Acceptance Log; green | §10; product identity |
| A5.1.2 | Scenario R2: degraded mode — all search endpoints fail → graceful §8-style error answer, no crash, no hanging loop | `[S]` | Green; wording follows §8 tables | §8 Endpoint Completely Unavailable |
| A5.1.3 | Re-run the 15 plan.md §10 scenarios against the new workflow paths (regression) | `[S]` | All PASS rows retained in the log | §10 |

### Sub-phase A5.2 — Prompt & profile tuning (~2 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A5.2.1 | Tune decompose + synthesis prompts across Mistral/Llama-3/Qwen/Phi profiles (existing profile mechanism from P10.T5) | `[S]` | Per-profile mock fixtures green; JSON-output instruction robust to weak parsers (ReAct fallback covered) | §7-P10 T5; §4 parser duality |

### Sub-phase A5.3 — Docs & sign-off (~1–2 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| A5.3.1 | Update `docs/ai-integration.md` (research workflow usage + citation metadata contract) and `docs/connection-guide.md` deltas | `[S]` | New-user walkthrough still <30 min; docs match code | §7-P10 T6; DoD |
| A5.3.2 | Final gate: `pytest` + `ruff` clean; `ponytail-debt` harvest; adhd sign-off with net-LOC and capability status ("#1 ✅ #2 ✅ #3 ✅ — #4 tracked in UI plan U2") | `[S]` | PROGRESS.md committed | Efficiency doctrine |
