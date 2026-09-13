# AI Integration Guide

The harness speaks **OpenAI-compatible HTTP** — any endpoint exposing
`/v1/models` and `/v1/chat/completions` works: local servers (Ollama,
LM Studio, llama.cpp, vLLM) or cloud providers (OpenAI, OpenRouter, Groq,
Together, …). The integration is deliberately simple:

```
provider preset ──► API key ──► test connection ──► fetch models ──► chat
```

## 1. Set up a provider (web UI)

Start the console:

```bash
harness-ui            # http://127.0.0.1:8080  (override with HARNESS_UI_HOST/PORT)
```

Open **02 · AI Provider**:

1. Pick a provider preset — the base URL fills in automatically
   (Ollama `http://localhost:11434/v1`, OpenAI `https://api.openai.com/v1`, …),
   or choose *Custom* and paste any OpenAI-compatible base URL.
2. Paste your **API key** (optional for local servers). Keys stay on the
   machine: server-memory only, always shown masked, never echoed back.
3. Press **Test connection** — the console hits `/models`, reports
   latency + model count, and explains common failures.
4. Press **Fetch models**, click a model card, then **Save as default**.

The same flow is available over HTTP:

| Route | Purpose |
|-------|---------|
| `GET /api/ai/provider` | Active provider (key masked) + presets |
| `POST /api/ai/provider` | Save `{provider, base_url, api_key, api_key_env, model}` |
| `POST /api/ai/test` | `{base_url, api_key}` → `{ok, latency_ms, models_count}` |
| `GET /api/models?base_url=&api_key=` | List models from any endpoint |

## 2. Browsing tools — free by default

The assistant gets browsing capabilities through **MCP services**, two of
which are built in and free (no API keys, no subprocesses, no setup):

| Service | Tools | What it does |
|---------|-------|--------------|
| `builtin-fetcher` | `fetch_url`, `extract_links` | Fetch any endpoint and read it as clean text |
| `builtin-search` | `web_search` | DuckDuckGo web search (titles, URLs, snippets) |

During chat, the model can request a tool by replying with JSON:

```json
{"tool_calls": [{"name": "web_search", "arguments": {"query": "…"}}]}
```

The harness executes it, feeds the result back, and asks again (bounded to
3 rounds). Answers cite the sources they used, and the UI renders them as
numbered citations.

### Optional extras

In **05 · MCP Services** you can additionally:

- enable the **Brave Search** preset (free-tier `BRAVE_API_KEY`, set it in
  **03 · Keys** or inline when enabling),
- install the official stdio fetch/DDG servers (`uvx mcp-server-fetch`,
  `uvx duckduckgo-mcp-server`),
- or use **Advanced → add manual MCP server** to point at any stdio command
  or SSE URL. This is entirely optional — everything works without it.

## 3. Optional manual endpoints

**04 · Endpoints** wires classic HTTP tool APIs (Serper, etc.) when you have
them: name + URL template + method + key env var, with a per-endpoint **Test**
button. Not required for browsing — the built-ins cover that.

## 4. Research workflow (multi-query fan-out)

`harness.research.run_research(question, llm_chat, run_tool)` is the single
entry point for research-grade answers (capability #1 + #3):

1. **Decompose** — one LLM call turns the question into 3–5 targeted queries
   (malformed output falls back to the original question, never crashes).
2. **Fan-out** — queries run in parallel (`max_parallel`, per-call timeout);
   partial failures are noted, not fatal.
3. **Aggregate** — results are URL-deduped and registered into the
   `SourceRegistry` in fan-out order (stable citation IDs).
4. **Synthesize + citation pipeline** — the answer is generated against the
   source pool, then passes the full `citations/` pipeline: orphan `[n]`
   removed, fabricated URLs stripped, bare URLs link-formatted, Sources
   section deduped/capped, keys scrubbed.

### Citation metadata contract (consumed by the UI — frozen at A3.2)

`run_research` returns:

```json
{
  "answer": "…validated markdown with [n] citations and a ## Sources section…",
  "queries": ["query 1", "query 2"],
  "sources": [{"id": 1, "title": "…", "url": "https://…"}],
  "citations": {"1": {"url": "https://…", "title": "…"}},
  "report": {"warnings": [], "stripped_urls": [], "redacted_keys": []},
  "failures": [{"query": "…", "error": "…"}],
  "degraded": false
}
```

- `citations` maps source id → url/title so the UI renders `[n]` anchors
  without re-parsing markdown.
- `degraded: true` means every search backend failed; `answer` is an honest
  §8-style notice (no crash, no hanging loop).
