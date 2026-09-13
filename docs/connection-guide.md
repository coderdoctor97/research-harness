# 🔌 Connection Guide — AI, Keys, Endpoints & MCP Services

> Everything you need to connect the harness to an AI, understand the two key
> forms, and verify the free browsing services. Follow top-to-bottom once;
> afterwards use the sections as a reference.

---

## 0. The big picture

```
            ┌─────────────────────────────────────────────────────┐
            │              RESEARCH HARNESS CONSOLE               │
            │                                                     │
  CHAT ───► │  AI Provider ──── talks to ────► your LLM endpoint  │
            │      (OpenAI-compatible: /v1/models, /v1/chat/…)    │
            │                                                     │
            │  MCP Services ── browsing tools the AI can use ──►  │
            │      builtin-fetcher  · builtin-search (free)       │
            │      brave / stdio / manual       (optional)        │
            │                                                     │
            │  Keys ─────► credentials used by the two above      │
            │  Endpoints ► optional classic HTTP tool APIs        │
            └─────────────────────────────────────────────────────┘
```

- **AI Provider** = *the brain* (answers your questions).
- **MCP Services** = *the hands* (fetch pages, search the web for the brain).
- **Keys** = credentials both of them may need.
- **Endpoints** = optional extra APIs; **not required** for anything below.

Start the console:

```bash
harness-ui                 # → http://127.0.0.1:8080
# custom port/host:  HARNESS_UI_HOST=0.0.0.0 HARNESS_UI_PORT=9000 harness-ui
```

---

## 1. Connect the AI  *(tab 02 · AI Provider)*

The harness speaks **OpenAI-compatible HTTP** — local *or* cloud, it doesn't
matter. The flow is always:

```
provider preset ──► API key (if needed) ──► Test connection ──► Fetch models ──► Save
```

### 1a. Local server (Ollama / LM Studio / llama.cpp) — no key needed

| Field | Value |
|-------|-------|
| Provider preset | **Ollama (local)** → fills `http://localhost:11434/v1` (LM Studio: `http://localhost:1234/v1`) |
| Base URL | keep as filled (must end with `/v1`) |
| API key | **leave empty** |

### 1b. Cloud provider (OpenRouter, OpenAI, Groq, Together) — key needed

| Field | Value |
|-------|-------|
| Provider preset | e.g. **OpenRouter** → fills `https://openrouter.ai/api/v1` |
| Base URL | keep as filled |
| API key | paste the real key: `sk-or-v1-…`, `sk-…`, `gsk_…` |

Then press, in order:

1. **⟲ Test connection** — green LED + latency + model count = working.
   Red LED shows the exact error and a hint.
2. **Fetch models** — lists everything the endpoint serves and click a model
   card to select it. **This step now auto-saves the provider**, so chat works
   immediately afterwards — you don't have to press Save separately.
3. **Save as default** *(optional now)* — press it any time to re-save after
   changing fields.

> 💡 If chat ever says it can't reach the endpoint: you tested but never
> fetched/saved. Just press **Fetch models** once — it saves for you.
> And if you only set a key in **03 · Keys** (e.g. `OPENROUTER_API_KEY`),
> chat detects it and infers the provider automatically.

### ⚠️ The #1 confusion: “API key” vs “API key env var”

| Field | What goes in it | Example |
|-------|----------------|---------|
| **API key** | the **secret itself** | `sk-or-v1-abc123…` |
| **API key env var** | the **NAME of an environment variable** that holds the secret | `OPENROUTER_API_KEY` |

Most people should use **API key** and ignore the env-var field.
The env-var field only matters if you exported the key in your shell
(`export OPENROUTER_API_KEY=sk-or-v1-…`) and want the harness to read it from
there.

> 💡 Pasted your real key into the env-var field by accident? The console
> detects it (warning toast) and automatically treats it as the actual key —
> but the clean way is the **API key** field.

---

## 2. Keys tab explained  *(tab 03 · Keys)*

