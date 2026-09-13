# Config Reference
## Top-level keys
| Key | Type | Description |
|-----|------|-------------|
| `llm.base_url` | string | OpenAI-compatible API base URL |
| `llm.model_name` | string | Model identifier |
| `llm.api_key_env` | string | Env var for API key (default: `none`) |
| `llm.timeout` | float | Request timeout in seconds |
| `llm.max_iterations` | int | Max tool-call loops per query |

## Endpoints
Each entry in `endpoints[]`: `{url, method, api_key_env, timeout, retries}`.

## Custom Endpoints
Each entry in `custom_endpoints[]`: `{name, endpoint, parameters, tool_mapping, enabled}`.
- `name`: Tool name exposed to the model
- `endpoint.url`: Template with `{{placeholders}}`
- `parameters`: `{body_template, query_params_template}`
- `tool_mapping`: Optional builtin tool to map to
- `enabled`: Enable/disable the tool

## MCP servers
`mcp_servers[]` is optional. The web UI seeds two **free built-in** services
automatically (no config needed):

| Server | Tools | Notes |
|--------|-------|-------|
| `builtin-fetcher` | `fetch_url`, `extract_links` | Endpoint fetcher for browsing — in-process, no key |
| `builtin-search` | `web_search` | DuckDuckGo search — in-process, no key |

Optional one-click presets in the UI: `brave-search` (needs free `BRAVE_API_KEY`),
`fetch-stdio` (`uvx mcp-server-fetch`), `ddg-stdio` (`uvx duckduckgo-mcp-server`).
Manual stdio/SSE servers can still be added (`command` + `args` + `env`) — see
`docs/ai-integration.md`.

## Web UI / AI provider state
The UI (`harness-ui`) keeps the active provider in memory and mirrors it to
environment variables so the chat route picks it up:

| Env var | Description |
|---------|-------------|
| `HARNESS_LLM_BASE_URL` | Active OpenAI-compatible base URL |
| `HARNESS_LLM_API_KEY` | Active API key (when one is set via the UI) |
| `HARNESS_LLM_API_KEY_ENV` | Name of the env var to resolve the key from |
| `HARNESS_UI_HOST` / `HARNESS_UI_PORT` | Bind address for `harness-ui` (default `127.0.0.1:8080`) |
