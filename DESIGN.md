---
name: LLM Research Harness — Console
description: Night-observatory instrument console — warm ink and amber signals over a deep blue-black sky.
colors:
  night-sky: "oklch(0.17 0.021 256)"
  panel: "oklch(0.205 0.024 256)"
  panel-raised: "oklch(0.245 0.026 256)"
  well: "oklch(0.15 0.019 258)"
  warm-ink: "oklch(0.93 0.012 235)"
  warm-ink-soft: "oklch(0.72 0.022 240)"
  warm-ink-faint: "oklch(0.68 0.024 242)"
  line: "oklch(0.315 0.032 252)"
  line-soft: "oklch(0.275 0.028 252)"
  amber-signal: "oklch(0.80 0.14 75)"
  amber-signal-soft: "oklch(0.80 0.14 75 / 0.10)"
  amber-signal-ring: "oklch(0.80 0.14 75 / 0.28)"
  blue-signal: "oklch(0.70 0.13 235)"
  blue-signal-soft: "oklch(0.70 0.13 235 / 0.06)"
  blue-signal-ring: "oklch(0.70 0.13 235 / 0.40)"
  signal-green: "oklch(0.76 0.14 160)"
  signal-green-soft: "oklch(0.76 0.14 160 / 0.12)"
  signal-yellow: "oklch(0.82 0.14 85)"
  signal-red: "oklch(0.70 0.19 25)"
  signal-red-soft: "oklch(0.70 0.19 25 / 0.12)"
typography:
  display:
    fontFamily: "Fraunces, Georgia, 'Times New Roman', serif"
    fontSize: "27px"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Fraunces, Georgia, 'Times New Roman', serif"
    fontSize: "17px"
    fontWeight: 600
    lineHeight: 1.3
  title:
    fontFamily: "Fraunces, Georgia, 'Times New Roman', serif"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: 1.3
  body:
    fontFamily: "'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "'IBM Plex Mono', 'SFMono-Regular', Consolas, monospace"
    fontSize: "10.5px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.14em"
rounded:
  sm: "3px"
  md: "4px"
  dot: "50%"
spacing:
  xs: "8px"
  sm: "12px"
  md: "18px"
  lg: "22px"
  xl: "34px"
components:
  button-primary:
    backgroundColor: "{colors.amber-signal}"
    textColor: "oklch(0.18 0.03 70)"
    rounded: "{rounded.sm}"
    padding: "9px 18px"
  button-primary-hover:
    backgroundColor: "oklch(0.84 0.14 78)"
    textColor: "oklch(0.18 0.03 70)"
    rounded: "{rounded.sm}"
    padding: "9px 18px"
  button-secondary:
    backgroundColor: "{colors.panel-raised}"
    textColor: "{colors.warm-ink-soft}"
    rounded: "{rounded.sm}"
    padding: "9px 18px"
  button-danger:
    backgroundColor: "{colors.signal-red-soft}"
    textColor: "{colors.signal-red}"
    rounded: "{rounded.sm}"
    padding: "9px 18px"
  input-field:
    backgroundColor: "{colors.well}"
    textColor: "{colors.warm-ink}"
    rounded: "{rounded.sm}"
    padding: "9px 12px"
  card:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.warm-ink}"
    rounded: "{rounded.md}"
    padding: "22px"
  badge-status:
    backgroundColor: "{colors.signal-green-soft}"
    textColor: "{colors.signal-green}"
    rounded: "{rounded.sm}"
    padding: "3px 9px"
  nav-item:
    backgroundColor: "transparent"
    textColor: "{colors.warm-ink-soft}"
    rounded: "{rounded.sm}"
    padding: "8.5px 10px"
  nav-item-active:
    backgroundColor: "{colors.blue-signal-soft}"
    textColor: "{colors.warm-ink}"
    rounded: "{rounded.sm}"
    padding: "8.5px 10px"
  led-online:
    backgroundColor: "{colors.signal-green}"
    size: "7px"
  led-offline:
    backgroundColor: "{colors.signal-red}"
    size: "7px"
---

# Design System: LLM Research Harness — Console

## Overview

**Creative North Star: "The Night Observatory"**

The console is a research instrument observed at night: a deep blue-black sky
(`oklch(0.17 0.021 256)`) with warm-ink readouts and amber signal lights, not a
template landing page. Density and scanability outrank expression — the visitor
is completing a task (Operate mode), and brand identity lives in precise
details: a numbered information architecture (`01 · Session`, `STEP 1`),
mono-spaced data readouts, and small LED status lights that pulse like
instrument hardware.