Both forms do the same mechanical thing — store a secret in server memory and
push it into the environment — but they serve different consumers.

### 2a. “Set tool endpoint key” (Tool keys sub-tab)

**Purpose:** credentials for *tool endpoints* (tab 04) — classic HTTP APIs
like Serper, Tavily, a PDF service, etc.

**When you need it:** only if you add a manual endpoint in tab 04 that
requires an API key. You set the key here *by the same name* you type into the
endpoint's “API key env var” field.

```
Example: you want Serper.dev search
  1. Keys → Tool keys → name: SERPER_API_KEY   value: 1a2b3c…  → Set key
  2. Endpoints → name: serper · url: https://google.serper.dev/search
                 method: POST · API key env var: SERPER_API_KEY → Add
  3. The endpoint now finds the key automatically (and its Test button works).
```

**You do NOT need tool keys for the free built-in browsing tools** — the
fetcher and DuckDuckGo search need no key at all.

### 2b. “Set AI backend key” (AI keys sub-tab)

**Purpose:** credentials for the *AI provider* — an alternative to pasting the
key in tab 02.

**When you need it:** never, if you already pasted the key into
**02 · AI Provider → API key**. Use this form when you prefer storing the key
once under its standard name (`OPENAI_API_KEY`, `OPENROUTER_API_KEY`,
`GROQ_API_KEY`, `TOGETHER_API_KEY`, `BRAVE_API_KEY`, …) so any part of the
harness can resolve it by name.

### Decision table

| I want to… | Use |
|------------|-----|
| Connect OpenRouter/OpenAI/Groq chat | 02 · AI Provider → **API key** field *(simplest)* |
| …or store that key under its standard name | 03 · Keys → **AI keys** |
| Add Serper / another paid tool API | 03 · Keys → **Tool keys**, then reference the name in 04 · Endpoints |
| Enable the Brave Search MCP preset | 03 · Keys → **AI keys** → `BRAVE_API_KEY` (or paste inline when enabling) |
| Use built-in fetcher + DuckDuckGo | **nothing** — no keys required ✅ |

Keys are only shown masked (`*********et99`), live in server memory, and are
never written to disk by the console.

---

## 3. Endpoints  *(tab 04 · Endpoints)* — optional

Classic HTTP tool APIs. **Everything works without them** — they exist for
specific paid/specialized APIs you may own.

1. Fill **name**, **URL** (`{query}` is substituted on test), **method**,
   and optionally an **API key env var** (see §2a).
2. **Add endpoint** → it appears in the table.
3. **Test** fires a real request and shows `ok` or the failure reason.
4. **✕** removes it.

---

## 4. MCP Services  *(tab 05 · MCP Services)*

### 4a. Free defaults — what you get with zero setup

| Service | Tools | Status |
|---------|-------|--------|
| `builtin-fetcher` | `fetch_url` (read any page as text), `extract_links` | ✅ built-in · ready |
| `builtin-search` | `web_search` (DuckDuckGo, titles + URLs + snippets) | ✅ built-in · ready |

Both run **inside the harness process** — no `npx`, no Docker, no API keys.
They are seeded automatically every time the server starts; the chat assistant
uses them on its own when it needs to browse, and answers show the sources as
numbered citations.

### 4b. “Are they actually working?” — verify in 30 seconds

**In the UI:** open **05 · MCP Services** → both cards show a green
**ready** badge, and under **Active servers** you see their tool tags
(`fetch_url`, `extract_links`, `web_search`).

**With one request each** (terminal, while `harness-ui` is running):

```bash
# 1) Fetcher — read a page
curl -s -X POST localhost:8080/api/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"server":"builtin-fetcher","tool":"fetch_url","arguments":{"url":"https://example.com"}}'

# 2) Search — DuckDuckGo
curl -s -X POST localhost:8080/api/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"server":"builtin-search","tool":"web_search","arguments":{"query":"large language model","max_results":3}}'
```

**Verified output (this project, 2026-09-12):**

