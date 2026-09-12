# Architecture
## Components
- `llm/client.py` — OpenAI-compatible chat + streaming
- `config/` — Pydantic models, resolver, templates, watcher
- `registry/` — Tool base class, executor (HTTP), rate limiter, dynamic tool generator
- `loop/` — Parser, agent loop, dispatcher, prompt builder
- `citations/` — Source registry, URL validation, scrubbing, pipeline
- `memory/` — Token counter, budget, summarizer, doc cache, dedup
- `tools/builtin/` — academic_search, news_search, extract_links, summarize_page, compute
- `ui/` — FastAPI app with routes for endpoints, keys, chat, logs, config

## Loop Flow
1. User query → system prompt assembly
2. LLM call → tool-call response or direct answer
3. Parallel tool execution with rate limiting
4. Results fed back to LLM (up to max iterations)
5. Final answer with citation post-processing

## Extending
See `extending.md` for adding tools and custom endpoints.
