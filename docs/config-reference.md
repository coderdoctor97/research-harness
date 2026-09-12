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
