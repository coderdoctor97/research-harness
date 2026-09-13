# UI Improvement Plan

**Domain:** interface refinement and enhancement of the web console and chat surface
**Hard constraint:** every sub-task executes **strictly through the existing UI skills** — `frontend-design` (baseline taste, auto-invoked), `hallmark` (anti-slop build/audit/redesign), `impeccable` (23-command design lifecycle + its 4 subagents) — as installed in `.claude/skills/` and catalogued in `skills-dictionary/SKILLS_DICTIONARY.md`. No UI change lands without a skill driving it and a skill verifying it.
**Vision baseline:** `plan.md` §5 (Example Output — citation anchors, Sources section) · §7-P9 (console acceptance criteria) · §9 (localhost bind, masked keys) — plus product-identity **capability #4: reactive text inspection** (highlight any phrase → anchored definition / deeper contextual breakdown), which is declared in the vision and **not yet implemented**.
**Depends on:** U1 is independent (read-only). U2.3 needs A2/A3 (research workflow + citation metadata contract). U3.3 needs E3.2.2 (SSE endpoint). **Blocks:** nothing outside itself.
**Architectural references (patterns only — native implementation, zero new dependencies):** Floating UI (selection-anchored viewport positioning, collision-aware boundaries) · Tiptap (selection listeners / bubble-menu trigger pattern) — per `references/architectural_references.json`. Ponytail rung 4: `window.getSelection()` + CSS is the platform-native form of both patterns.
**Efficiency doctrine:** ponytail ladder on every implementation task (native before library, one line before fifty); `ponytail:` tags on deliberate simplifications; `ponytail-review` at gates; adhd-format reports.
**Guardrail:** `bugfix.json` UI rules are law — BF-001 (Jinja2 `{{` / TemplateResponse form), BF-006 (animation fill-mode), BF-007 (verify before done: pytest + curl + renderer checks), BF-008 (async-in-routes), BF-010 (state survives restart).

## Baseline findings this plan closes

| # | Finding (2026-09-13 review) | Phase |
|---|---|---|
| F6 | Capability #4 (reactive text inspection) unimplemented — no selection/popover/anchored-breakdown code exists | U2 |
| F7 | UI skills applied once (2026-09-12 redesign); no DESIGN.md, no scored audit baseline, no re-score loop | U1, U5 |
| — | Chat renders answers, but citation anchors/Sources/tool-trace rendering does not yet exploit the A3 metadata contract; streaming render pending E3 | U3 |
| — | `index.html` is a single 1663-line template; punch-list debt unknown until U1 scores it | U4 |

---

## Phase U1 — Skill-Driven Baseline & Audit *(read-only; ~2–3 h)*

> Entry: none. Exit: DESIGN.md exists, both audits scored, punch list prioritized and frozen. **No edits in this phase** — skills evaluate, humans/agents decide.

### Sub-phase U1.1 — Document the current design language (~1 h)

| ID | Sub-task | Skill (mandatory) | Mode | Acceptance | Vision trace |
|---|---|---|---|---|---|
| U1.1.1 | Capture the current console's design system → `DESIGN.md` (theme tokens: warm-ink + amber instrument palette, Fraunces/IBM Plex pairing, numbered nav IA, LED status lights, mono readouts) | `/impeccable document` | `[S]` | `DESIGN.md` committed; tokens match `index.html` CSS variables | §7-P9 console identity; skills-dictionary routing table |
| U1.1.2 | Log the documentation pass in `skills-dictionary` usage log | — | `[S]` | Usage-log row added | Dictionary protocol |

### Sub-phase U1.2 — Dual scored audit (~1–1.5 h)

