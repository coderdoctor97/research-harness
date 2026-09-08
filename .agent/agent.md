# AGENT.md — Master Execution Brief

**Project:** Local LLM Research Assistant Harness ("the harness")
**Source of truth:** [`../plan.md`](../plan.md) — the comprehensive implementation plan (10 sections).
**This file:** the operating manual for the agent(s) that build the project. It divides the plan
into 10 executable phases, assigns each phase a goal and a fixed set of tasks, and defines how
agents and sub-agents execute them in sync.

> **START HERE.** If you are an agent reading this file: follow §6 (Execution Protocol) exactly.
> Check `.agent/PROGRESS.md` first — resume from the first phase not marked `DONE`.

---

## 1. Mission

Build the complete research-assistant harness specified in `plan.md`: a local-LLM agent loop with
a config-driven tool registry, citation-enforced responses, token-budgeted memory, and
plug-and-play custom endpoints — passing all 15 validation scenarios of `plan.md` §10.

**Project-level Definition of Done (all must hold at the end):**

- [ ] All 10 phases marked `DONE` in `.agent/PROGRESS.md`
- [ ] All 15 test scenarios from `plan.md` §10 executed and passing (logged in PROGRESS.md)
- [ ] Installs with `pip install -e .` and runs against Ollama / llama.cpp / vLLM (≥3 backends)
- [ ] Zero secrets in code or config — all keys via `${ENV_VAR}` references (plan.md §9)
- [ ] User docs + developer docs complete; new user can set up in < 30 minutes

## 2. Folder Map

```
.agent/
├── agent.md            ← you are here (master brief: division of labor + protocol)
├── PROGRESS.md         ← live status tracker (update after every phase — never delete)
└── phases/
    ├── phase-01-llm-wrapper.md
    ├── phase-02-config-system.md
    ├── phase-03-tool-registry.md
    ├── phase-04-orchestration-loop.md
    ├── phase-05-citation-engine.md
    ├── phase-06-memory-context.md
    ├── phase-07-custom-endpoints.md
    ├── phase-08-default-tools.md
    ├── phase-09-web-ui.md
    └── phase-10-hardening.md

research-harness/       ← the codebase being built (created in Phase 1)
├── pyproject.toml
├── src/harness/        (llm/ config/ registry/ tools/ loop/ citations/ memory/ cli/ ui/)
├── tests/
└── docs/
```

## 3. Agent Team Model

One **Orchestrator** (the agent that reads this file) plus **sub-agents** spawned per task wave.

```
ORCHESTRATOR (you)
│   owns: phase sequencing, task dispatch, sync gates, PROGRESS.md, conflict resolution
│
├── Squad-Core          → Phases 1 → 2 → 3 → 4   (strict chain — the spine)
├── Squad-Citations     → Phase 5 → Phase 6      (sequential pair, runs in parallel band)
├── Squad-Extensibility → Phase 7                (parallel band)
├── Squad-Tools         → Phase 8                (parallel band)
├── Squad-UI            → Phase 9 (optional)     (after sync gate)
└── Squad-QA            → Phase 10 + final acceptance
```

**Sub-agent roles used inside every phase:**

| Role | Responsibility | Gate |
|---|---|---|
| ARCHITECT | Convert the phase brief into module/file-level decisions before any code. No code. | — |
| IMPLEMENTER-A/B/C | Write code for assigned tasks only. One owner per file (ownership map per phase). | — |
| TESTER | Write + run the phase acceptance tests (pytest). Must be green before review. | TEST GATE |
| REVIEWER | Audit the diff against plan.md requirements, §8 error tables, §9 security rules. | REVIEW GATE |
| INTEGRATOR | (Orchestrator) merges squad outputs at sync gates, resolves shared-file conflicts. | SYNC GATE |

> **Compatibility note:** if the runtime cannot spawn real parallel sub-agents, execute the waves
> in the listed order, role-playing each sub-agent, and **never skip the TEST / REVIEW gates.**
> The wave order preserves correctness; parallelism is a latency optimization, not a shortcut.

## 4. Phase Overview (the division of the plan)

