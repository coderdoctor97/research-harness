"""Shared AI-provider state for the UI (OpenAI-compatible endpoints).

The harness speaks OpenAI-compatible HTTP: any base_url exposing
/models and /chat/completions works — local (Ollama, LM Studio, llama.cpp,
vLLM) or cloud (OpenAI, OpenRouter, Groq, Together, ...).

State is persisted to `.harness-state.json` (see bugfix.json BF-010) so the
saved provider survives server restarts. Set HARNESS_STATE_FILE to relocate
the file (tests point it at a temp path).
"""
from __future__ import annotations

import json
import os

# Provider presets: base_url templates + whether an API key is expected.
AI_PROVIDER_PRESETS: dict[str, dict] = {
    "ollama": {"label": "Ollama (local)", "base_url": "http://localhost:11434/v1", "needs_key": False},
    "lmstudio": {"label": "LM Studio (local)", "base_url": "http://localhost:1234/v1", "needs_key": False},
    "openai": {"label": "OpenAI", "base_url": "https://api.openai.com/v1", "needs_key": True},
    "openrouter": {"label": "OpenRouter", "base_url": "https://openrouter.ai/api/v1", "needs_key": True},
    "groq": {"label": "Groq", "base_url": "https://api.groq.com/openai/v1", "needs_key": True},
    "together": {"label": "Together AI", "base_url": "https://api.together.xyz/v1", "needs_key": True},
    "custom": {"label": "Custom OpenAI-compatible", "base_url": "", "needs_key": False},
}

# BF-011 note: no hardcoded default models here — cloud model IDs go stale.
# When no model is saved, routes_chat auto-discovers one from the endpoint's
# /models list and persists the choice.

# ---------------------------------------------------------------------------
# Persistence — .harness-state.json (gitignored). Sections: ai_provider, keys.
# ---------------------------------------------------------------------------

def _state_file() -> str:
    override = os.environ.get("HARNESS_STATE_FILE")
    if override:
        return override
    pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../src/harness
    return os.path.normpath(os.path.join(pkg_root, "..", "..", ".harness-state.json"))


def _read_state_file() -> dict:
    try:
        with open(_state_file(), "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_state_file(data: dict) -> None:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(_state_file())), exist_ok=True)
        with open(_state_file(), "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
    except OSError:
        pass


def load_section(section: str, default=None):
    return _read_state_file().get(section, default)


def persist_section(section: str, value) -> None:
    data = _read_state_file()
    data[section] = value
    _write_state_file(data)


# ---------------------------------------------------------------------------
# Active provider configuration — loaded from disk at import.
# ---------------------------------------------------------------------------

_DEFAULT_STATE: dict = {
    "provider": "ollama",
    "base_url": "http://localhost:11434/v1",
    "api_key": "",
    "api_key_env": "none",
    "model": "",
    # BF-014: generation controls. None/0 = let the endpoint decide.
    "max_tokens": None,      # cap on OUTPUT tokens per response
    "context_window": None,  # client-side cap on context fed to the model
}

_ai_state: dict = dict(_DEFAULT_STATE)


def _load_ai_state() -> None:
    saved = load_section("ai_provider") or {}
    if isinstance(saved, dict):
        for key in _ai_state:
            if key in saved and saved[key] is not None:
                _ai_state[key] = saved[key]


_load_ai_state()


def get_state() -> dict:
    return dict(_ai_state)


def update_state(**fields) -> dict:
    # None explicitly clears a field (used by BF-014 generation controls and
    # BF-011 model rediscovery). Callers pass real values; save_provider drops
    # untouched keys via model_dump(exclude_none=True).
    for key, value in fields.items():
        if key in _ai_state:
            _ai_state[key] = value
    persist_section("ai_provider", dict(_ai_state))
    return dict(_ai_state)


def mask_key(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "****"
    return value[-4:].rjust(len(value), "*")


def public_state() -> dict:
    """State safe to send to the browser — API key always masked."""
    state = get_state()
    state["api_key_masked"] = mask_key(state.get("api_key", ""))
    state["api_key"] = ""
    return state
