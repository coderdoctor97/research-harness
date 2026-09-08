# Phase 01 — Bare-Bones LLM Wrapper

> **Squad:** Squad-Core (spine) · **Depends on:** nothing · **Tasks:** 5
> **Source of truth:** `plan.md` §7-Phase 1, §2 (`harness.llm` block), §8 (error style)

## Goal

A CLI application that accepts user input, sends it to a local LLM server
(Ollama / llama.cpp / vLLM — any OpenAI-compatible endpoint), and prints the response —
with connection errors handled gracefully. This is the skeleton everything else hangs on.

## Preconditions

- None. This is the first phase.

## Tasks

| ID | Task | Mode | Owner | Output |
|---|---|---|---|---|
| P1.T1 | Repo scaffold: `research-harness/` with `pyproject.toml` (deps: `httpx`, `pyyaml`, `pydantic`, `pytest`, `ruff`), `src/harness/` package layout (`llm/`, `cli.py`), `tests/`, `.gitignore` including `.env` | `[S]` | IMPLEMENTER-A | runnable empty package, `pytest` green |
| P1.T2 | `LLMClient` (`llm/client.py`): OpenAI-compatible `POST /v1/chat/completions`, configurable `base_url`, `model_name`, `api_key_env` (may be `none`), timeouts, typed exceptions (`LLMConnectionError`, `LLMResponseError`), non-streaming for now | `[P]` | IMPLEMENTER-A | `llm/client.py` + unit tests (mock transport) |
| P1.T3 | CLI REPL (`cli.py`): read line → send → print; `/quit` to exit; connection errors print a friendly one-line message, never a traceback | `[P]` | IMPLEMENTER-B | `cli.py` |
| P1.T4 | Minimal config loader (`config.py`): read `llm.base_url`, `llm.model_name`, `api_key_env` resolved from the process env; CLI flags override config | `[P]` | IMPLEMENTER-C | `config.py` + tests |
| P1.T5 | Integration smoke test: pytest fixture spins up a mock OpenAI-compatible server (local http server or respx mock); optional `--live` test against a real endpoint if `LOCAL_LLM_BASE_URL` is set; README "Quickstart" section | `[S]` | TESTER | `tests/test_smoke.py`, README |

## Execution Waves

1. **Wave 1 (sequential):** P1.T1 — nothing exists until the scaffold lands.
2. **Wave 2 (parallel, in sync):** P1.T2 + P1.T3 + P1.T4 — three IMPLEMENTERs, disjoint files.
3. **Wave 3 (sequential):** P1.T5 — TESTER wires everything together.

## Acceptance Criteria (from plan.md §7-P1)

- [ ] Connects to a running Ollama/llama.cpp/vLLM instance (verified by mock + optional live test)
- [ ] Sends a message and receives a coherent response
- [ ] Connection refused / timeout produce a clean error message, no crash, no traceback
- [ ] `pytest` fully green; `ruff check` clean
- [ ] `.env` is gitignored; no keys anywhere in the repo

## Handoff to Phase 2

- `research-harness/` package exists with the `harness.config` module Phase 2 replaces/extends.
- `LLMClient` is the single entry point for inference; document its public signature in the
  module docstring — Phases 4, 6, 8 build against it.