| # | Phase | Goal (one line) | Tasks | Depends on | plan.md § |
|---|---|---|---|---|---|
| 1 | LLM Wrapper | CLI that talks to a local LLM server | **5** | — | §7-P1 |
| 2 | Config System | YAML config: env resolution, templates, validation, hot-reload | **6** | P1 | §2, §7-P2 |
| 3 | Tool Registry | Schema-generating registry + generic HTTP tool executor | **6** | P2 | §3, §7-P3 |
| 4 | Orchestration Loop | Full ReAct agent loop with parallel dispatch + recovery | **6** | P3 | §4, §7-P4 |
| 5 | Citation Engine | Source registry + post-processing citation/hyperlink enforcement | **7** | P4 | §5, §7-P5 |
| 6 | Memory & Context | Token budgets, rolling summarization, document cache | **6** | P5 | §6, §7-P6 |
| 7 | Custom Endpoints | Zero-code user endpoints → auto-generated tools | **5** | P3 | §3.8, §7-P7 |
| 8 | Default Tool Suite | academic/news/links/summarize/compute tools | **5** | P3, P4 | §3, §7-P8 |
| 9 | Web UI (optional) | Local panel: endpoints, keys, chat, logs | **6** | sync gate | §7-P9 |
| 10 | Hardening | Audit, perf, streaming, docs, packaging, final acceptance | **8** | all | §7-P10, §8–10 |

**Total: 60 tasks.** Every task has an ID (`Pn.Tm`) used in dispatches, commits, and PROGRESS.md.

## 5. Dependency Graph & Sync Gates

```
P1 ─► P2 ─► P3 ─► P4 ─┬─► P5 ─► P6 ─┐
                      ├─► P7 ───────┼──► SYNC GATE 2 ──► (P9 optional) ──► P10 ──► FINAL ACCEPTANCE
                      └─► P8 ───────┘
        ▲ strict chain: Squad-Core (spine)        ▲ parallel band: 3 squads in sync
```

- **SYNC GATE 1** (after P4): spine complete; orchestrator reviews the core APIs that the
  parallel band will build against (Tool interface, Loop events, config models). Freeze them.
- **Parallel band** (P5+P6, P7, P8): three squads run **in sync on disjoint files**.
  Ownership: Squad-Citations → `src/harness/citations/` + `src/harness/memory/`;
  Squad-Extensibility → `src/harness/registry/dynamic.py`, `registry/fallback.py`;
  Squad-Tools → `src/harness/tools/builtin/` (new files only).
  Shared files (`registry/index.py`, prompts) change only through the INTEGRATOR.
- **SYNC GATE 2** (after the band): integration tests across citations+memory+custom tools;
  resolve conflicts; only then proceed to P9/P10.

## 6. Execution Protocol (follow for every phase)

```
for phase in next_incomplete_phase(PROGRESS.md):
    1. READ      .agent/phases/phase-N-*.md  +  the plan.md sections it cites
    2. KICKOFF   spawn ARCHITECT → brief module/file plan (small, time-boxed)
    3. EXECUTE   for each WAVE in the phase file:
                     spawn one sub-agent per [P] task (parallel, in sync)
                     run [S] tasks in order; [S] after its wave = integration task
    4. TEST GATE   TESTER runs acceptance criteria → all green, else FIX LOOP (max 3)
    5. REVIEW GATE REVIEWER signs off vs plan.md (requirements, §8 errors, §9 security)
    6. RECORD    update PROGRESS.md (phase status, per-task checkboxes, notes)
    7. COMMIT    one commit per task: "feat(pN): Tm — <task title>"
```

**Task mode legend:** `[S]` = sequential (order matters / touches shared state).
`[P]` = parallel-safe → dispatch concurrent sub-agents in the same wave.

**Sub-agent dispatch template (use verbatim):**

```
DISPATCH ─ Sub-agent: <ROLE>  |  Phase: P<N>  |  Task: <P<N>.T<M>>
Read first : .agent/phases/phase-0N-*.md ; plan.md §<cited sections>
Scope      : ONLY the files listed under "Output" for your task. Do not touch
             files owned by other tasks/squads. Follow repo conventions.
Done when  : task acceptance bullet satisfied + unit test you wrote passes
Report back: files changed, tests run (pass/fail), open questions
```

