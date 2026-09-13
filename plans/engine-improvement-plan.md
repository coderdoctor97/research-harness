# Engine Improvement Plan

**Domain:** core execution mechanics · system architecture · application harnessing
**Vision baseline:** `plan.md` §1 (six-component architecture, data flow) · §4 (orchestration loop, Steps 1–7) · §7-P4/P10 · §8 (edge cases) — the harness is an **autonomous research engine**, and its engine room must be *one* mechanism, not three.
**Depends on:** nothing (E1 starts immediately). **Blocks:** A2/A3 (research workflow runs on the consolidated core), U3.3 (streaming render consumes E3's SSE).
**Efficiency doctrine:** every phase opens on the ponytail ladder; E1 *is* a ponytail audit; every REVIEW gate runs `ponytail-review`; sync points run `ponytail-debt`. Reports follow i-have-adhd format.

## Baseline findings this plan closes

| # | Finding (2026-09-13 review) | Phase |
|---|---|---|
| F1 | `ui/routes_chat.py` re-implements tool-call extraction, dispatch, context fitting (~470 lines) in parallel to `harness/loop/*`; `cli/repl.py` uses neither | E2 |
| F2 | `LLMClient.stream_chat` exists and passes tests but is wired to no surface (CLI and UI both non-streaming) | E3 |
| F3 | `loop/agent.py` is a 37-line state machine; parser/dispatcher/recovery/prompts are fragments — plan.md §4's full flow is not assembled on one shared core | E2, E4 |
| — | Single-file UI template (1663 lines) and possible over-build elsewhere — quantify, then cut | E1, E5 |

---

## Phase E1 — Baseline Audit & Debt Map *(read-only; ~2–3 h)*

> Entry: none. Exit: audit report + green test baseline + frozen core-API list recorded in PROGRESS.md. No code changes in this phase.

### Sub-phase E1.1 — Repo-wide over-engineering audit (~1 h)

| ID | Sub-task | Mode | Acceptance (verifiable) | Vision trace |
|---|---|---|---|---|
| E1.1.1 | Run `ponytail-audit` over `src/harness/` (report only, ranked biggest-cut-first) | `[S]` | Report appended to PROGRESS.md; every finding tagged `delete:/stdlib:/native:/yagni:/shrink:` with path | plan.md §1 — architecture stays lean enough to hold the six-component model |
| E1.1.2 | Run full test suite; record pass count as the green baseline | `[S]` | `pytest` green; baseline number written to PROGRESS.md ("233 tests, N passed") | §10 — validation discipline |
| E1.1.3 | Run `ruff` check; record violations count (fix nothing yet) | `[P]` | Count in PROGRESS.md | §7-P10 hardening |

### Sub-phase E1.2 — Engine debt & rule review (~45 min)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| E1.2.1 | Scan for existing `ponytail:` markers (`grep -rnE '(#\|//) ?ponytail:'`); establish empty ledger if none | `[S]` | Ledger row count recorded in PROGRESS.md | Efficiency doctrine — deferrals visible from day one |
| E1.2.2 | Extract engine-relevant rules from `bugfix.json` (BF-004 LLMClient attrs, BF-008 async-in-routes, BF-009 dev deps) into the phase working note | `[S]` | Rule list quoted in E2/E3 dispatch briefs | §9 — hard-won invariants never regress |
| E1.2.3 | Map the three divergent loop implementations: line ranges in `routes_chat.py`, `cli/repl.py`, `loop/*` that duplicate parsing/dispatch/context logic | `[S]` | Duplication table (file → lines → duplicate of what) in PROGRESS.md | §1 — one orchestration loop, per the architecture diagram |

### Sub-phase E1.3 — Freeze the core API surface (~30 min)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| E1.3.1 | List public functions/classes of `loop/`, `registry/`, `citations/`, `memory/`, `llm/` that consolidation must preserve | `[S]` | API freeze list in PROGRESS.md; changes after freeze route through REVIEW gate | §4 — stable loop contract for CLI+UI parity (§7-P9) |

---

## Phase E2 — Single Orchestration Core *(the keystone; ~1–2 days)*

> Entry: E1 done. Exit: CLI and UI chat both run on ONE shared loop core; net LOC **negative**; all tests green.
> Ponytail rule for this phase: **deletion over addition** — the win is measured in lines removed from `routes_chat.py` and `repl.py`.

### Sub-phase E2.1 — Assemble the shared core in `harness/loop/` (~0.5 day)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| E2.1.1 | Build one async session entry point (e.g. `run_chat(...)`) that implements plan.md §4 Steps 1–7 end-to-end: prompt build → LLM call → parse (native + ReAct fallback) → dispatch → inject results → iterate/force-final | `[S]` | New unit test drives a scripted mock LLM through all 7 steps | §4 Steps 1–7 verbatim |
| E2.1.2 | Fold `routes_chat.py`'s working extras (model discovery/retry, `_fit_context`, tool-call JSON extraction) into the core **only where the core lacks them** — reuse before writing (ladder rung 2) | `[S]` | No behavior in the core that duplicates an existing helper; each fold listed in commit message | §4 + §8 recovery tables |
| E2.1.3 | Keep recovery mechanics per §8: malformed output → correction prompt at 3 strikes → tools-off at 5; iteration cap → force-final | `[S]` | Recovery tests from `test_loop_e2e.py` still green against the new entry point | §8 Edge Cases rows 2–5 |

### Sub-phase E2.2 — Rewire the surfaces, delete the duplicates (~0.5 day)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| E2.2.1 | Rewrite `routes_chat.py::_handle_chat` to call the shared core; **delete** the private mini-loop (`_extract_tool_calls`, `_run_tool*`, `_fit_context`, prompt builders now owned by core) | `[S]` | `test_ui.py` + `test_chat_sessions.py` green; net diff negative; BF-008 respected (async-in-routes rule) | §7-P9 — "chat wired to the same orchestrator as the CLI" (parity requirement) |
| E2.2.2 | Rewire `cli/repl.py` to the shared core; keep streaming-free output for now (E3 adds it) | `[S]` | `test_smoke.py` green; manual REPL sanity logged | §7-P1/P9 CLI–UI parity |
| E2.2.3 | Preserve persisted state contracts: `.harness-state.json` provider resolution, session save/resume untouched | `[S]` | BF-010 check passes: restart server → `curl /api/models` returns 200 | bugfix.json BF-010; §6 sessions |

### Sub-phase E2.3 — Gate: consolidation sign-off (~1 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| E2.3.1 | TEST gate: full `pytest` green; record delta vs E1 baseline | `[S]` | All tests pass; count ≥ baseline | §10 |
| E2.3.2 | REVIEW gate: `ponytail-review` the whole E2 diff | `[S]` | Zero unresolved findings; net-LOC delta recorded (expect large negative) | Efficiency doctrine |
| E2.3.3 | SYNC point: run `ponytail-debt`; update PROGRESS.md in i-have-adhd format ("Phase E2 of 5 done — core consolidated, −N lines. Next: E3 streaming") | `[S]` | Ledger + PROGRESS entry committed | Efficiency doctrine |

---

## Phase E3 — Streaming End-to-End *(~0.5–1 day)*

> Entry: E2 done. Exit: token-level streaming from `LLMClient.stream_chat` through the core to CLI stdout and UI (SSE endpoint). UI *rendering* of the stream is U3.3's job — engine owns the wire only.

### Sub-phase E3.1 — Core streaming (~2–3 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| E3.1.1 | Add a streaming path to the shared core: yield events (`token`, `tool_call`, `tool_result`, `final`) wrapping existing `stream_chat` | `[S]` | Unit test: scripted mock yields tokens in order, tool events interleaved | §7-P10 T3 — "streaming responses end-to-end" |
| E3.1.2 | Non-streaming path stays the default; streaming is opt-in per surface (ladder rung 1 — no speculative config) | `[S]` | Existing tests unchanged and green | §4 — loop contract stability |

### Sub-phase E3.2 — Surface wiring (~2–3 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| E3.2.1 | CLI: stream tokens to stdout as they arrive | `[S]` | Manual run shows incremental output; smoke test updated | §7-P10 T3 |
| E3.2.2 | UI: add `GET/POST` SSE route (`text/event-stream`) emitting the core's events; no frontend changes here | `[S]` | `curl -N` against a mocked chat shows SSE frames; BF-008 respected | §7-P10 T3 + §9 localhost-only |
| E3.2.3 | Extend `test_streaming.py` from client-level to surface-level (CLI fn + SSE route via TestClient) | `[S]` | New tests green | §10 |

### Sub-phase E3.3 — Gate (~30 min)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| E3.3.1 | TEST + REVIEW gates (`pytest`, `ponytail-review` diff) | `[S]` | Green; findings resolved | Efficiency doctrine |
| E3.3.2 | PROGRESS update, adhd format; announce to U3.3 that SSE contract is frozen | `[S]` | Event schema (`token/tool_call/tool_result/final`) documented in `docs/architecture.md` | Cross-plan contract |

---

## Phase E4 — Robustness & Performance of the Consolidated Core *(~0.5–1 day)*

> Entry: E2 done (parallel-safe with E3). Exit: §4 multi-tool strategy and §8 edge-case tables demonstrably hold on the shared core.

### Sub-phase E4.1 — Parallel dispatch & recovery audit (~3 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| E4.1.1 | Verify parallel dispatch on the core: `asyncio.gather`, `max_parallel` cap, per-call timeout, partial-failure injection | `[S]` | E2E test: two parallel tool calls, one times out → other's result still injected | §4 Multi-Tool Call Strategy |
| E4.1.2 | Walk every row of §8 tables (endpoint failure, malformed, unavailable, refuses tools, circular calls, overflow); confirm a test exists on the **core** path | `[S]` | Row→test mapping table in PROGRESS.md; gaps closed | §8 verbatim |

### Sub-phase E4.2 — Memory & budget integration (~2 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| E4.2.1 | Confirm the core routes context through `memory/` (budget calculator, 3-pass eviction, doc cache, dedup) instead of ad-hoc fitting | `[S]` | `test_memory.py` + `test_dedup.py` green against core path; ad-hoc fitters deleted if duplicated (ponytail) | §6 Memory & Context |
| E4.2.2 | 20-turn stress on the core: budget respected, summarizer triggers, session resumes | `[S]` | Stress test from P6 re-run green | §6; §10 T-scenarios |

### Sub-phase E4.3 — Performance pass (~2 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| E4.3.1 | Connection pooling audit on `httpx` clients (one client per endpoint config, reused) | `[P]` | `test_perf_smoke.py` green; pooling noted in architecture doc | §7-P10 T2 |
| E4.3.2 | Async I/O audit: no blocking calls inside the event loop (BF-008 pattern check across `ui/` and `loop/`) | `[P]` | grep report clean or violations fixed | bugfix.json BF-008; §7-P10 T2 |

---

## Phase E5 — Structural Hygiene & Sign-off *(~0.5 day)*

> Entry: E1 audit report + E2–E4 done. Exit: audit findings resolved or consciously deferred with `ponytail:` tags; docs match reality; full regression green.

### Sub-phase E5.1 — Apply the E1 audit cuts (~2–3 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| E5.1.1 | Work the ranked E1.1.1 findings biggest-cut-first: `delete:` dead code, `stdlib:` hand-rolled stdlib, `shrink:` verbose logic | `[S]` | Each finding resolved OR tagged `ponytail: <ceiling>, <upgrade path>` with reason; net-LOC recorded | §1 lean architecture |
| E5.1.2 | Re-run `ponytail-audit`; expect "Lean already. Ship." or a materially shorter list | `[S]` | Second report in PROGRESS.md shows improvement | Efficiency doctrine |

### Sub-phase E5.2 — Docs & ledger alignment (~1–2 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| E5.2.1 | Update `docs/architecture.md`: one-loop diagram (CLI+UI → shared core → registry/memory/citations), SSE event schema | `[S]` | Doc matches code paths an outsider can trace | §1 architecture honesty |
| E5.2.2 | Final `ponytail-debt` harvest; every marker has ceiling + upgrade trigger (no `no-trigger` rows) | `[S]` | Ledger committed | Efficiency doctrine |

### Sub-phase E5.3 — Final gate (~1 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| E5.3.1 | Full regression: `pytest` + `ruff` + the 15 scenarios of plan.md §10 (engine-relevant rows re-verified) | `[S]` | All green; results appended to Final Acceptance Log | §10 |
| E5.3.2 | Sign-off entry in PROGRESS.md, adhd format, with program-level net-LOC delta for the Engine plan | `[S]` | "Engine plan done: X phases, −N lines, M tests added. Next: <plan/phase>" | Efficiency doctrine |
