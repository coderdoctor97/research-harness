# Phase 07 — Custom Endpoints & Dynamic Tool Generation

> **Squad:** Squad-Extensibility (parallel band) · **Depends on:** P3 · **Tasks:** 5
> **Source of truth:** `plan.md` §3.8 (`custom_endpoint`), §7-Phase 7, §10 Test 8/15

## Goal

Zero-code extensibility: a user adds a YAML block under `custom_endpoints` and the harness
auto-generates a callable LLM tool — schema inferred, executed, parsed, hot-reloaded.

## Preconditions

- Phase 3 `DONE` (Tool base class + executor). Runs in the parallel band — touches ONLY
  `src/harness/registry/dynamic.py` and `registry/fallback.py` (ownership map, agent.md §5).

## Tasks

| ID | Task | Mode | Owner | Output |
|---|---|---|---|---|
| P7.T1 | Dynamic tool generator: one `custom_endpoints` entry → one `Tool` (name = key, description = `tool_description`, execution via the generic executor + custom `response_parsing`) | `[S]` | IMPLEMENTER-A | `registry/dynamic.py` |
| P7.T2 | Parameter-schema inference: scan `body_template` + `query_params_template` + URL path for `{{placeholders}}` → JSON-schema properties; type heuristics (`{{n|default:5}}` ⇒ integer, `default:null` ⇒ optional); `required` = placeholders without defaults | `[P]` | IMPLEMENTER-A | part of `dynamic.py` |
| P7.T3 | Config fields + validation: honor `tool_mapping` (group under a logical tool), `enabled` toggle; malformed custom entry ⇒ friendly config error listing the offending fields, other endpoints unaffected | `[P]` | IMPLEMENTER-B | `registry/validation_extras.py` |
| P7.T4 | Fallback chain execution: multiple enabled endpoints sharing one `tool_mapping` form a primary → secondary chain; failover on §8 triggers (auth, 429, 5xx); config `enabled:false` or removed key ⇒ tool disappears on hot-reload | `[P]` | IMPLEMENTER-C | `registry/fallback.py` |
| P7.T5 | Tests with a local mock endpoint: add tool via config → appears in `list_schemas()`; model-shaped call returns parsed results; remove entry → gone after reload (§10 Test 15); broken entry ⇒ clear error (§10 Test 8) | `[S]` | TESTER | `tests/test_dynamic_tools.py` |

## Execution Waves

1. **Wave 1 (sequential):** P7.T1.
2. **Wave 2 (parallel):** P7.T2 + P7.T3 + P7.T4.
3. **Wave 3 (sequential):** P7.T5 + TEST/REVIEW gates.

## Acceptance Criteria (from plan.md §7-P7)

- [ ] Add a custom endpoint in config → tool appears in the model's tool list
- [ ] Model-shaped calls succeed and results parse per custom `response_parsing` rules
- [ ] Remove/disable a custom endpoint → tool disappears from the registry (hot-reload, no restart)
- [ ] Malformed custom endpoint config produces a clear error
- [ ] Failed primary endpoint fails over to the secondary for the same `tool_mapping`

## Handoff to the Sync Gate

- Register the generator into the registry bootstrap so hot-reload (P2.T5) rebuilds dynamic
  tools — the INTEGRATOR owns `registry/index.py`, so deliver `register_dynamic_tools(registry, config)`
  as a clean function for them to call.