| ID | Sub-task | Skill (mandatory) | Mode | Acceptance | Vision trace |
|---|---|---|---|---|---|
| U1.2.1 | Anti-slop audit of the console: score against the 57 slop-test gates; punch list, no edits | `hallmark audit src/harness/ui/templates/index.html` | `[S]` | Scored report + punch list appended to PROGRESS.md | Product identity — a research instrument, not a template |
| U1.2.2 | Design-fluency critique: IA, hierarchy, micro-details across all panels (Chat, AI Provider, Keys, Endpoints, MCP, Logs, Config) | `/impeccable critique` | `[S]` | Findings list with severity; overlaps with U1.2.1 merged | §7-P9 panel set |

### Sub-phase U1.3 — Prioritize & freeze scope (~30 min)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| U1.3.1 | Rank merged punch list: (1) vision-capability blockers (citation rendering, inspection affordances), (2) BF-rule violations, (3) polish | `[S]` | Ranked list frozen in PROGRESS.md; anything outside the three plans' scope explicitly rejected (no new features) | Scope constraint |
| U1.3.2 | Map each punch-list item to its executing phase (U2/U3/U4) so nothing is orphaned | `[S]` | Every item has a home task ID | Efficiency doctrine — deferrals visible |

---

## Phase U2 — Reactive Text Inspection *(capability #4; ~1–2 days)*

> Entry: U1 done; U2.3 needs A2/A3 complete. Exit: selecting any phrase in an assistant response opens an anchored popover offering a definition / deeper breakdown, answered through the research pipeline with citations.
> Pattern study first (references registry rule): Floating UI → collision-aware anchored positioning; Tiptap → selection-triggered bubble menu. Implement natively: `window.getSelection()` + absolutely-positioned popover + viewport clamping in CSS/JS. **No library added** (ponytail rung 4).

### Sub-phase U2.1 — Pattern study & design (~1–2 h)

| ID | Sub-task | Skill (mandatory) | Mode | Acceptance | Vision trace |
|---|---|---|---|---|---|
| U2.1.1 | Study the two mapped references; write a ≤20-line pattern note (trigger → anchor → placement → collision rule) into the task brief — adopt the pattern, not the package | `frontend-design` (baseline) | `[S]` | Note committed with the implementation PR | references registry `selection_anchor_engine` + `interactive_text_document`; agent.md §0 rule |
| U2.1.2 | Shape the component's IA and states (idle → selection → popover → loading → answer → cite) before any code | `/impeccable shape` | `[S]` | State list + placement rules reviewed against DESIGN.md tokens | Capability #4 |

### Sub-phase U2.2 — Native implementation (~0.5 day)

| ID | Sub-task | Skill (mandatory) | Mode | Acceptance | Vision trace |
|---|---|---|---|---|---|
| U2.2.1 | Selection listener on assistant message bubbles: `mouseup`/`keyup` + `getSelection()` → non-empty, single-message selection triggers the popover anchor | `frontend-design` | `[S]` | Manual + renderer test: selecting text in an answer shows the trigger; selecting in user messages/input does not | Capability #4 verbatim — "user selects/highlights any phrase in a response" |
| U2.2.2 | Anchored popover positioned at the selection rect, clamped to viewport (flip/shift on collision — the Floating UI pattern in ~30 lines) | `frontend-design` | `[S]` | Popover fully visible at window edges; no layout shift of the message list | references `selection_anchor_engine` |
| U2.2.3 | Popover actions: **Define** (anchored definition) and **Break down** (deeper contextual analysis); ESC/click-away dismisses; keyboard reachable | `/impeccable shape` output applied | `[S]` | Both actions fire; dismissal works; focus returns to the selection on close | Capability #4 |

### Sub-phase U2.3 — Wire to the research pipeline (~3 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| U2.3.1 | Popover action → backend call carrying (selected phrase, source message context) → A2 workflow (or a single-hop chat call for Define — cheapest path that satisfies the vision; ladder rung 1) | `[S]` | Response renders in popover with inline `[n]` citations from the A3 metadata contract | Capabilities #3+#4 composed |
| U2.3.2 | Loading + error states: matter-of-fact copy (adhd rule 8), retry once, graceful failure keeps the console usable | `[S]` | Mocked failure → popover shows cause + fix, no dead ends | §8 error wording style |
| U2.3.3 | Backend route follows BF-008 (async-in-routes via worker thread) and reuses existing chat state/session persistence | `[S]` | `test_ui.py` extended; BF-010 restart check unaffected | bugfix.json |

