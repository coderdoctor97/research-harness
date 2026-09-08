# PROGRESS.md — Live Execution Tracker

> **Protocol:** The ORCHESTRATOR updates this file after every phase (and after every task in
> the parallel band). Never delete history — append. Statuses: `TODO → IN_PROGRESS → BLOCKED → DONE`.
> If you are an agent resuming work: start at the first phase not marked `DONE`.

---

## Phase Status

| # | Phase | Status | Tasks done | Tests | Notes |
|---|---|---|---|---|---|
| 1 | LLM Wrapper | TODO | 0/5 | — | |
| 2 | Config System | TODO | 0/6 | — | blocked by P1 |
| 3 | Tool Registry | TODO | 0/6 | — | blocked by P2 |
| 4 | Orchestration Loop | TODO | 0/6 | — | blocked by P3 |
| 5 | Citation Engine | TODO | 0/7 | — | blocked by P4 |
| 6 | Memory & Context | TODO | 0/6 | — | blocked by P5 |
| 7 | Custom Endpoints | TODO | 0/5 | — | blocked by P3 (parallel band) |
| 8 | Default Tool Suite | TODO | 0/5 | — | blocked by P3+P4 (parallel band) |
| 9 | Web UI (optional) | TODO | 0/6 | — | blocked by sync gate 2 — ask user if wanted |
| 10 | Hardening | TODO | 0/8 | — | blocked by all |

## Parallel Band Tracker (after Phase 4)

| Squad | Phase(s) | Owner files | Status |
|---|---|---|---|
| Squad-Citations | P5 → P6 | `citations/`, `memory/` | TODO |
| Squad-Extensibility | P7 | `registry/dynamic.py`, `registry/fallback.py` | TODO |
| Squad-Tools | P8 | `tools/builtin/` | TODO |

## Task Checklists

### Phase 1 — LLM Wrapper
- [ ] P1.T1 `[S]` Repo scaffold (pyproject, layout, pytest/ruff, .gitignore)
- [ ] P1.T2 `[P]` LLMClient (OpenAI-compatible, timeouts, typed errors)
- [ ] P1.T3 `[P]` CLI REPL
- [ ] P1.T4 `[P]` Minimal config loader
- [ ] P1.T5 `[S]` Smoke test + README run instructions

### Phase 2 — Config System
- [ ] P2.T1 `[S]` Pydantic schema models
- [ ] P2.T2 `[P]` `${ENV_VAR}` resolver + `.env`
- [ ] P2.T3 `[P]` `{{placeholder}}` template engine
- [ ] P2.T4 `[P]` Validation + friendly errors
- [ ] P2.T5 `[P]` Hot-reload watcher
- [ ] P2.T6 `[S]` Config tests + committed config.yaml/.env.example

### Phase 3 — Tool Registry
- [ ] P3.T1 `[S]` Tool base class + schema generation
- [ ] P3.T2 `[P]` Registry auto-discovery + fallback chains
- [ ] P3.T3 `[P]` Generic HTTP executor (JSON/XML)
- [ ] P3.T4 `[P]` Rate limiter + retry/backoff
- [ ] P3.T5 `[P]` web_search implementation + tests
- [ ] P3.T6 `[P]` fetch_url implementation + tests

### Phase 4 — Orchestration Loop
- [ ] P4.T1 `[S]` Tool-call parser (OpenAI + ReAct)
- [ ] P4.T2 `[P]` Loop state machine + iteration cap
- [ ] P4.T3 `[P]` Parallel dispatch engine
- [ ] P4.T4 `[P]` Malformed-output recovery
- [ ] P4.T5 `[P]` System prompt builder
- [ ] P4.T6 `[S]` E2E loop tests (mock LLM)

### Phase 5 — Citation Engine
- [ ] P5.T1 `[S]` SourceRegistry
- [ ] P5.T2 `[P]` Citation validator
- [ ] P5.T3 `[P]` URL validator
- [ ] P5.T4 `[P]` Markdown link formatter
- [ ] P5.T5 `[P]` Auto Sources section
- [ ] P5.T6 `[P]` Key scrubber
- [ ] P5.T7 `[S]` Pipeline assembly + prompt refinement + tests

### Phase 6 — Memory & Context
- [ ] P6.T1 `[S]` Token counter
- [ ] P6.T2 `[P]` Budget calculator
- [ ] P6.T3 `[P]` Rolling summarizer
- [ ] P6.T4 `[P]` Document cache (TTL)
- [ ] P6.T5 `[P]` Context assembler (3-pass eviction)
- [ ] P6.T6 `[S]` Registry persistence + sessions + 20-turn stress test

### Phase 7 — Custom Endpoints
- [ ] P7.T1 `[S]` Dynamic tool generator
- [ ] P7.T2 `[P]` Param-schema inference
- [ ] P7.T3 `[P]` tool_mapping/description + validation
- [ ] P7.T4 `[P]` Fallback chain execution
- [ ] P7.T5 `[S]` Mock-endpoint + hot-reload tests

### Phase 8 — Default Tool Suite
- [ ] P8.T1 `[P]` academic_search (arXiv XML)
- [ ] P8.T2 `[P]` news_search
- [ ] P8.T3 `[P]` extract_links
- [ ] P8.T4 `[P]` summarize_page (compound)
- [ ] P8.T5 `[P]` compute (sandboxed)

### Phase 9 — Web UI (optional)
- [ ] P9.T1 `[S]` FastAPI scaffold (localhost bind)
- [ ] P9.T2 `[P]` Endpoint manager
- [ ] P9.T3 `[P]` Key management (masked)
- [ ] P9.T4 `[P]` Chat UI
- [ ] P9.T5 `[P]` Log viewer
- [ ] P9.T6 `[S]` Export/import + UI tests

### Phase 10 — Hardening
- [ ] P10.T1 `[P]` Error audit vs §8 tables
- [ ] P10.T2 `[P]` Perf pass (pooling, async audit)
- [ ] P10.T3 `[P]` Streaming end-to-end
- [ ] P10.T4 `[P]` Request deduplication
- [ ] P10.T5 `[P]` Multi-model prompt tuning
- [ ] P10.T6 `[P]` User docs
- [ ] P10.T7 `[P]` Developer docs
- [ ] P10.T8 `[S]` Packaging + 15-scenario acceptance run

## Final Acceptance Log (plan.md §10 — fill in Phase 10)

| # | Scenario | Result | E2E time | Tool calls | Tokens | Notes |
|---|---|---|---|---|---|---|
| 1 | Simple factual (no tools) | | | | | |
| 2 | Current events query | | | | | |
| 3 | Deep dive w/ URL fetch | | | | | |
| 4 | Academic research query | | | | | |
| 5 | Multi-turn context retention | | | | | |
| 6 | Endpoint failure degradation | | | | | |
| 7 | Rate-limit handling | | | | | |
| 8 | Custom endpoint integration | | | | | |
| 9 | API key scrubbing | | | | | |
| 10 | Context window stress | | | | | |
| 11 | Malformed output recovery | | | | | |
| 12 | Special-character URL | | | | | |
| 13 | No-tool fallback | | | | | |
| 14 | Parallel tool execution | | | | | |
| 15 | Config hot reload | | | | | |

## Blocker Log

| Date | Phase/Task | Blocker | Resolution |
|---|---|---|---|
| | | | |
