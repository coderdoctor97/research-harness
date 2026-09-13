# Architecture

## Components

- `llm/client.py` — OpenAI-compatible chat, model listing, and token streaming.
- `config/` — Pydantic models, resolver, templates, watcher.
- `registry/` — Tool base class, HTTP executor, rate limiter, dynamic tool generator.
- `loop/` — Shared orchestration core, parser, dispatcher, prompt builder, recovery.
- `citations/` — Source registry, URL validation, scrubbing, finalization pipeline.
- `memory/` — Token counter, budget, summarizer, document cache, dedup.
- `tools/builtin/` / `mcp/builtin.py` — built-in research tools exposed through `ToolRegistry`.
- `ui/` — FastAPI app with endpoint, key, chat, streaming, logs, config, and MCP routes.

## One-loop chat flow

```text
CLI REPL ─┐
          ├─> harness.loop.agent.run_chat(...) / run_chat_stream(...)
UI chat ──┘        │
                   ├─ memory.compute(...) + memory.build_context(...)
                   ├─ LLMClient.chat(...) or LLMClient.stream_chat(...)
                   ├─ parser.extract_tool_calls(...)
                   ├─ dispatcher.async_dispatch(...) via ToolRegistry
                   ├─ memory.DedupCache + optional DocumentCache
                   ├─ SourceRegistry + citation finalize(...)
                   └─ return final response / stream events
```

Both CLI and UI now use the same loop core. Surface code owns only I/O concerns: CLI printing, FastAPI HTTP/SSE framing, provider/model discovery, and UI session persistence.

## HTTP client pooling and async boundaries

`LLMClient` keeps one reusable `httpx.Client` per `(base_url, timeout)` endpoint configuration. API keys remain request headers, so secrets are not part of the pool key and are never stored in pool metadata. UI routes that need synchronous model discovery run it through `asyncio.to_thread(...)`; chat orchestration likewise keeps blocking model/tool work out of the FastAPI event loop through the shared core.

## Non-streaming flow

1. User query enters `run_chat(...)`.
2. Core assembles system prompt, history, tool results, and token budget.
3. `LLMClient.chat(...)` returns a model response.
4. Core parses final answer or tool calls.
5. Tool calls dispatch through `ToolRegistry` and results are injected back into context.
6. At the tool-round cap, core adds the force-final prompt and performs one last LLM call.
7. Final text runs through citation/link/source/key-scrub post-processing.

## Streaming flow and SSE contract

Streaming is opt-in. Surfaces call `run_chat_stream(...)`; the default `/api/chat` path still uses `run_chat(...)`.

UI endpoint contract:

- `POST /api/chat/stream` with JSON body `{ "message": "...", "model": "...", "session_id": "..." }`.
- `GET /api/chat/stream?message=...&model=...&session_id=...`.
- Response media type: `text/event-stream`.
- Each frame is:

```text
event: <event-type>
data: <json payload>
```

Event schema:

| Event | Payload fields | Meaning |
|---|---|---|
| `token` | `type`, `text` | One streamed model text chunk from `LLMClient.stream_chat(...)`. |
| `tool_call` | `type`, `name`, `arguments` | The completed streamed response requested a tool. |
| `tool_result` | `type`, `name`, `result` | A tool finished; `result` is the standardized tool payload. |
| `final` | `type`, `response`, `tool_calls`, `sources`, `model`, `report`, `context`, `session_id` | Final post-processed answer. In the UI route this event also persists the chat session. |
| `error` | `type`, `error` | SSE-only error frame for connection/LLM failures. |

The `token/tool_call/tool_result/final` schema is frozen for UI plan U3.3. UI rendering may consume these events but should not change their names or required fields without an engine review gate.

## Extending

See `extending.md` for adding tools and custom endpoints.