### Sub-phase U2.4 — Skill polish & gate (~2 h)

| ID | Sub-task | Skill (mandatory) | Mode | Acceptance | Vision trace |
|---|---|---|---|---|---|
| U2.4.1 | Polish pass on the new component: hierarchy, motion (fill-mode per BF-006), type scale from DESIGN.md | `/impeccable polish` | `[S]` | Polish notes applied; no `opacity:0`-without-fill-mode regressions | BF-006 |
| U2.4.2 | TEST + REVIEW gates: `pytest` + `curl localhost:8080/` + renderer checks (BF-007); `ponytail-review` the diff (target: whole feature in well under 200 lines) | — | `[S]` | BF-007 checklist logged green; net-LOC recorded | BF-007; efficiency doctrine |

---

## Phase U3 — Research Output Rendering *(capabilities #1/#3 made visible; ~0.5–1 day)*

> Entry: A3.2.1 (citation metadata contract) for U3.1/U3.2; E3.2.2 (SSE endpoint) for U3.3. Exit: research answers render as research — clickable citation anchors, Sources section, visible fan-out trace, streamed tokens.

### Sub-phase U3.1 — Citation anchors & sources (~3 h)

| ID | Sub-task | Skill (mandatory) | Mode | Acceptance | Vision trace |
|---|---|---|---|---|---|
| U3.1.1 | Render inline `[n]` as clickable anchors from the A3 metadata map (no markdown re-parsing); hover shows source title; click opens source URL | `frontend-design` | `[S]` | Renderer test: metadata map → anchors; unknown `[n]` renders inert (validator already stripped orphans) | §5 Example Output; capability #3 |
| U3.1.2 | Sources section styling: citation-numbered, deduped, mono readout consistent with the instrument theme | `/impeccable polish` | `[S]` | Matches DESIGN.md tokens; hallmark "no AI-slop list" gate passes | §5; skills-dictionary (citation-numbered search results precedent) |

### Sub-phase U3.2 — Fan-out trace visibility (~2–3 h)

| ID | Sub-task | Skill (mandatory) | Mode | Acceptance | Vision trace |
|---|---|---|---|---|---|
| U3.2.1 | Show the research workflow's stages in the tool-trace panel: decomposed queries → parallel searches (per-query status LEDs) → aggregated sources → synthesis | `/impeccable shape` then implement | `[S]` | Trace renders from existing SSE/log events; LED vocabulary reused from current status lights | Capability #1 made observable; §7-P9 "tool-call trace per answer" |

### Sub-phase U3.3 — Streaming render (~3 h)

| ID | Sub-task | Skill (mandatory) | Mode | Acceptance | Vision trace |
|---|---|---|---|---|---|
| U3.3.1 | Consume the frozen E3 SSE contract (`token/tool_call/tool_result/final`); render incrementally into the message bubble | `frontend-design` | `[S]` | Mocked SSE stream → incremental render; final event reconciles full markdown | §7-P10 T3 UI surface |
| U3.3.2 | XSS-safe incremental markdown: reuse the existing renderer path; run the BF-007 renderer battery (headings/lists/links/code/XSS) on streamed output | — | `[S]` | Renderer battery green on streaming fixtures | BF-007 |

### Sub-phase U3.4 — Gate (~1 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| U3.4.1 | TEST + REVIEW gates (BF-007 full checklist; `ponytail-review`); adhd PROGRESS entry | `[S]` | Green; state restated ("Phase U3 of 5 done — anchors, trace, streaming render live. Next: U4") | Efficiency doctrine |

---

## Phase U4 — Console Polish & Consistency *(punch-list execution; ~0.5–1 day)*