Motion is restrained and mechanical: short (90–260 ms) eased transitions for
state changes, a single hard 2 px depth shadow under tactile buttons, and one
permitted ambient flourish — the starfield and occasional meteor in the sidebar
rail, which is the only living element on screen and is disabled entirely under
`prefers-reduced-motion`.

**Key Characteristics:**

- Warm ink on deep blue-black — never pure black or pure white
- Two signal colors with strict jobs: amber = action, blue = information
- Mono type for anything that reads like data; serif (Fraunces) only for headings humans read first
- Numbered IA: `01`–`07` view eyebrows, `STEP 1/2/3` provider sequence
- Tonal depth (recessed wells → raised panels), flat by default, no ambient drop shadows
- 3 px corners, 1 px hairline borders, 2 px accent edges marking assistant output
- LED status lights (7 px, glowing, pulsing) for machine state

## Colors

A quiet blue-black palette with one warm accent, two signal hues, and a
three-color status set — every color is a machine or action, never decoration.

### Primary

- **Amber Signal** (`oklch(0.80 0.14 75)`): the one warm accent. Primary
  buttons, the brand monogram border, inline `code`, citation numbers, the
  `::marker` dots, blockquote edges, and the `Send →` action. Its soft (10 %)
  and ring (28 %) alpha variants carry user-message bubble tint and amber focus.

### Secondary

- **Blue Signal** (`oklch(0.70 0.13 235)`): the cool counterpart. Links in
  rendered answers, active nav state and its left bar, assistant-bubble left
  edge, selected model cards, tab underline, text selection background, and
  typing dots. Its 40 %-alpha ring is the decorative ring/glow/border role
  (`--blue-ring` — 2.16–2.19:1, never the sole state indicator); the input
  focus ring uses the 60 %-alpha strong ring (`--blue-ring-strong`,
  3.46:1 on the Well input host — the 3:1 non-text floor, verified
  colour-science 0.4.7 in U5.1.1, which also corrected the U4-era "3.35:1"
  measurement made on a buggy luminance model).

### Tertiary

- **Signal Green** (`oklch(0.76 0.14 160)`): success — online LEDs, `ok`/`ready`/`set` badges, ✓ states.
- **Signal Yellow** (`oklch(0.82 0.14 85)`): warning — `warn` badges, "key needed", "on connect" states.
- **Signal Red** (`oklch(0.70 0.19 25)`): error — offline LED, `err`/`fail` badges, destructive buttons, delete hovers.

### Neutral

- **Night Sky** (`oklch(0.17 0.021 256)`): app background; the main pane layers faint radial glows and a 26 px dot grid over it.
- **Panel** (`oklch(0.205 0.024 256)`): card and container surfaces (cards layer a subtle top-down gradient over it).
- **Panel Raised** (`oklch(0.245 0.026 256)`): one step up — secondary buttons, table-row hover, dim badges.
- **Well** (`oklch(0.15 0.019 258)`): recessed surfaces — inputs, code blocks, assistant bubbles, model cards. Darker than the background: wells sink, panels rise.
- **Warm Ink** (`oklch(0.93 0.012 235)`): primary text — slightly cool, never white.
- **Warm Ink Soft** (`oklch(0.72 0.022 240)`): secondary text, nav links, readouts, snippets — and the text-inspection popover's leading label (the `INSPECT` eyebrow), the one label register that sits a step lighter than Faint because it heads the only floating surface; 6.51:1 on Panel Raised (verified U5.1.1, resolving the U2.1 note that this choice was pending H-M1).
- **Warm Ink Faint** (`oklch(0.68 0.024 242)`): labels, timestamps, hints, icons at rest. Raised from 0.55 in U4.2.2 (H-M1) to clear WCAG AA 4.5:1 on every surface it sits on — weakest is Panel at **6.22:1** (U5.1.1: verified against the colour-science 0.4.7 reference; the in-session oklch models undercounted this pair by ~25–35 % at the WCAG-luminance step, so the U1.2/U4 ratios were recomputed against the reference there).
- **Line** (`oklch(0.315 0.032 252)`): strong borders (inputs, buttons, tables, scrollbars).
- **Line Soft** (`oklch(0.275 0.028 252)`): quiet borders (cards, rows, page-header rule).

