# AGENT.md — Master Execution Brief (Improvement Program)

**Project:** LLM Research Harness — an **autonomous academic/deep-research engine** (not a conversational chatbot).
**Vision / source of truth:** [`../plan.md`](../plan.md) — every phase, sub-phase, and sub-task in the program must trace back to it.
**Execution plans:** [`../plans/`](../plans/) — three structured plans (Engine · AI Integration · UI). The original 10-phase build is `DONE`; **this program is what you execute now.**
**This file:** the operating manual. It tells you which plan to open, how to walk it, and the two always-on efficiency skills that make execution fast.

> **START HERE.** If you are an agent reading this file:
> 1. Activate the efficiency layer (§1) — it is a strict constraint, not a suggestion.
> 2. `cat .agent/PROGRESS.md` → find the first improvement phase not marked `DONE`.
> 3. Open that phase's plan in `../plans/` and follow §4 (Execution Protocol) exactly.

---

## 0. Product Identity (unchanged — the vision baseline)

Four declared capabilities; every task serves at least one:

1. **Multi-query web/paper searches** — fan out one research question into several targeted queries, aggregate results. *(gap → plans/ai-integration-plan.md A2)*
2. **Live-content ingestion** — fetch pages → LLM-ready clean markdown, links harvested. *(A4)*
3. **Research-grade synthesis** — one answer, verified inline citations, clickable anchor hyperlinks. *(A3, U3)*
4. **Reactive text inspection** — selecting/highlighting a phrase triggers an anchored definition or deeper breakdown. *(U2)*

Two kinds of knowledge: **`skills/`** = callable runtime tools (`src/harness/tools/`, `registry/`, `mcp/`); **`references/`** = architectural patterns studied before building, never imported at runtime (`references/architectural_references.json`).

---

## 1. Efficiency Layer (STRICT CONSTRAINT — always on)

Two skills are vendored in [`../.claude/skills/`](../.claude/skills/). They are **mandatory for every task in every plan**. Their whole purpose is implementation efficiency and speed; skipping them violates the program's constraints.

### 1.1 ponytail — write less, ship faster

Source: [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) (MIT) · skills: `ponytail`, `ponytail-audit`, `ponytail-debt`, `ponytail-review`.