> Entry: U1 punch list frozen. Exit: ranked punch list executed or consciously deferred with `ponytail:` tags; console coherent with DESIGN.md across all panels.

### Sub-phase U4.1 — Punch-list execution (~3–4 h)

| ID | Sub-task | Skill (mandatory) | Mode | Acceptance | Vision trace |
|---|---|---|---|---|---|
| U4.1.1 | Work rank-1 items (vision-capability blockers) via targeted impeccable commands per item (`polish`, `clarify`, `layout`, `typeset`, `colorize` — per the dictionary's routing table) | `/impeccable <cmd>` per item | `[S]` | Each item closed or tagged `ponytail: <ceiling>, <upgrade path>` | U1.3 ranking |
| U4.1.2 | Rank-2: BF-rule violation sweep (BF-001 Jinja braces, BF-006 fill-modes, BF-010 state persistence) | — | `[S]` | Sweep report: zero violations | bugfix.json |
| U4.1.3 | Rank-3: whole-console coherence pass — panel-to-panel spacing/type/color consistency against DESIGN.md | `/impeccable harden` + `frontend-design` | `[S]` | Critique delta from U1.2.2 shows resolved findings | §7-P9 |

### Sub-phase U4.2 — Responsive & accessibility (~2 h)

| ID | Sub-task | Skill (mandatory) | Mode | Acceptance | Vision trace |
|---|---|---|---|---|---|
| U4.2.1 | Adapt pass: narrow-viewport layout for chat + panels; popover (U2) repositioning on resize | `/impeccable adapt` | `[S]` | Manual check at 3 widths; no horizontal scroll in chat | §7-P9 usability |
| U4.2.2 | Keyboard/focus audit: tab order, focus rings (`::selection`/`--blue-ring` tokens), popover focus trap | `/impeccable harden` | `[S]` | All interactive elements keyboard-reachable; audit notes resolved | ponytail "not lazy about accessibility" |

### Sub-phase U4.3 — Gate (~30 min)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| U4.3.1 | TEST gate (BF-007 full) + `ponytail-review`; `ponytail-debt` harvest for all UI `ponytail:` tags | `[S]` | Green; ledger rows all have triggers | Efficiency doctrine |

---

## Phase U5 — Skill Verification & Sign-off *(~2–3 h)*

> Entry: U2–U4 done. Exit: both audit skills re-score the console showing measurable improvement; usage log and PROGRESS updated; capability #4 declared done.

### Sub-phase U5.1 — Re-score (~1–1.5 h)

| ID | Sub-task | Skill (mandatory) | Mode | Acceptance | Vision trace |
|---|---|---|---|---|---|
| U5.1.1 | `hallmark audit` re-run; compare to U1.2.1 score | `hallmark audit` | `[S]` | Score improved; remaining findings are tagged deferrals only | Anti-slop gate |
| U5.1.2 | `/impeccable audit` re-run across panels | `/impeccable audit` | `[S]` | Findings delta vs U1.2.2 recorded | Design-fluency gate |

### Sub-phase U5.2 — Regression & docs (~1 h)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| U5.2.1 | Full BF-007 verification: `pytest` + server restart + `curl localhost:8080/` + `curl /api/models` (BF-010) + renderer battery | — | All green, logged | bugfix.json |
| U5.2.2 | Update `skills-dictionary` usage log (skills used, actions, dates) and `DESIGN.md` deltas | — | Dictionary + DESIGN.md committed | Dictionary protocol |

### Sub-phase U5.3 — Sign-off (~30 min)

| ID | Sub-task | Mode | Acceptance | Vision trace |
|---|---|---|---|---|
| U5.3.1 | Adhd-format sign-off in PROGRESS.md: capability #4 status, punch-list closure rate, net-LOC, audit score deltas, remaining `ponytail:` debt | — | "UI plan done: capability #4 live, audit score X→Y, −N/+M lines, K debt tags (all with triggers). Next: <open item>" | Efficiency doctrine |
