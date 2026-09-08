# Phase 04 — Orchestration Loop (Core Agent)

> **Squad:** Squad-Core (spine) · **Depends on:** P3 · **Tasks:** 6
> **Source of truth:** `plan.md` §4 (full decision flow), §7-Phase 4, §5 (system prompt rules), §8

## Goal

The full agent loop: model reasons → requests tools → harness dispatches (parallel where
independent) → results injected → repeat until final answer, iteration cap, or recovery.

## Preconditions

- Phase 3 `DONE` (`list_schemas()`, `dispatch()`, `LLMClient` frozen APIs). **SYNC GATE 1:**
  orchestrator reviews + freezes the Tool interface, Loop event types, and config models before
  the parallel band (P5–P8) starts.

## Tasks

| ID | Task | Mode | Owner | Output |
|---|---|---|---|---|
| P4.T1 | Tool-call parser: (a) native OpenAI `tool_calls` arrays, (b) ReAct text fallback (`Action:`/`Action Input:`); classify output as `FINAL_ANSWER` / `TOOL_CALL` / `MALFORMED`; unit tests with messy real-model outputs | `[S]` | IMPLEMENTER-A | `loop/parser.py` |
| P4.T2 | Loop state machine implementing §4 Steps 1–7: context assembly, inference, classification, dispatch, result injection (source-ID assignment hook for P5), iteration check, post-processing hook; `max_tool_iterations` + force-final-answer injection | `[P]` | IMPLEMENTER-A | `loop/agent.py` |
| P4.T3 | Parallel dispatch engine: independent calls via `asyncio.gather` up to `max_parallel`, per-call timeout, partial-failure injection (successes + one error message), sequential mode when a call consumes a prior result | `[P]` | IMPLEMENTER-B | `loop/dispatcher.py` |
| P4.T4 | Malformed-output recovery: correction prompt at 3 strikes, tools-disabled direct answer at 5 (§4); duplicate-call guard — cache `(tool, params_hash)` per run, return cached result with note (§8 Circular Tool Calls) | `[P]` | IMPLEMENTER-C | `loop/recovery.py` |
| P4.T5 | System prompt builder: tool schemas + §5 citation rules (mandatory `[n]`, hyperlink format, Sources section, no fabricated URLs, no key leakage) + §8 fallback instructions + `fallback_to_training_knowledge` flag | `[P]` | IMPLEMENTER-B | `loop/prompts.py` |
| P4.T6 | E2E tests with a scripted mock LLM (queues of canned responses): single-tool answer, chained search→fetch across iterations, iteration-cap stop, malformed → correction → recovery, no-tool-needed question answered directly, parallel timing assertion | `[S]` | TESTER | `tests/test_loop_*.py` |

## Execution Waves

1. **Wave 1 (sequential):** P4.T1 — classification drives everything.
2. **Wave 2 (parallel):** P4.T2 + P4.T3 + P4.T4 + P4.T5.
3. **Wave 3 (sequential):** P4.T6 + TEST/REVIEW gates.

## Acceptance Criteria (from plan.md §7-P4)

- [ ] "What happened in tech news today?" (mocked) → model calls `web_search`, answer carries citations
- [ ] Multi-step question chains `web_search` + `fetch_url` across iterations
- [ ] Loop stops after `max_tool_iterations` and forces a final answer
- [ ] Malformed tool calls trigger the correction prompt; 5 strikes → tools-off direct answer
- [ ] Simple training-knowledge questions trigger zero tool calls
- [ ] Parallel calls finish in ~1 request time, not 2× (timing assertion in tests)

## Handoff to Phase 5/6 (parallel band)

- Loop exposes `events`: `on_tool_result(results)`, `on_final_answer(text)` — P5 hooks citation
  post-processing into `on_final_answer`, P6 hooks budgeting into context assembly.
- Result injection already stamps provisional source IDs — P5 formalizes them in SourceRegistry.
