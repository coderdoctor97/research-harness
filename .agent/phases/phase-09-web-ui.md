# Phase 09 — Web UI Configuration Panel (OPTIONAL)

> **Squad:** Squad-UI · **Depends on:** SYNC GATE 2 · **Tasks:** 6
> **Source of truth:** `plan.md` §7-Phase 9, §9 (UI security: localhost bind, masked keys)

> **ORCHESTRATOR NOTE:** confirm with the user before starting this phase. If declined,
> mark Phase 9 `SKIPPED` in PROGRESS.md and jump to Phase 10 (its criteria don't depend on the UI).

## Goal

A lightweight local web panel (FastAPI + minimal HTML, or Gradio/Streamlit) for managing
endpoints, testing tools, and chatting — bound to `127.0.0.1` only, keys always masked.

## Preconditions

- SYNC GATE 2 passed (P1–P8 integrated).

## Tasks

| ID | Task | Mode | Owner | Output |
|---|---|---|---|---|
| P9.T1 | App scaffold: FastAPI app, bind `127.0.0.1` by default (override explicit only, per §9), static assets inline, launch via `harness-ui` command | `[S]` | IMPLEMENTER-A | `ui/app.py` |
| P9.T2 | Endpoint manager: list/add/edit/disable endpoints and test-fire one with sample params showing the raw parsed result; edits write to config + trigger hot-reload | `[P]` | IMPLEMENTER-A | `ui/routes_endpoints.py` |
| P9.T3 | Key management: show masked keys (last 4 chars only), set/update writes to `.env` via the resolver; server responses NEVER include resolved values | `[P]` | IMPLEMENTER-B | `ui/routes_keys.py` |
| P9.T4 | Chat interface: same orchestrator instance as the CLI (parity requirement), shows tool-call trace per answer, citation rendering as in CLI | `[P]` | IMPLEMENTER-B | `ui/routes_chat.py` |
| P9.T5 | Tool execution log viewer: timestamped calls with timing and result previews; auth headers and key values filtered out before render (§9 Audit Logging) | `[P]` | IMPLEMENTER-C | `ui/routes_logs.py` |
| P9.T6 | Sanitized config export/import (keys stripped/re-inserted via env names) + end-to-end UI tests (TestClient) | `[S]` | TESTER | `ui/routes_config.py` + tests |

## Execution Waves

1. **Wave 1 (sequential):** P9.T1.
2. **Wave 2 (parallel):** P9.T2 + P9.T3 + P9.T4 + P9.T5.
3. **Wave 3 (sequential):** P9.T6 + TEST/REVIEW gates.

## Acceptance Criteria (from plan.md §7-P9)

- [ ] Add a new endpoint through the UI → immediately usable in chat (hot-reload proves it)
- [ ] API keys are masked in the UI (only last 4 chars); no response ever carries a resolved key
- [ ] A tool can be tested independently (fill params → see raw result)
- [ ] Chat quality/behavior is identical to the CLI (same orchestrator)
- [ ] Server binds to localhost only by default

## Handoff to Phase 10

- UI shares the orchestrator entry `create_application()` — Phase 10's streaming work (P10.T3)
  covers both CLI and UI surfaces.
