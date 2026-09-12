# Setup Guide
## Prerequisites
- Python 3.10 or higher
- pip

## Installation
```bash
git clone <repo>
cd llm-research-harness
pip install -e "research-harness[dev]"
```

## Configuration
1. Copy `research-harness/config.yaml.example` to `research-harness/config.yaml`
2. Set `LLM_API_KEY` environment variable or add to `.env`
3. For Ollama: `ollama pull llama3` then use `base_url: http://localhost:11434/v1`

## Running
```bash
# CLI
harness chat

# Web UI
harness-ui
```

## Verification
```bash
cd research-harness && python -m pytest tests/ -q
```
