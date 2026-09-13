# LLM Research Harness

A local-LLM research assistant harness: orchestration loop, tool registry,
citations, memory, and a web console — speaking **OpenAI-compatible HTTP**, so
any endpoint works (Ollama, LM Studio, llama.cpp, vLLM locally, or OpenAI /
OpenRouter / Groq / Together in the cloud).

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

No secrets in the repo — set keys via env (see `.env.example`) or live in the UI.

## Web console

```bash
harness-ui          # http://127.0.0.1:8080 (override: HARNESS_UI_HOST / HARNESS_UI_PORT)
```

1. **Chat** — research assistant with browsing tools; answers cite sources.
2. **AI Provider** — pick a provider preset → paste API key → **Test
   connection** → **Fetch models** → save as default. Any OpenAI-compatible
   `base_url` works. See [`docs/ai-integration.md`](docs/ai-integration.md).
3. **Keys** — masked key storage (server memory + environment only).
4. **Endpoints** — optional manual tool APIs.
5. **MCP Services** — free built-ins are ready by default:
   - `builtin-fetcher` — endpoint fetcher (`fetch_url`, `extract_links`)
   - `builtin-search` — DuckDuckGo web search (`web_search`), no API key
   Plus one-click presets (Brave Search with free key, stdio fetch/DDG) and an
   optional manual MCP server form.
6. **Logs** / **Config** — tool telemetry and sanitized export/import.

## Docs

- ⭐ [`docs/connection-guide.md`](docs/connection-guide.md) — **start here**: connecting AI, the two key forms, endpoints, verifying free MCP services
- [`docs/ai-integration.md`](docs/ai-integration.md) — provider setup + browsing tools
- [`docs/config-reference.md`](docs/config-reference.md) — config keys
- [`docs/architecture.md`](docs/architecture.md), [`docs/extending.md`](docs/extending.md),
  [`docs/setup.md`](docs/setup.md), [`docs/troubleshooting.md`](docs/troubleshooting.md)

## UI design skills

The console UI is polished with installed Claude design skills — see the
**project skill dictionary** in [`skills-dictionary/SKILLS_DICTIONARY.md`](skills-dictionary/SKILLS_DICTIONARY.md):

- `.claude/skills/hallmark/` — Hallmark (anti-AI-slop design, audit verb used on this UI)
- `.claude/skills/impeccable/` — Impeccable (23-command design language; polish/critique passes)
- `.claude/skills/frontend-design/` — Anthropic's official frontend design guidance
