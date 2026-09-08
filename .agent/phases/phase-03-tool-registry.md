# Phase 03 — Tool Registry & Basic Tool Execution

> **Squad:** Squad-Core (spine) · **Depends on:** P2 · **Tasks:** 6
> **Source of truth:** `plan.md` §3 (tool defs + schema generation), §7-Phase 3, §8 (endpoint failure tables)

## Goal

A tool registry that auto-generates LLM-facing schemas from config and executes HTTP-based tools
through one generic executor — template fill → HTTP call → response parse → structured output.

## Preconditions

- Phase 2 `DONE` (typed config, template engine, env resolver, hot-reload).

## Tasks

| ID | Task | Mode | Owner | Output |
|---|---|---|---|---|
| P3.T1 | `Tool` base class: name, description, JSON-parameter schema, `run(**params) -> ToolResult`; generates OpenAI function-calling schema (`{"type":"function","function":{...}}` per §3); `ToolResult` = success/error union with metadata (never raw headers) | `[S]` | IMPLEMENTER-A | `registry/tool.py` |
| P3.T2 | Registry auto-discovery: build tools from enabled `endpoints` entries; group by tool type; first enabled = primary, rest = fallbacks (§2 rule 5); expose `list_schemas()` for the prompt builder | `[P]` | IMPLEMENTER-A | `registry/index.py` |
| P3.T3 | Generic HTTP executor: fill templates → async httpx request (GET/POST) → parse response via `response_parsing` (dot-notation `results_path`, `fields` mapping; JSON + XML via `format`) → normalized tool output; every §8 malformed-response row implemented here | `[P]` | IMPLEMENTER-B | `registry/executor.py` |
| P3.T4 | Rate limiter + retry: token-bucket per endpoint (`requests_per_minute/day`), retry with configured `backoff_seconds`, honor `Retry-After` on 429 (§8), failover to fallback endpoint on exhaustion | `[P]` | IMPLEMENTER-C | `registry/ratelimit.py` |
| P3.T5 | `web_search` tool per §3.1 (Serper-shaped config): params `query`, `num_results`, `country_code`; output `results[]`, `query_used`, `result_count`; fixture-based tests with recorded HTTP responses | `[P]` | IMPLEMENTER-B | `tools/builtin/web_search.py` + tests |
| P3.T6 | `fetch_url` tool per §3.2 (Jina-reader-shaped): params `url`, `extract_links`; content truncation to `max_content_tokens` + `content_truncated` flag; `{{target_url}}` URL-encoding (§10 Test 12); fixture tests | `[P]` | IMPLEMENTER-C | `tools/builtin/fetch_url.py` + tests |

## Execution Waves

1. **Wave 1 (sequential):** P3.T1 — base class defines the contracts.
2. **Wave 2 (parallel):** P3.T2 + P3.T3 + P3.T4 (executor and limiter are composed by T5/T6 but
   coded against T1 interfaces — keep signatures frozen at wave start).
3. **Wave 3 (parallel):** P3.T5 + P3.T6.
4. **Wave 4:** TEST GATE (TESTER) → REVIEW GATE (REVIEWER checks §8 tables are covered).

## Acceptance Criteria (from plan.md §7-P3)

- [ ] Tool schemas are correctly generated in OpenAI function-calling format
- [ ] `web_search("latest AI news")` returns parsed, structured results (fixture + live-flagged test)
- [ ] `fetch_url("https://example.com")` returns markdown content
- [ ] HTTP errors return structured error objects, not crashes (4xx, 5xx, timeout, DNS, empty body)
- [ ] Rate limiting is respected (limiter unit test with fake clock)
- [ ] Failover: with primary returning 500 persistently, the fallback endpoint serves the call

## Handoff to Phase 4

- `registry.index.list_schemas()` → consumed by the prompt builder (P4.T5).
- `registry.index.dispatch(tool_call)` → the single call the orchestration loop makes; it
  internally handles fallbacks, limits, retries, and returns normalized `ToolResult`s.