```text
fetch_url  → ok: true, status 200, content: "Example Domain …"
web_search → ok: true, result_count: 3
             [1] Large language model - Wikipedia   → en.wikipedia.org
             [2] Large Language Model (LLM) …       → geeksforgeeks.org
             [3] What are large language models …   → ibm.com
```

If you see `"ok": true` with results, the free MCPs are working. If search
ever returns 0 results, it is a DuckDuckGo rate-limit blip — retry in a
minute; the fetcher is unaffected.

### 4c. Optional presets

| Preset | Cost | Extra requirement |
|--------|------|-------------------|
| **Brave Search** | free tier | API key from [brave.com/search/api](https://brave.com/search/api/) → set `BRAVE_API_KEY` in Keys, then press **Enable with key** |
| **Fetch (official stdio)** | free | `uvx` on PATH (`pip install uv`) |
| **DuckDuckGo (stdio)** | free | `uvx` on PATH |

### 4d. Manual MCP server (advanced, fully optional)

Expand **ADVANCED — ADD MANUAL MCP SERVER** and enter any stdio command, e.g.:

```
name:    filesystem
command: npx
args:    -y @modelcontextprotocol/server-filesystem /home/user/docs
```

or an SSE URL as the command (`https://my-mcp.example.com`). Manual servers
connect on demand; their tools appear once connected.

---

## 5. Test the whole pipeline

1. **02 · AI Provider** → Test connection (green) → Fetch models → pick one.
2. **01 · Chat** → ask something that needs the web, e.g.
   *“Search the web for recent news on AI agents and summarize with sources.”*
3. Expect: ⚙ tool badges (`web_search`, maybe `fetch_url`) + a numbered
   citation list under the answer.
4. **06 · Logs** shows every tool call with timing.

Quick curl chat test (replace nothing — uses your saved provider):

```bash
curl -s -X POST localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Search the web for what MCP is and cite sources"}'
```

---

## 6. Troubleshooting

| Symptom | Cause → fix |
|---------|-------------|
| Test connection: *Connection refused* | Server not running / wrong port. Start Ollama, or fix the base URL (keep `/v1`). |
| Test connection: *HTTP 401/403* | Missing or wrong API key → paste it into **API key** field. |
| Models list loads but chat fails with 401 | The endpoint's `/models` is public but chat needs auth — the key wasn't saved. Re-do step 1 with the key, then **Save as default**. |
| “endpoint offline” in chat header | Normal before first successful Fetch models; disappears once the provider works. |
| I pasted my key into *API key env var* | Move it to **API key**. (The console auto-recovers real-looking keys, but don't rely on it.) |
| Where did my keys/provider go after restart? | They shouldn't — provider + keys persist in `.harness-state.json` (gitignored). If you see "offline" after a restart, re-press **Fetch models** once; if it persists, check `bugfix.json` BF-010. |
| Search returns 0 results occasionally | DuckDuckGo throttling — retry; the fetcher still works. |

---

## Appendix · HTTP API

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/ai/provider` | GET / POST | read / save active provider (key masked on read) |
| `/api/ai/test` | POST | `{base_url, api_key}` → `{ok, latency_ms, models_count}` |
| `/api/ai/presets` | GET | provider preset list |
| `/api/models` | GET | `?base_url=&api_key=&api_key_env=` → model list |
| `/api/chat` | POST | `{message, model?}` → answer + tool_calls + sources |
| `/api/keys`, `/api/keys/{name}` | GET / POST / DELETE | masked key list / set / remove |
| `/api/endpoints`, `/api/endpoints/{name}[/test]` | GET / POST / DELETE | manual endpoints + live test |
| `/api/mcp/servers` | GET / POST / DELETE | MCP server list / add / remove |
| `/api/mcp/presets`, `/api/mcp/presets/{id}/install` | GET / POST | free presets + one-click install |
| `/api/mcp/tools`, `/api/mcp/tools/call` | GET / POST | list all tools / call a built-in tool |
| `/api/logs`, `/api/config/export|import` | GET / … | telemetry + sanitized config |