### Named Rules

**The Two Signal Colors Rule.** Amber means *act* and blue means *read*. They
never swap jobs, and each appears on ≤10 % of any panel — their rarity is the
point. Status colors (green/yellow/red) describe machine state only.

**The Instrument Dark Rule.** No pure black, no pure white. Darkest surface is
Well (`oklch(0.15 0.019 258)`); lightest text is Warm Ink
(`oklch(0.93 0.012 235)`). Everything sits between, in the blue-black family.

## Typography

**Display Font:** Fraunces (variable optical size 9–144; weights 500–700), with Georgia, Times New Roman fallbacks
**Body Font:** IBM Plex Sans (400/500/600), with system-ui fallbacks
**Label/Mono Font:** IBM Plex Mono (400/500/600), with SFMono-Regular, Consolas fallbacks

**Character:** A serif/mono duet with a workhorse sans in between — Fraunces
gives the console a human, editorial face; IBM Plex Mono gives it the feel of a
lab instrument; Plex Sans is the neutral bridge for everything in between.
Loaded from Google Fonts with `display=swap`.

### Hierarchy

- **Display** (600, 27 px, 1.15, -0.01em tracking): page titles only — the `h2` under each numbered eyebrow.
- **Headline** (600, 17 px, 1.3): card titles (`.card-header h3`).
- **Title** (600, 15–15.5 px, 1.3): sub-card and list headers — chat header, MCP server cards, preset cards, empty-state headings.
- **Body** (400/500, 14 px, 1.55): base text. Dense zones step down to 13.5 px (nav, message bubbles) and 12–13 px (hints, snippets). Answer text wraps at the bubble's width (≤86 % of the pane).
- **Label** (600, 9.5–11 px, uppercase, 0.12–0.18em tracking): eyebrows, section labels, field labels, buttons, badges, table headers, step numbers, timestamps — all mono, all uppercase, all letter-spaced.

### Named Rules

**The Mono Speaks Data Rule.** IBM Plex Mono is used for anything the machine
says — readouts, labels, buttons, badges, table headers, times, model IDs, key
names, URLs in config views. It never carries prose.

**The Fraunces Is Human Rule.** The serif appears only on headings a human
reads first (page, card, bubble headings, empty-state titles). Never on body
text, never on controls.

## Layout

Two-pane instrument shell: a fixed 248 px sidebar (collapsible to a 66 px icon
rail, preference persisted in `localStorage`) plus a main pane whose content is
a single-column stack capped at 1060 px with 34 px top / 40 px side / 60 px
bottom padding. The sidebar holds brand, numbered nav (grouped `Console` /
`Instrumentation`), the sessions history list, and a footer LED + status
readout. Views swap in place (one `.view` active at a time); within a view,
cards stack with 18 px rhythm and 22 px internal padding.

Grids appear only where the content is tabular or card-farm: model cards
`repeat(auto-fill, minmax(230px, 1fr))` at 10 px gap; MCP presets
`minmax(300px, 1fr)` at 12 px gap.

**Responsive:** at ≤820 px the sidebar collapses to the icon rail, main padding
drops to 20 px/16 px, grids become single-column, and chat messages widen to
96 %. `prefers-reduced-motion` removes the starfield, meteor, and all
entering animations.

Spacing rhythm in use: 8 / 12 / 18 / 22 / 34 px.

## Elevation & Depth

Flat, tonal, and bordered — depth is almost never a drop shadow. Surfaces are
ordered by lightness: Well (recessed, darker than the background) < Night Sky <
Panel < Panel Raised (raised). A 1 px hairline border (`Line` / `Line Soft`)
defines every edge. The main pane's faint radial glows and 26 px dot grid add
atmosphere without elevation.

### Shadow Vocabulary

- **Tactile depth** (`box-shadow: 0 2px 0 oklch(0.62 0.15 60 / 0.9)` on amber; `0 2px 0 oklch(0.17 0.02 256)` on secondary): hard 2 px edge under buttons — a physical switch, not a glow. Collapses to `inset 0 2px 5px` on `:active`.
- **Float** (`box-shadow: 0 10px 30px oklch(0 0 0 / 0.45)`): the only true drop shadow — reserved for floating surfaces: toasts and the text-inspection popover.
- **LED glow** (`box-shadow: 0 0 8px` of the LED color): instrument-light bloom, state-driven (green = online, red = offline), pulsing at 2.4 s.

