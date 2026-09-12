# Phase 02 — Config System

> **Squad:** Squad-Core (spine) · **Depends on:** P1 · **Tasks:** 6
> **Source of truth:** `plan.md` §2, §7-Phase 2, §9 (secrets/ENV_VAR)

## Goal

A full config layer: YAML loading, `${ENV_VAR}` resolution, `{{placeholder}}` templates,
schema validation with friendly errors, and a hot-reload watcher. Phase 1's flat
`config.py` is fully replaced.

## Preconditions

- Phase 1 complete (`LLMClient`, package layout, `.env` gitignored, zero secrets).

## Tasks

| ID | Task | Mode | Owner | Output |
|---|---|---|---|---|
| P2.T1 | Pydantic models for full §2 schema (harness + endpoints + custom_endpoints) | `[S]` | IMPLEMENTER-A | `config/models.py` |
| P2.T2 | `${ENV_VAR}` resolver + `.env` load; §9 priority; missing-key warning → disable endpoint | `[P]` | IMPLEMENTER-A | `config/resolver.py` + tests |
| P2.T3 | `{{placeholder\|default:x}}` template engine (body, query params, URL path) | `[P]` | IMPLEMENTER-B | `config/templates.py` + tests |
| P2.T4 | Validation + human-readable errors; malformed YAML ⇒ friendly message, no traceback | `[P]` | IMPLEMENTER-C | `config/validation.py` + tests |
| P2.T5 | Hot-reload watcher (≤5 s poll); atomic swap of live config dict | `[P]` | IMPLEMENTER-C | `config/watcher.py` |
| P2.T6 | Config test suite + commit `config.yaml` / `.env.example` exactly per §2 | `[S]` | TESTER | `tests/test_config_system.py`, `config.yaml`, `.env.example` |

## Execution Waves

1. **Wave 1 (sequential):** P2.T1 — schema first; nothing else compiles without it.
2. **Wave 2 (parallel, in sync):** P2.T2 + P2.T3 + P2.T4 + P2.T5 — four disjoint files.
3. **Wave 3 (sequential):** P2.T6 — TESTER wires everything + committed artifacts.

## Acceptance Criteria (from plan.md §7-P2)

- [ ] `${ENV_VAR}` resolves in base_url, headers, body; missing key → warning, endpoint disabled
- [ ] `{{placeholder|default:x}}` works in URL, query params, body templates
- [ ] Malformed YAML produces friendly error; no traceback leaks to CLI
- [ ] Hot-reload picks up YAML change within ≤5 s; in-flight requests complete with old config
- [ ] `config.yaml` and `.env.example` present and match §2 schema exactly
- [ ] `pytest` fully green; `ruff check` clean
- [ ] Zero secrets in committed files (`.env` gitignored)

## Handoff to Phase 3

- `research-harness/src/harness/config/` is the canonical config package.
- `models.py` exports `HarnessConfig` — Phase 3's registry imports it.
