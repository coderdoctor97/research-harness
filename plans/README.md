# plans/ — Improvement Program Index

> **Read this first.** Three plans upgrade the finished harness (all 10 build phases `DONE`)
> toward the full vision in [`../plan.md`](../plan.md). Execution rules live in
> [`../.agent/agent.md`](../.agent/agent.md). Progress is tracked in
> [`../.agent/PROGRESS.md`](../.agent/PROGRESS.md).

## The plans

| Plan | File | Domain | Vision anchor (plan.md) |
|---|---|---|---|
| **Engine Improvement** | [`engine-improvement-plan.md`](engine-improvement-plan.md) | Core execution mechanics, system architecture, application harnessing | §1 Architecture · §4 Orchestration Loop · §8 Edge Cases |
| **AI Integration** | [`ai-integration-plan.md`](ai-integration-plan.md) | AI workflows, integration pipelines, dedicated research capabilities | §2 Providers · §3 Tools · §5 Citations · Capabilities #1–#3 |
| **UI Improvement** | [`ui-improvement-plan.md`](ui-improvement-plan.md) | Interface refinement — **strictly via the existing UI skills** | §5 Output format · §7-P9 · Capability #4 |

## Uniform structure (all three plans)

```
Phase (E/A/U n)  →  Sub-phase (n.m)  →  Sub-task (n.m.k)
```

Every sub-task carries: mode `[S]`/`[P]`, a concrete time estimate, a verifiable
acceptance check, and a **vision trace** back to plan.md. No task exists that does
not serve the vision.

## Gaps these plans close (baseline review, 2026-09-13)

| # | Finding | Closed by |
|---|---|---|
| F1 | `ui/routes_chat.py` re-implements the agent loop; CLI bypasses `harness/loop` too — three divergent cores | E2 |
| F2 | `LLMClient.stream_chat` tested in isolation but wired to no surface | E3 |
| F3 | Loop fragments (parser/dispatcher/recovery) not assembled into plan.md §4's full flow on a shared core | E2, E4 |
| F4 | Vision capability #1 (multi-query fan-out search) absent from `src/` | A2 |
| F5 | Citation pipeline exists but is not integrated into a research-grade synthesis workflow | A3 |
| F6 | Vision capability #4 (reactive text inspection: highlight → anchored breakdown) unimplemented | U2 |
| F7 | UI skills applied once (2026-09-12); no DESIGN.md, no scored audit baseline | U1 |

## Efficiency layer (strict constraint — always on)

Two vendored agent skills in [`../.claude/skills/`](../.claude/skills/) make every
plan step cheaper and faster. They are **mandatory**, not optional:

| Skill | Source | Role in this program |
|---|---|---|
| **ponytail** (+ `ponytail-audit`, `ponytail-debt`, `ponytail-review`) | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) (MIT) | *Implementation efficiency.* The 7-rung ladder before any code (reuse → stdlib → native → one-line → minimum); shortest working diff; deletion over addition; deliberate simplifications tagged `ponytail: <ceiling>, <upgrade path>`; every diff reviewed with `ponytail-review`; every sync point runs `ponytail-debt`. Measured effect: ~54% less code, ~27% faster. |
| **i-have-adhd** | [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) (MIT) | *Execution speed of communication.* All reports, PROGRESS.md entries, and handoffs are action-first, numbered, restate state every turn ("Phase E2 of 5 — sub-phase 2.3 done"), carry specific time estimates, and make wins visible. No preamble, no buried results. |

How they bind into execution:

1. **Before writing code** → climb the ponytail ladder; if a rung holds, stop there.
2. **During** → deliberate shortcuts get a `ponytail:` comment (ceiling + upgrade path).
3. **At every REVIEW gate** → `ponytail-review` the diff; net-LOC delta recorded in PROGRESS.md.
4. **At every sync point** → `ponytail-debt` harvests the ledger; nothing deferred rots silently.
5. **Every report/update** → i-have-adhd format (next action first; state restated; one concrete next step at the end).

## Recommended execution order

```
E1 (audit, read-only) ──┬─► E2 (consolidate core) ──► A2 ──► A3 ──┐
U1 (skill audit, read-only) ─────────────────────────────────────┼─► E3 ──► U2 ──► U3 ─►
A1 (provider hardening, independent) ────────────────────────────┘   E4/E5 · A4/A5 · U4/U5
```

- E1 and U1 are read-only audits — run them first, in parallel, same session if possible.
- E2 is the keystone: A2/A3 (research workflow) and U2/U3 (rendering its output) build on the consolidated core.
- E3 (streaming) precedes U3.3 (streaming render).
- A1, E4, E5, A4, A5, U4, U5 slot into remaining bandwidth; dependency details are in each plan's header.

## Hard constraints (apply to every plan)

1. **No new product features** beyond the structural / architectural / AI / UI improvements specified here. Completing declared vision capabilities (#1 multi-query, #4 reactive inspection) is alignment, not a new feature.
2. **All UI work executes strictly through the existing UI skills** (frontend-design, hallmark, impeccable) — audit before edit, skill pass after edit, skill re-score before sign-off.
3. **No new runtime dependencies.** Patterns from `references/architectural_references.json` (Floating UI, Tiptap, Perplexica, Crawl4AI…) are studied and re-implemented natively per ponytail rung 4 — adopt the pattern, not the package.
4. **bugfix.json `rules_for_agents` are law** for any file they touch (UI state, async-in-routes, templates, keys).
5. Zero secrets in code/config (`${ENV_VAR}` only); UI binds `127.0.0.1` by default; keys always masked.
