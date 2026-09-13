# 🎨 Skill Dictionary — UI Polishment Pack + Upgrade Roadmap

> Dictionary for this project in two parts: (1) the three frontend design skills
> installed to polish the research-harness UI, and (2) a **future-upgrade roadmap**
> of reference frameworks to study/adopt when extending the harness.
> Machine-readable version: [`skills-dictionary.json`](skills-dictionary.json).

Installed on **2026-09-12** into `.claude/skills/`.

## 🔧 Project integration — Hallmark & impeccable, active in this repo

Both **Hallmark** and **impeccable** are registered here *and* applied to this
project (see `integration` block in the JSON):

- **Hallmark** — ran the anti-slop audit over the web console: rejected the
  purple-gradient / system-stack defaults, forced structural variety (stepped
  provider flow instead of stacked identical cards) and the warm ink + amber
  instrument theme now in `src/harness/ui/templates/index.html`.
- **impeccable** — `shape` + `polish` passes defined the IA (numbered nav,
  step labels, provider → key → test → fetch), hierarchy, and micro-details
  (LED status lights, mono readouts, citation-numbered search results).
- **frontend-design** — baseline taste on every UI change in this repo.

Usage log (newest first):

| Date | Skills | Action |
|------|--------|--------|
| 2026-09-13 | ponytail (ladder + no-new-features) · i-have-adhd | **U1.3** — ranked & froze the U1.2 punch list in PROGRESS.md: rank-1/2 verified empty (BF-001/006/010 re-checked against the template), rank-3 ordered a11y-floor → safety → coherence; 18/18 findings homed to U4 tasks; 4 out-of-scope critique requests rejected per hard constraint #1. **Phase U1 DONE (6/6).** |
| 2026-09-13 | hallmark (audit) · impeccable (critique) · ponytail · i-have-adhd | **U1.2** — dual scored audit of the console (read-only): `hallmark audit` → 0 critical / 6 major / 11 minor across 58 gates (contrast pairs computed: 24 measured, 10 fail — `--ink-3` tier, focus ring, badge cluster); `/impeccable critique` (degraded single-context — no sub-agents/engine/browser in sandbox) → 29/40 Good; merged punch list + provisional home mapping appended to PROGRESS.md as the U5.1 re-score baseline. |
| 2026-09-13 | impeccable (document) · ponytail · i-have-adhd | **U1.1** — scan-mode `document` pass over `src/harness/ui/templates/index.html`: extracted the 20 OKLCH tokens + Fraunces/IBM Plex hierarchy + components into `DESIGN.md` (frontmatter + 8 sections, North Star "The Night Observatory") and the `.impeccable/design.json` sidecar (9 drop-in components, ramps, shadows, motion). No UI edits (U1 is read-only). |
| 2026-09-13 | ponytail · i-have-adhd | Vendored as the **mandatory efficiency layer** for the `plans/` improvement program (agent.md §1): ponytail governs implementation (ladder, minimal diffs, `ponytail:` debt tags, audit/review/debt at gates); i-have-adhd governs reporting (action-first, numbered, state-restating). Roadmap item #1 now installed. |
| 2026-09-12 | hallmark · impeccable · frontend-design | Full console redesign + AI-provider flow + MCP service cards |

| # | Skill | Version | Author | License | Install path |
|---|-------|---------|--------|---------|--------------|
| 1 | **Hallmark** | 1.1.0 | Nutlope (Together AI) | MIT | `.claude/skills/hallmark/` |
| 2 | **Impeccable** | 4.3.1 | Paul Bakaus | Apache-2.0 | `.claude/skills/impeccable/` + `.claude/agents/` |
| 3 | **Frontend Design** | latest | Anthropic (official) | see LICENSE.txt | `.claude/skills/frontend-design/` |
| 4 | **Ponytail** (+ audit/debt/review) | latest | DietrichGebert | MIT | `.claude/skills/ponytail*/` |
| 5 | **I Have ADHD** | latest | ayghri | MIT | `.claude/skills/i-have-adhd/` |

> Skills 4–5 are the **workflow-efficiency layer**, not design skills. They are mandatory for the
> `plans/` improvement program — see [`.agent/agent.md`](../.agent/agent.md) §1.
> **Ponytail**: laziest solution that works (reuse → stdlib → native → one-line → minimum code),
> deletion over addition, `ponytail: <ceiling>, <upgrade path>` tags on deliberate shortcuts.
> Commands: `/ponytail-audit` (repo-wide over-engineering scan), `/ponytail-review` (diff review at gates),
> `/ponytail-debt` (harvest markers into a ledger). **I Have ADHD**: output shaped for action —
> next action first, numbered steps, state restated every turn, specific time estimates, visible wins.

---

## 1. Hallmark — anti-AI-slop design