- **Before any code, climb the ladder — stop at the first rung that holds:**
  1. Does this need to exist at all? (YAGNI)
  2. Already in this codebase? Reuse it. *(This repo is full of finished machinery: loop, registry, citations, memory, MCP. Build on it; don't re-write it.)*
  3. Stdlib does it? Use stdlib.
  4. Native platform feature? Use it. *(e.g. `window.getSelection()` + CSS for capability #4 — not Tiptap/Floating UI packages.)*
  5. Already-installed dependency? Use it.
  6. One line? One line.
  7. Only then: minimum code that works.
- **Deletion over addition.** The Engine plan's keystone (E2) is measured in lines *removed*.
- **Bug fix = root cause**, one shared guard, not per-caller patches.
- **No new runtime dependencies, no unrequested abstractions.** Reference frameworks in `references/` are patterns to study, not packages to install.
- **Deliberate simplifications** get a `ponytail: <ceiling>, <upgrade path>` comment. `ponytail-debt` harvests them at every sync point — a deferral with no trigger is a defect.
- **Every REVIEW gate runs `ponytail-review`** on the diff; **E1/E5 run `ponytail-audit`** repo-wide.
- Not lazy about: understanding the flow before cutting, input validation, error handling, security, accessibility, and leaving ONE runnable check per non-trivial change.

### 1.2 i-have-adhd — communicate so work moves

Source: [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) (MIT) · skill: `i-have-adhd`.

Every report, commit summary, PROGRESS.md entry, and handoff you produce follows its rules:

1. **Lead with the next action** — first line is something the reader can do.
2. **Number multi-step work** — one bounded action per step.
3. **Restate state every turn** — "Phase E2 of 5 — sub-phase 2.2 done (3/3 tasks). Next: E2.3 gate."
4. **Specific time estimates** — "about 2 hours", never "some work".
5. **Suppress tangents** — finish the task; surface side-issues once, at the end.
6. **Make wins visible** — "Chat and CLI now share one loop; −412 lines. Verify: `pytest tests/test_loop_e2e.py`."
7. **Matter-of-fact errors** — cause and fix, no drama.

### 1.3 Why this is a hard constraint

Measured on real agentic sessions, ponytail cuts ~54% of written code and ~27% of time while keeping safety at 100%; adhd-shaped reporting removes the re-reading/re-asking overhead between turns. The program's plans already embed both (audit phases, debt ledgers, net-LOC accounting, state-restating progress entries). Execute them as written.

---

## 2. Document Map & Navigation Pathways

```
plan.md                          ← VISION baseline (traceability target for every task)
plans/                           ← THE PLANS (all generated planning lives here, nowhere else)
├── README.md                    ← index · gap findings F1–F7 · execution order · hard constraints
├── engine-improvement-plan.md   ← E1–E5: execution mechanics, architecture, harnessing
├── ai-integration-plan.md       ← A1–A5: AI workflows, pipelines, research capabilities
└── ui-improvement-plan.md       ← U1–U5: UI refinement — strictly via existing UI skills
.agent/
├── agent.md                     ← you are here
├── PROGRESS.md                  ← live tracker (append-only; improvement program section at bottom)
└── phases/                      ← ARCHIVE of the completed 10-phase build (history; do not extend)
references/architectural_references.json  ← pattern registry per capability (study before building)
skills-dictionary/               ← skill catalog + usage log (update when you use a skill)
bugfix.json                      ← prevention rules — LAW for any file they touch
.claude/skills/                  ← UI skills (frontend-design, hallmark, impeccable)
                                   + efficiency skills (ponytail*, i-have-adhd)
docs/                            ← user/dev docs — keep in sync when behavior changes
```

**Pathway table — intent to plan:**

| You are asked to / you need to… | Open | Walk |
|---|---|---|
| Fix or restructure the agent loop, CLI/UI wiring, streaming, perf, dedup, memory mechanics | `plans/engine-improvement-plan.md` | Phase → sub-phase → sub-task tables in order |
| Touch providers, keys, model discovery, multi-query fan-out, citations, ingestion quality, research prompts | `plans/ai-integration-plan.md` | same |
| Change ANY pixels: console panels, chat rendering, popover, citations display, polish, a11y | `plans/ui-improvement-plan.md` | same — and only via the UI skills named in each task |
| Unsure which domain owns a task | `plans/README.md` → gap table + execution order | then the owning plan |
| About to design/upgrade one of the four capabilities | `references/architectural_references.json` → study mapped pattern first | then the plan task |
| About to touch `ui/` routes, state, or `index.html` | `bugfix.json` → `rules_for_agents` | then the plan task |

**Traceability rule:** before executing any sub-task, check its *Vision trace* column. If you cannot tie what you're about to do to plan.md or a declared capability, stop and don't do it (YAGNI — ladder rung 1).

---

## 3. Mission, Scope & Constraints

**Mission:** execute the three plans in `plans/` to completion — closing findings F1–F7 and realizing all four vision capabilities — while the codebase gets *leaner*, not bigger.

**Program-level Definition of Done:**

- [ ] All 15 phases (E1–E5, A1–A5, U1–U5) marked `DONE` in PROGRESS.md's Improvement Program Tracker
- [ ] Capability status: #1 multi-query ✅ · #2 ingestion ✅ · #3 cited synthesis ✅ · #4 reactive inspection ✅
- [ ] CLI and UI chat run on ONE shared loop core; streaming live end-to-end (E2/E3)
- [ ] `ponytail-audit` re-run at E5.1.2 shows improvement; every `ponytail:` debt marker has a trigger
- [ ] hallmark + impeccable re-scores improved vs U1 baseline (U5.1)
- [ ] plan.md §10's 15 scenarios still PASS + new research scenarios R1/R2 PASS (A5.1)
- [ ] `pytest` + `ruff` green; zero secrets in code/config; UI bound to `127.0.0.1` by default

**Hard constraints (non-negotiable):**

1. **No new product features** outside the plans. Completing declared capabilities #1–#4 is alignment, not addition. Anything else → reject per ladder rung 1, log the rejection in one line.
2. **UI work executes strictly through the existing UI skills** (frontend-design, hallmark, impeccable). Audit before edit, skill pass after edit, skill re-score before sign-off. No skill, no merge.
3. **No new runtime dependencies.** Patterns from `references/` are re-implemented natively.
4. **All planning documents live in `plans/`** — do not scatter plan fragments elsewhere; PROGRESS.md tracks status only.
5. **bugfix.json rules are law** for the files they name; every bug you fix adds a ledger entry.
6. Secrets via `${ENV_VAR}` only; keys masked (last-4) everywhere; never log key values.

---

## 4. Execution Protocol (every phase, every plan)

```
for phase in next_incomplete_phase(PROGRESS.md tracker):
    1. READ     the phase section in its plans/*.md file + the plan.md sections in its
                vision-trace column + bugfix.json rules for files you'll touch
                (+ references/*.json mapped pattern if the phase names one)
    2. LADDER   for each sub-task: climb the ponytail ladder BEFORE writing code;
                record which rung you stopped at (one line in the commit body)
    3. EXECUTE  [S] sub-tasks in listed order; [P] sub-tasks may run concurrently
                in the same sub-phase (disjoint files only)
    4. TAG      every deliberate simplification: `ponytail: <ceiling>, <upgrade path>`
    5. TEST     pytest (+ BF-007 checklist for any ui/ or index.html change) — green or FIX LOOP (max 3)
    6. REVIEW   `ponytail-review` the phase diff; resolve or consciously tag findings
    7. SYNC     `ponytail-debt` at phases marked SYNC; skills-dictionary usage log for any skill used
    8. RECORD   PROGRESS.md entry in i-have-adhd format:
                "<Plan> phase <X> of 5 done — <visible win, concrete numbers>. Next: <one action>."
                Update the tracker table (status, tasks done, net-LOC delta, tests).
    9. COMMIT   one commit per sub-task where practical: "feat(E2.2.1): rewire chat route to shared core"
                / "refactor(E2): delete duplicate mini-loop (−N lines)"
```

**Gates:** a phase is `DONE` only when its gate sub-phase (x.3/x.4 "Gate") passes — TEST green, REVIEW clean, RECORD committed. Never mark `DONE` at "code complete".

**Cross-plan sequencing** (from `plans/README.md`):

```
E1 ──► E2 ──► A2 ──► A3 ──┐
U1 (parallel, read-only)  ├──► E3 ──► U2 ──► U3 ──► E4/E5 · A4/A5 · U4 ──► U5
A1 (parallel, independent)┘
```

SYNC points: after E2.3 (core API frozen — A2 builds on it), after E3.3 (SSE contract frozen — U3.3 consumes it), after A3.2 (citation metadata contract frozen — U2.3/U3.1 consume it). A frozen contract changes only through a REVIEW gate + doc update.

**Failure policy:** FIX LOOP max 3 iterations per failing gate; still red ⇒ mark the phase `BLOCKED` in PROGRESS.md with a matter-of-fact diagnosis (adhd rule 7), continue with independent phases (A1, U1, E4…), otherwise stop and report with ONE concrete next action for the user.

---

## 5. Guardrails (every task, every plan)

- **Understand before cutting** — read the flow end-to-end first; a small diff you don't understand is a second bug (ponytail).
- Python 3.10+ (per pyproject), async-first (`httpx`, `asyncio`), full type hints, `pytest`, `ruff`.
- BF-008: never `asyncio.run` directly inside a FastAPI route — worker thread pattern.
- BF-001: `index.html` is Jinja2 — no literal `{{`; `TemplateResponse(request, name)` form only.
- BF-010: configured state survives restarts (`.harness-state.json`); after any server restart verify `curl /api/models` → 200.
- Every external call goes through config-driven endpoint templates — no ad-hoc URLs.
- Every tool result passes input sanitization before entering a prompt (§9); every model-facing output passes the key scrubber.
- New test deps go in `pyproject [project.optional-dependencies].dev` in the same commit (BF-009).

---

## 6. Kickoff Instruction (to the executing agent)

You are the ORCHESTRATOR of the improvement program. Begin now:

1. Activate §1 (ponytail + i-have-adhd modes on for the rest of the program).
2. `cat .agent/PROGRESS.md` → Improvement Program Tracker → first phase not `DONE`.
   Fresh start ⇒ run **E1** and **U1** first (both read-only audits, parallel-safe), and **A1** if bandwidth allows.
3. For each phase: follow §4 exactly — plan file → ladder → execute → tag → TEST → REVIEW → SYNC → RECORD → COMMIT.
4. When a plan completes, run its sign-off sub-phase, then post the adhd-style program summary (capabilities closed, net-LOC, audit deltas, debt ledger state).
5. When E1–E5, A1–A5, U1–U5 are all `DONE`: run the Program Definition of Done (§3) as final acceptance and report results with one concrete next action for the user.