**Sync rules (non-negotiable):**
1. A phase starts only when every dependency is `DONE` (tests green), never merely code-complete.
2. Parallel squads never edit each other's files; shared-file changes route through the INTEGRATOR.
3. No phase is marked `DONE` without TEST + REVIEW gates and a PROGRESS.md update.
4. The 15 scenarios of plan.md §10 are the project's final acceptance — run them in Phase 10
   against ≥ 2 real model backends + mock backends.

**Fix loop / failure policy:** if a TEST GATE fails, the IMPLEMENTER fixes and re-tests — max
3 iterations per phase. Still red ⇒ mark the phase `BLOCKED` in PROGRESS.md with a diagnosis,
continue only with independent phases, otherwise stop and report to the user.

**Guardrails (apply to every sub-agent):**
- Secrets: never hardcode; resolve only via `${ENV_VAR}` (§2, §9). `.env` stays gitignored.
- Every external call goes through the config-driven endpoint templates — no ad-hoc URLs.
- Every tool result passes input sanitization before entering a prompt (§9).
- Tool errors returned to the model follow the wording style of the §8 tables.
- Python 3.11+, async-first (`httpx`, `asyncio`), full type hints, `pytest`, `ruff`.
- Never log header values containing keys; log key *names* only (§9 Audit Logging).

## 7. Per-Phase Task Index

Deep detail (waves, ownership, acceptance criteria) lives in `phases/phase-0N-*.md`.
Summary of all 60 tasks:

**Phase 1 — LLM Wrapper (5 tasks)**
- P1.T1 `[S]` Repo scaffold: `research-harness/`, pyproject, package layout, pytest/ruff, `.gitignore` (+`.env`)
- P1.T2 `[P]` `LLMClient` — OpenAI-compatible chat completions, timeouts, typed connection errors
- P1.T3 `[P]` CLI REPL — input → response → print, graceful connection errors
- P1.T4 `[P]` Minimal config loader — llm.base_url / model_name / api_key_env from env
- P1.T5 `[S]` Smoke test vs mock server (+ live optional) + run instructions in README

**Phase 2 — Config System (6 tasks)**
- P2.T1 `[S]` Pydantic models for the full §2 schema (harness + endpoints + custom_endpoints)
- P2.T2 `[P]` `${ENV_VAR}` resolver + `.env` load, §9 priority, missing-key warnings (disable endpoint)
- P2.T3 `[P]` `{{placeholder|default:x}}` template engine (body, query params, URL path)
- P2.T4 `[P]` Validation + human-readable errors (malformed YAML ⇒ friendly message, no traceback)
- P2.T5 `[P]` Hot-reload watcher (≤5 s), atomic swap of live config
- P2.T6 `[S]` Config test suite + commit `config.yaml` / `.env.example` exactly per §2

**Phase 3 — Tool Registry (6 tasks)**
- P3.T1 `[S]` `Tool` base class + OpenAI function-calling schema generation
- P3.T2 `[P]` Registry auto-discovery from `endpoints` config; primary → fallback chains
- P3.T3 `[P]` Generic HTTP executor: template fill → async request → JSON/XML parse
- P3.T4 `[P]` Rate limiter + retry/backoff per endpoint config (honor `Retry-After`)
- P3.T5 `[P]` `web_search` implementation (Serper-shaped) + fixture tests
- P3.T6 `[P]` `fetch_url` implementation (Jina-reader-shaped) + truncation + fixture tests

**Phase 4 — Orchestration Loop (6 tasks)**
- P4.T1 `[S]` Tool-call parser: OpenAI native format + ReAct text fallback
- P4.T2 `[P]` Loop state machine (§4 Steps 1–7): iteration cap + force-final-answer
- P4.T3 `[P]` Parallel dispatch: `asyncio.gather`, `max_parallel`, per-call timeout, partial-failure injection
- P4.T4 `[P]` Malformed-output recovery: correction prompt at 3 strikes, tools-off at 5
- P4.T5 `[P]` System prompt builder: schemas + §5 citation rules + §8 fallback instructions
- P4.T6 `[S]` E2E loop tests with scripted mock LLM (chaining, iteration stop, recovery)

