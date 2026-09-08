# Phase 10 — Hardening, Optimization & Polish

> **Squad:** Squad-QA · **Depends on:** all phases (or P9 skipped) · **Tasks:** 8
> **Source of truth:** `plan.md` §7-Phase 10, §8 (edge cases), §9 (security), §10 (15 scenarios)

## Goal

Production readiness: every §8 edge case has a test, performance is tuned, streaming works,
docs enable a < 30-minute setup, the package installs cleanly — and the full 15-scenario
acceptance suite from plan.md §10 passes.

## Preconditions

- P1–P8 `DONE` (and P9 `DONE` or `SKIPPED`); SYNC GATE 2 integrated.

## Tasks

| ID | Task | Mode | Owner | Output |
|---|---|---|---|---|
| P10.T1 | Error-handling audit: walk both §8 tables row by row — every scenario (auth, 429, 5xx, DNS, timeout, malformed, empty, zero-results, unconfigured tool, circular calls) has a test asserting the exact §8 behavior | `[P]` | IMPLEMENTER-A | `tests/test_edge_cases.py` |
| P10.T2 | Performance pass: shared async httpx client w/ connection pooling, no sync I/O in async paths, cache-hit fast path benchmarked | `[P]` | IMPLEMENTER-B | perf fixes + `tests/test_perf_smoke.py` |
| P10.T3 | Streaming: token-by-token output end-to-end (CLI + UI if built), streaming must not break citation post-processing (buffer final segment) | `[P]` | IMPLEMENTER-B | `llm/client.py` stream mode + tests |
| P10.T4 | Request deduplication: session-level `(tool, params_hash)` cache across turns — repeat query returns the cached result with the §8 note | `[P]` | IMPLEMENTER-C | `memory/dedup.py` + tests |
| P10.T5 | Multi-model prompt tuning: run the §4/§5 prompts against Mistral, Llama 3, Qwen, Phi profiles (mock + live if available); per-model system-prompt tweaks stored as profiles | `[P]` | IMPLEMENTER-C | `loop/prompts.py` profiles + report |
| P10.T6 | User docs: `docs/setup.md` (< 30-minute path), `docs/config-reference.md` (every §2 key), `docs/troubleshooting.md` (maps §8 errors to fixes) | `[P]` | DOCS-A | docs |
| P10.T7 | Developer docs: `docs/architecture.md` (§1 components + loop flow), `docs/extending.md` (add a tool / custom endpoint), inline module docstrings reviewed | `[P]` | DOCS-A | docs |
| P10.T8 | Packaging + FINAL ACCEPTANCE: console_scripts (`harness`, `harness-ui`), Dockerfile, `pip install -e .` verified clean; run all 15 §10 scenarios, record results in PROGRESS.md Final Acceptance Log, verify ≥ 3 backends | `[S]` | TESTER | packaging + acceptance log |

## Execution Waves

1. **Wave 1 (parallel):** P10.T1–P10.T7 (audit/perf/streaming/dedup/tuning/docs).
2. **Wave 2 (sequential):** P10.T8 — packaging, then the full acceptance run. No phase-10
   `DONE` until the 15-row Final Acceptance Log in PROGRESS.md is filled with passing results.

## Acceptance Criteria (from plan.md §7-P10)

- [ ] All test scenarios from plan.md §10 pass (15/15 in the log)
- [ ] Works with at least 3 different local model backends (Ollama + llama.cpp server + vLLM,
  or mock-equivalents where hardware is unavailable — documented in the log)
- [ ] 50+ turn conversations without degradation (extended P6 stress test)
- [ ] Streaming responses work for the user
- [ ] A new user can set up in < 30 minutes following `docs/setup.md` (walkthrough-verified)
- [ ] `pip install -e .` + Docker build succeed from a clean checkout
- [ ] §9 security checklist re-verified on the final build (no keys in repo/logs/responses)

## Handoff

- Project complete. Report to the user: acceptance log, known limitations, and how to run.
