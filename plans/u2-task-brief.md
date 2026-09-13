# U2 Task Brief — Reactive Text Inspection (capability #4)

**Status:** U2.1 complete (2026-09-13) — pattern note + shape brief, per `plans/ui-improvement-plan.md` Phase U2.
**Consumers:** U2.2 (native implementation), U2.3 (pipeline wiring), U2.4 (polish & gate).
**Sources studied:** `references/architectural_references.json` → `selection_anchor_engine` (Floating UI: "virtual coordinate positioning via `window.getSelection()` and collision-aware tooltip boundary management") · `interactive_text_document` (Tiptap: "ProseMirror-based interactive node views, BubbleMenu for selection triggers, and rich citation metadata nodes"). **Patterns adopted, packages not** (hard constraint #3, ponytail rung 4).
**Design authority:** `DESIGN.md` (frozen by U1.1) — every decision below is token-mapped.
**Efficiency ladder rung:** 2 (reuse — `renderMarkdown`, `escapeHtml`, `api()`, `.search-result-item`, `.spinner-sm` already exist) + 4 (native — `window.getSelection()` + one fixed-positioned div).

---

## 1. Pattern note — selection → anchored popover (U2.1.1, ≤20 lines)

```
TRIGGER  (Tiptap BubbleMenu pattern, native)
 1. Listen for mouseup + keyup on document (after the gesture ends, not mid-drag).
 2. sel = window.getSelection(); valid iff trimmed text >= 3 chars AND anchor + focus
    resolve to the SAME .message.assistant .msg-bubble (else no-op).
 3. New valid selection while open -> re-anchor in place; selection leaving the bubble -> close.
ANCHOR   (Floating UI "virtual element")
 4. Range.getBoundingClientRect() is the anchor rect. Position against the rect, never
    wrap the text (zero layout shift).
PLACEMENT
 5. Default below (rect.bottom + 8px); flip above (rect.top - h - 8px) when below overflows
    the viewport bottom.
 6. Render hidden -> measure (offsetWidth/offsetHeight) -> place -> show. position: fixed;
    re-run on scroll + resize while open (Floating UI fixed-strategy update loop).
COLLISION
 7. Flip once; if both overflow (tiny viewport), clamp and shrink max-height. Horizontal:
    shift so edges stay >= 8px inside the viewport.
 8. Size: width min(420px, vw - 16px); max-height min(320px, 60vh); body scrolls, header pinned.
 9. Dismiss: ESC, outside mousedown, chat clear / new session, view switch.
```

## 2. Shape brief (U2.1.2 — `/impeccable shape`, state list + placement rules)

### Job and audience
- **Who arrives:** the operator, mid-reading — they just consumed an assistant answer and want to drill into one phrase without losing their place. Visitor mode: **Operate** (DESIGN.md), not Read.
- **Need:** "What does *this* mean in the context of *that* answer?" — two depths: a fast **Define** (anchored definition, single-hop) and a deeper **Break down** (contextual analysis through the research pipeline, U2.3.1).
- **Product-specific truth:** this is a research instrument — the popover is an inspector's loupe, not a tooltip. It quotes the exact selected phrase and answers with citations.

### Outcome and proof
- Primary action: select a phrase in an assistant response → popover appears anchored to it → **Define** or **Break down** → cited answer renders inside the popover with the message list untouched (no scroll jump, no reflow — acceptance U2.2.2).
- Proof: manual + renderer checks per U2.2.1 acceptance: trigger fires in assistant bubbles only; never in user bubbles or the chat input.

### Selected direction (structural / interaction thesis)
- **One floating surface, assistant's voice.** The popover is the console's second floating surface (after toasts). It borrows the assistant bubble's identity: `--well` is the assistant *bubble* surface; the popover is a *raised* surface → `--panel` background, 1px `--line` border, 3px radius (**The 3px Rule**), the toast's shadow (the named "one floating surface" rule extends to floating surfaces generally — DESIGN.md delta logged for U5.2.2), and a 2px `--accent-2` left edge (the documented assistant-content marker).
- **Mono speaks the machine's part:** eyebrow label `INSPECT` (mono 10.5px, uppercase, 0.14em, `--ink-2` — one step brighter than `--ink-3` pending the U1.2 contrast fix H-M1; builder uses the fixed token), the quoted phrase in mono 12px `--ink` (truncated at ~80 chars + ellipsis), `msg-meta`-style footer readout (source count, model) in `--ink-3`.
- **Two actions, one primary.** **Define** = primary (`--accent` fill — the cheap, fast, default choice; **The Two Signal Colors Rule**: amber = act). **Break down** = secondary (`--panel-2` fill). Both `btn-sm` (5px 12px padding, 11px mono) for popover density.

### Scope and boundaries
- **In scope (U2.2):** selection listener, virtual-anchor positioning, flip/shift clamping, popover surface + states, dismiss logic, keyboard reachability (ESC; focus returns to the pre-open focused element — assumption A5).
- **Out of scope (later phases):** Define/Break-down payloads + backend route (U2.3.1 — Define = single-hop chat call, the cheapest path that satisfies the vision; Break down = A2 workflow once A2 lands), error copy + retry behavior (U2.3.2), BF-007 gate + `ponytail-review` (U2.4.2), polish pass (U2.4.1).
- **Anti-goals:** no library (no Floating UI / Tiptap packages), no wrapping/highlight markup around selected text (zero layout shift), no persistent highlights after close, no popover on user messages, no multi-phrase/cross-bubble selections.
- **Untouched:** chat input, sessions list, message list DOM structure, `renderMarkdown` (reused as-is — BF-007 renderer battery stays green).

### States and ranges (acceptance: idle → selection → popover → loading → answer → cite)

| # | State | Trigger / exit | Surface content | Tokens |
|---|-------|----------------|-----------------|--------|
| S0 | **idle** | default | nothing rendered | — |
| S1 | **selection (valid)** | valid selection in assistant bubble | popover opens (180ms enter, `--ease`, fill-mode `both` — BF-006; reduced-motion: none) | see S2 |
| S1' | selection (invalid) | user bubble / input / <3 chars / cross-bubble | no popover; existing `::selection` (`--blue-ring`) stays the only feedback | `::selection` |
| S2 | **popover** | S1 | header: `INSPECT` eyebrow + quoted phrase + ✕ (btn-sm ghost, `--err` on hover); action row: **Define** (primary) + **Break down** (secondary) | `--panel`, `--line`, `--accent`, `--panel-2` |
| S3 | **loading** | action fired | actions replaced by spinner (`.spinner-sm` reused) + mono readout — Define: `working…` · Break down: `researching…` (matter-of-fact, adhd rule 8; final copy U2.3.2) | `--accent-2` spinner, `--ink-2` readout |
| S4 | **answer** | response rendered | `renderMarkdown()` output, 13px body (`--ink` on `--panel`), inline `[n]` in mono `--accent-2` (citation-numbered voice); scrollable body (max-height per pattern note §8) | `--accent-2` cites |
| S5 | **cite** | with S4 (sources present) | 1–5 source rows reusing `.search-result-item` (CSS-counter `[n]`, hover `--blue-ring` border) | as documented |
| S6 | **error** | request fails (U2.3.2 owns copy/retry) | mono `--err` one-liner (cause, not apology) + **Retry** (btn-sm secondary); popover stays, console stays usable | `--err` |

**Ranges:** selection 3–~300 chars (display truncated ~80) · Define answer ~1–3 sentences + ≤2 sources · Break-down answer paragraphs + ≤5 sources · popover 340–420px wide, ≤320px tall (body scrolls).

### Interaction and layout
- **Hierarchy:** phrase (what) → actions (do) → answer (result) → sources (proof). One decision per state.
- **Topology:** single popover instance, created lazily on first open, appended to `<body>`, `position: fixed`, `z-index: 900` (below toasts at 1000 so error toasts still win).
- **Feedback:** every state change answers the user's action (frontend-design: "motion that answers a person's action is welcome") — enter 180ms, state swap 120ms crossfade, dismiss 120ms fade; all on `--ease`, all fill-mode `both`, all disabled under `prefers-reduced-motion`.
- **Responsiveness:** pattern note §8 already clamps to viewport at any width; at ≤820px (narrow breakpoint) the popover goes full-width-minus-16px and docks near the selection without horizontal shift (U4.2.1 re-verifies).
- **Keyboard:** ESC dismisses at every state; focus is saved on open and restored on close (A5); actions are real `<button>`s (tab-reachable while open) with the U1.2-mandated instant `:focus-visible` ring (`--accent-2` 2px, no transition — H-M3 convention, which does not exist yet: builder implements the popover's focus ring per the H-M3 fix and reuses the same recipe).

### Constraints and open decisions
- **Binding:** BF-001 (Jinja2 — no literal `{{` in `index.html`), BF-006 (fill-mode), BF-007 (pytest + curl + renderer battery before done), BF-008 (U2.3 backend route: worker-thread pattern), BF-010 (no new state that must survive restarts beyond existing session persistence); no new runtime dependencies; total feature budget "well under 200 lines" (U2.4.2).
- **Assumptions (marked, per shape protocol — correct any in one line):**
  - **A1:** Define is the primary (amber) action — it is the cheap path; Break down is secondary.
  - **A2:** popover shares the toast drop-shadow; the "one floating surface" named rule is generalized to *floating surfaces* (DESIGN.md delta at U5.2.2).
  - **A3:** minimum selection = 3 trimmed chars (single letters and stray spaces don't trigger).
  - **A4:** popover tracks scroll/resize (reposition) rather than closing on scroll.
  - **A5:** focus returns to the element focused before open (usually the chat input).
- **Open (builder must NOT invent — owned by later tasks):** Define/Break-down request payloads and endpoint (U2.3.1) · error copy + single-retry behavior (U2.3.2) · whether Break down streams via SSE once E3 lands (U3.3 integration).

---

## 3. Verification (U2.1 acceptance)

- Pattern note ≤20 lines ✓ (9 numbered rules across TRIGGER / ANCHOR / PLACEMENT / COLLISION) — committed with the implementation PR (this branch → PR #1).
- State list + placement rules reviewed against DESIGN.md tokens ✓ (every state row token-mapped; two DESIGN.md deltas logged: floating-surface shadow rule, `--ink-2` eyebrow pending H-M1).
- No UI edits in U2.1 (design only) ✓ — implementation starts U2.2.