**Phase 5 — Citation Engine (7 tasks)**
- P5.T1 `[S]` Cross-turn `SourceRegistry` (ID assignment, lookup, prompt reference table)
- P5.T2 `[P]` Citation validator: `[n]` → real sources, orphan removal + warnings
- P5.T3 `[P]` URL validator: only tool-seen URLs; fabricated URLs stripped
- P5.T4 `[P]` Markdown link formatter: bare-URL wrapping, `link_format` support
- P5.T5 `[P]` Auto "Sources" section: dedupe, `max_sources_per_response`
- P5.T6 `[P]` Key scrubber: exact-match against resolved keys + §9 regex patterns
- P5.T7 `[S]` Pipeline assembly + system-prompt citation refinement + tests

**Phase 6 — Memory & Context (6 tasks)**
- P6.T1 `[S]` Token counter (tiktoken-compatible, fallback estimator)
- P6.T2 `[P]` Budget calculator (§6 formula) surfaced to the loop
- P6.T3 `[P]` Rolling summarizer (LLM call, `[Summary of turns X–Y]` header, 3–5× compression)
- P6.T4 `[P]` Document cache: in-memory + filesystem, TTL from config, instant re-serve
- P6.T5 `[P]` Context assembler with the 3-pass eviction strategy (§6)
- P6.T6 `[S]` Source-registry persistence + session save/resume + 20-turn stress test

**Phase 7 — Custom Endpoints (5 tasks)**
- P7.T1 `[S]` Dynamic tool generator from `custom_endpoints` entries
- P7.T2 `[P]` Parameter-schema inference from `{{placeholders}}` (+ type heuristics)
- P7.T3 `[P]` `tool_mapping` / `tool_description` handling + config validation rules
- P7.T4 `[P]` Fallback chain execution (primary → secondary for the same `tool_mapping`)
- P7.T5 `[S]` Mock-endpoint tests incl. hot-reload add/remove of tools (§10 Test 15)

**Phase 8 — Default Tool Suite (5 tasks)**
- P8.T1 `[P]` `academic_search` — arXiv API (XML) with fixture tests
- P8.T2 `[P]` `news_search` — NewsAPI-shaped, recency parameter
- P8.T3 `[P]` `extract_links` — fetch wrapper + link parser + regex filter
- P8.T4 `[P]` `summarize_page` — compound tool: fetch → side-channel LLM summarization
- P8.T5 `[P]` `compute` — sandboxed AST expression evaluator (`import os` ⇒ rejected)

**Phase 9 — Web UI (optional, 6 tasks)**
- P9.T1 `[S]` FastAPI scaffold, bound to `127.0.0.1` by default (§9)
- P9.T2 `[P]` Endpoint manager: add/edit/disable/test (keys masked)
- P9.T3 `[P]` Key management: mask to last 4 chars, write to `.env`, never echo values
- P9.T4 `[P]` Chat UI wired to the same orchestrator as the CLI
- P9.T5 `[P]` Tool execution log viewer (timing + result preview, no auth headers)
- P9.T6 `[S]` Sanitized config export/import + UI test pass

**Phase 10 — Hardening (8 tasks)**
- P10.T1 `[P]` Error-handling audit vs both §8 tables (every row has a test)
- P10.T2 `[P]` Performance pass: connection pooling, async I/O audit
- P10.T3 `[P]` Streaming responses end-to-end (CLI + UI)
- P10.T4 `[P]` Session-level request deduplication (query-hash cache)
- P10.T5 `[P]` Prompt tuning across Mistral / Llama 3 / Qwen / Phi profiles
- P10.T6 `[P]` User docs: setup (<30 min), config reference, troubleshooting
- P10.T7 `[P]` Developer docs: architecture, extension points
- P10.T8 `[S]` Packaging (console script, Dockerfile) + full 15-scenario acceptance run

---

## 8. Kickoff Instruction (to the executing agent)

You are the ORCHESTRATOR. Begin now:

1. `cat .agent/PROGRESS.md` → find the first phase without status `DONE`.
2. Open that phase's brief in `.agent/phases/` and the plan.md sections it cites.
3. Run the §6 Execution Protocol. Dispatch sub-agents with the §6 template.
4. After every phase: update PROGRESS.md, commit, move to the next phase.
5. Do not stop at "code complete" — a phase is done only when its TEST and REVIEW gates pass.
6. When Phase 10 completes, run the 15-scenario final acceptance and report the full results.
