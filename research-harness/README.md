# Local LLM Research Assistant Harness

A config-driven, async-first Python harness for local LLM research workflows.

## Quickstart

```bash
# 1. Install
cd research-harness
pip install -e ".[dev]"

# 2. Configure
cp config.yaml.example config.yaml
cp .env.example .env
# Edit .env with your endpoint settings

# 3. Run
harness
```

## What's Included

- `LLMClient` — OpenAI-compatible chat completions with timeout + error handling
- CLI REPL — interactive chat loop with `/quit`
- Config loader — YAML-based with env var resolution
- Tool registry — dynamic tool discovery from config (coming in Phase 3)
- Orchestration loop — ReAct-style agent loop (coming in Phase 4)

## Requirements

- Python 3.11+
- A running local LLM server (Ollama, llama.cpp, vLLM, or any OpenAI-compatible endpoint)

## License

MIT