### Named Rules

**The Flat-By-Default Rule.** Cards, rows, and wells are flat at rest. No
ambient drop shadow on containers, ever — if a surface needs to read as raised,
it steps to Panel Raised lightness plus a border, not a shadow.

## Shapes

Small, squared, instrument-grade corners: 3 px (`rounded.sm`) for everything
interactive and small (buttons, inputs, badges, nav items, model cards, code
spans, toasts) and 4 px (`rounded.md`) for large containers (cards, chat
container, message bubbles, MCP/preset cards). Circles are reserved for
machine parts: LED status lights, stars, typing dots, and the spinner.

Borders do the structural work: 1 px `Line` (strong) or `Line Soft` (quiet)
everywhere; a **2 px left edge** in the signal color marks assistant content
(assistant bubble, typing indicator) and 3 px on toasts; a **dashed 1 px
border** marks optional or advanced content (empty-state icon box, `ADVANCED`
details panel). No outlines beyond focus rings, no clipping, no diagonal
geometry.

### Named Rules

**The 3px Rule.** Corners stay at 3 px (small) or 4 px (large containers). A
new shape with a 6 px+ radius is a different product.

**The Dashed-Optional Rule.** If something is optional, collapsible, or empty,
its border is dashed — the console's visual idiom for "not required".

## Components

### Buttons

- **Character:** tactile mono switches — they press, they don't just highlight.
- **Shape:** 3 px radius (sm: 5 px 12 px padding, 11 px type).
- **Type:** IBM Plex Mono 12 px / 600, 0.04em tracking — buttons read like hardware labels.
- **Primary:** Amber Signal background, dark text (`oklch(0.18 0.03 70)`), hard 2 px amber depth shadow.
- **Secondary:** Panel Raised background, Warm Ink Soft text, 1 px Line border, hard 2 px dark shadow.
- **Danger:** Signal Red Soft background, Signal Red text, 35 %-alpha red border.
- **Hover / Focus / Active:** hover shifts the fill (amber → `oklch(0.84 0.14 78)`; secondary border → Warm Ink Faint); `:focus-visible` = instant 2 px Blue Signal outline (offset 2 px, no transition); `:active` translates down 1.5 px, scales 0.98, and inverts the shadow to inset; disabled = 50 % opacity, no transform.

### Inputs / Fields

- **Style:** Well background, 1 px Line border, 3 px radius, 9 px 12 px padding, 13.5 px Plex Sans; selects use an inline SVG chevron and `appearance:none`.
- **Labels:** mono, 10.5 px, uppercase, 0.12em tracking, Warm Ink Faint, above the field.
- **Focus:** border → Blue Signal + 3 px Blue Signal strong ring (`--blue-ring-strong`, 60 % alpha — 3.46:1 on the Well host; U5.1.1) — instant, deliberately kept off the transition. Outline removed in favor of the ring. `:hover` → border Warm Ink Faint; `:disabled` → 55 % opacity, `not-allowed`.
- **Placeholder:** Warm Ink Faint.

### Navigation (sidebar)

- **Style:** 13.5 px Plex Sans 500 links, 8.5 px 10 px padding, 3 px radius, grouped under mono uppercase labels (`Console`, `Instrumentation`).
- **States:** hover/active = Blue Signal Soft background, text → Warm Ink, icon opacity 0.75 → 1 (active icon → Blue Signal).
- **Active marker:** a 2.5 px Blue Signal bar at the rail edge with an 8 px glow — the "you are here" light.
- **Collapsed:** 66 px icon rail; bar and labels hidden, monogram centered.

### Badges & Readouts

- **Badge:** mono 10.5 px / 600 uppercase, 0.06em tracking, 3 px 9 px padding, 3 px radius, 1 px tinted border. Variants map 1:1 to the color roles: `ok` (green), `warn` (yellow), `err` (red), `dim` (Panel Raised), `accent` (amber), `blue` (blue) — soft 6–12 % fill with the full-strength text (blue softened to 6 % in U4.2.2 for badge-text contrast).
- **Readout:** plain mono 12 px, Warm Ink Soft — the console's default voice for values (latency, counts, status).

### Cards / Containers