*"A design skill that refuses to look AI-generated."* — 21 themes, 57 slop-test gates, structural variety.
Source: [github.com/Nutlope/hallmark](https://github.com/Nutlope/hallmark) · [usehallmark.com](https://usehallmark.com)

| Command | What it does |
|---------|--------------|
| `hallmark <brief>` | Build new UI. Picks a macrostructure, applies the rule-set, runs the slop test before handing back. |
| `hallmark audit <target>` | Score existing code against the anti-patterns. Punch list, no edits. |
| `hallmark redesign <target>` | Throw out the structure, keep copy + IA + brand, rebuild with a different fingerprint. |
| `hallmark study <screenshot \| URL>` | Extract the DNA from a design you admire (macrostructure, type-pairing, colour anchor). Refuses pixel-clones. |

## 2. Impeccable — the design language (23 commands)

*"Design fluency for frontend development."* — full interface lifecycle: craft, shape, audit, polish, harden, animate…
Source: [github.com/pbakaus/impeccable](https://github.com/pbakaus/impeccable) · [impeccable.style](https://impeccable.style)

**Build** · `shape` · `init` · `document` · `extract` *(+ deprecated `craft`)*
**Evaluate** · `critique` · `audit`
**Refine** · `polish` ⭐ · `bolder` · `quieter` · `distill` · `harden` · `onboard`
**Enhance** · `animate` · `colorize` · `typeset` · `layout` · `delight` · `overdrive`
**Fix** · `clarify` · `adapt` · `optimize`
**Iterate** · `live`

Invoke as `/impeccable <command> [target]`, e.g. **`/impeccable polish src/ui`** for the final UI polishment pass.

Comes with 4 subagents installed in `.claude/agents/`: `impeccable-asset-producer`, `impeccable-documenter`, `impeccable-finish-reviewer`, `impeccable-manual-edit-applier`.

> Note: installed as skill + agents. The official plugin also ships PostToolUse/Stop hooks; if you want them, run `/plugin marketplace add pbakaus/impeccable` in Claude Code.

## 3. Frontend Design — Anthropic's official skill

Guidance for distinctive, intentional visual design when building new UI or reshaping existing ones: aesthetic direction, typography, deliberate palette/layout choices that don't read as templated defaults. Auto-invoked on UI work — no subcommands.
Source: [github.com/anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/frontend-design)

---

## 🧭 Which skill for which job?

| Task | Reach for |
|------|-----------|
| Build a brand-new page from scratch | `hallmark` (+ frontend-design as baseline) |
| **Polish / finish an existing screen** | `/impeccable polish` |
| Review or score existing UI | `/impeccable critique` · `/impeccable audit` · `hallmark audit` |
| Redesign keeping copy + brand | `hallmark redesign` |
| Capture design DNA of a site you admire | `hallmark study` |
| Document current design → DESIGN.md | `/impeccable document` |
| Motion / color / typography passes | `/impeccable animate` · `colorize` · `typeset` |

---

## 🚀 Future-upgrade roadmap — reference frameworks

> **Not installed** — these are vetted open-source targets to *study* (and selectively
> adopt) when the research-harness outgrows a hand-rolled piece. Each maps a known
> framework to the harness component it would upgrade.

| # | Framework | What it offers | Borrow for (this project) |
|---|-----------|----------------|---------------------------|
| 1 | **Ponytail** — [github.com/DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) ✅ **INSTALLED 2026-09-13** | Agent rule pack: write less, ship only what's needed, tag corner-cuts with a `ponytail:` comment (`/ponytail-debt` greps them). | Discipline for future agent contributions — keep the repo lean; complements the bugfix.json prevention rules. Now the mandatory efficiency layer of `plans/` (with i-have-adhd). |
| 2 | **Composio** — [github.com/composiohq/composio](https://github.com/composiohq/composio) | 1000+ toolkits, managed auth, tool search, MCP gateway, sandboxed workbench. | Replace the hand-rolled MCP preset catalog (`routes_mcp.py`, `harness/mcp/`) with a real connector + auth layer. |
| 3 | **Chainlit** — [github.com/Chainlit/chainlit](https://github.com/Chainlit/chainlit) | Python framework for chat UIs: streaming, rich elements (tables/charts), multi-step flows, auth. | Upgrade the web console (`harness.ui`): streaming responses, richer message types, step visualization. |
| 4 | **Open WebUI** — [github.com/open-webui/open-webui](https://github.com/open-webui/open-webui) | Self-hosted chat UI over Ollama/OpenAI endpoints: RAG, function calling, multi-user, plugins. | Multi-model/multi-user direction + document RAG for the AI Provider / Keys / Sessions panels. |
| 5 | **Agno** — [github.com/agno-agi/agno](https://github.com/agno-agi/agno) | Python agent framework (formerly Phidata): memory, knowledge/RAG, multi-modal, agent teams. | Upgrade the hand-rolled loop (`harness.loop`): memory, multi-step tool use, agent teams. |
| 6 | **Semantic Kernel / MS Agent Framework** — [github.com/microsoft/semantic-kernel](https://github.com/microsoft/semantic-kernel) | Enterprise SDK: plugins/functions, planners, memory, multi-agent; A2A + MCP interop. | The citation/memory/tool-planning layers (`harness/citations`, `memory`, `registry`); A2A/MCP interop. |
| 7 | **Dify** — [github.com/langgenius/dify](https://github.com/langgenius/dify) | Self-hosted platform: visual agent/workflow/RAG pipelines, model management, collaboration. | The "product-grade" direction — a no-code workflow + RAG builder if the harness grows past a single console. |

### Quick routing — future upgrade intent

| You want to… | Study / adopt |
|--------------|---------------|
| Extend tools beyond the built-in fetcher + DuckDuckGo | Composio |
| Add streaming / richer chat UX | Chainlit, Open WebUI |
| Evolve single-agent loop → multi-agent, memory, RAG | Agno, Semantic Kernel |
| Add a visual workflow / RAG builder | Dify |
| Keep agent contributions lean & intentional | Ponytail |

> Licensing note (verify before adopting code): Chainlit & Composio — Apache-2.0;
> Semantic Kernel — MIT; Agno — MPL-2.0; Open WebUI — BSD-3-Clause-based (custom
> branding terms); Dify — Apache-2.0-based (Dify Open Source License); Ponytail —
> see repo LICENSE.
