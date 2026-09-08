# Phase 02 — Configuration System

> **Squad:** Squad-Core (spine) · **Depends on:** P1 · **Tasks:** 6
> **Source of truth:** `plan.md` §2 (full YAML schema + resolution rules), §7-Phase 2, §9 (key priority)

## Goal

Full config file parsing exactly per plan.md §2: `${ENV_VAR}` resolution, `{{placeholder|default:x}}`
templates, validation with human-readable errors, and hot-reload without restart.

## Preconditions

- Phase 1 `DONE` (package + minimal config loader exist).

## Tasks

| ID | Task | Mode | Owner | Output |
|---|---|---|---|---|
| P2.T1 | Pydantic models mirroring the §2 schema 1:1: `harness.llm`, `harness.orchestration`, `harness.memory`, `harness.response`, `endpoints.*` (url, method, headers, body_template, query_params_template, response_parsing, rate_limit, retry, enabled), `custom_endpoints.*` (incl. tool_mapping, tool_description) | `[S]` | IMPLEMENTER-A | `config/models.py` |
| P2.T2 | Env resolver: load `.env` (python-dotenv), then resolve every `${VAR}` per §9 priority (system env → `.env`); missing key ⇒ log warning naming the key (never the value) and disable the affected endpoint | `[P]` | IMPLEMENTER-A | `config/resolver.py` |
| P2.T3 | Template engine: fill `{{placeholder}}` and `{{placeholder|default:x}}` in body templates, query-param templates, and URL paths; strict mode raises on unresolved required placeholders; JSON-safe escaping for string substitution | `[P]` | IMPLEMENTER-B | `config/templates.py` |
| P2.T4 | Validation + error reporting: required fields, type checks, URL format; malformed YAML ⇒ friendly one-screen error (file, line, hint) — never a raw stack trace | `[P]` | IMPLEMENTER-C | `config/validation.py` |
| P2.T5 | Hot-reload: file watcher (watchfiles/polling fallback) detecting changes ≤ 5 s; atomic swap of the live config object; registry-notified hook for Phase 7 | `[P]` | IMPLEMENTER-B | `config/watcher.py` |
| P2.T6 | Test suite + committed artifacts: `config.yaml` and `.env.example` committed byte-faithful to §2; tests for every resolution rule (§2 "Configuration Resolution Rules" 1–5) | `[S]` | TESTER | `tests/test_config_*.py`, `config.yaml`, `.env.example` |

## Execution Waves

1. **Wave 1 (sequential):** P2.T1 — models are imported by everything else.
2. **Wave 2 (parallel):** P2.T2 + P2.T3 + P2.T4 + P2.T5.
3. **Wave 3 (sequential):** P2.T6 — TESTER + REVIEWER gate.

## Acceptance Criteria (from plan.md §7-P2)

- [ ] Config loads and validates without errors (committed `config.yaml` is the fixture)
- [ ] Missing required fields produce clear error messages
- [ ] Environment variables resolve per priority; missing keys disable endpoints with a warning
- [ ] Malformed YAML produces a helpful error, not a stack trace
- [ ] Config changes are detected and reloaded within 5 seconds (test with tmp_path + sleep/poll)
- [ ] Resolution rules 1–5 of §2 each have a dedicated test

## Handoff to Phase 3

- `HarnessConfig` object (typed, validated, hot-swappable) is the API Phase 3 builds on.
- Template engine and env resolver are the primitives the generic HTTP executor composes.