- **Corner Style:** 4 px.
- **Background:** Panel with a subtle 180° gradient toward darker; 1 px Line Soft border.
- **Shadow Strategy:** none (see Flat-By-Default).
- **Internal Padding:** 22 px; 18 px between cards.
- **Header:** Fraunces 17 px title, optionally prefixed by an amber mono `STEP n`; right side carries badges or actions.

### LED Status Lights (signature)

- **Shape:** 7 px dot, `border-radius:50%`, 8 px self-glow in its color.
- **States:** green + 2.4 s pulse = online/ok; red, static = offline/off.
- **Placement:** sidebar footer (server), connection panel (endpoint test), any place a machine state must be glanceable. The LED plus a mono readout is the console's standard "status" pattern.

### Table

- **Header:** mono 10 px / 600 uppercase, 0.14em tracking, Warm Ink Faint.
- **Cells:** 10 px 14 px padding, 13 px body, 1 px Line Soft row border; row hover → Panel Raised.
- **In answers:** full 1 px cell borders, mono uppercase headers, zebra rows at 30 % Panel Raised.

### Tabs

- **Style:** flat mono 11.5 px / 500, 0.06em tracking, no border except a 2 px bottom rule; active = Blue Signal text + Blue Signal underline; hover → Warm Ink.

### Model Card (selectable grid item)

- **Style:** Well background, no border at rest (the well/panel tone shift carries the card edge), 3 px radius, 13 px 15 px padding.
- **States:** hover → Blue Signal Ring border + translateY(-1 px); selected → Blue Signal border + Blue Signal Soft fill; press → scale 0.99.
- **Content:** Plex Sans 600 name over a mono 10.5 px ID (wrap anywhere).

### Toast

- **Style:** Panel background, 1 px Line border with a 3 px colored left edge (green/red/blue by type), 3 px radius, mono 12 px, max-width 400 px, fixed top-right.
- **Motion:** slides in from the right over 240 ms with the one permitted drop shadow; auto-dismisses ~3.2 s.

### Citation-Numbered Search Results (signature)

- **Style:** list of result rows with a CSS-counter `[n]` in mono Blue Signal at the left; Well-dark row background, 1 px Line Soft border, 3 px radius.
- **Content:** title link (Plex Sans 600, → Blue Signal on hover) over a 12 px Warm Ink Soft snippet (≤220 chars). Hover → Blue Signal Ring border. This is the research console's signature "evidence" pattern.

### Empty State

- **Style:** 44 px dashed-border icon box (icon in Blue Signal), Fraunces 15 px title, 12.5 px Warm Ink Faint copy capped at 40 ch, centered.

### Monogram (brand)

- **Style:** 34 px square, 3 px radius, 1.5 px Amber Signal border, Amber Signal Soft fill, mono 13 px / 600 "RH" — the console's only brand mark.

## Do's and Don'ts

### Do:

- **Do** use Warm Ink on Night Sky for body text, and Warm Ink Soft/Faint strictly for secondary and label tiers.
- **Do** keep every label mono, uppercase, letter-spaced (0.12–0.18em) — the console's data voice.
- **Do** number views (`01 · Session` … `07 · State`) and multi-step flows (`STEP 1/2/3`) with the mono eyebrow pattern.
- **Do** convey machine state with an LED (green pulse / red) plus a mono readout, not with prose alone.
- **Do** mark assistant-generated content with the 2 px Blue Signal left edge; user content with the amber tint.
- **Do** use `animation-fill-mode: both` on every element whose visibility comes from an entering keyframe (BF-006 — the "response vanished" bug).
- **Do** honor `prefers-reduced-motion`: stars, meteors, and enter animations all switch off.

### Don't:

- **Don't** use pure `#000` or `#fff` anywhere — the Instrument Dark Rule owns the full range.
- **Don't** let amber and blue cross jobs (amber = act, blue = read), and don't use status colors for emphasis.
- **Don't** put a drop shadow on a card or container — depth is tonal; shadows belong to buttons (2 px hard), toasts, and LED glow only.
- **Don't** round anything past 4 px, and don't put Fraunces on body text or controls.
- **Don't** add new ambient animation — the sidebar sky is the single living element; everything else transitions 90–260 ms on `cubic-bezier(0.33, 1, 0.68, 1)`.
- **Don't** write literal `{{` in `index.html` (it is a Jinja2 template — BF-001), and never log or display unmasked keys (keys render as `••••last4` mono readouts).
