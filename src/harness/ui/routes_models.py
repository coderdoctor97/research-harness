# AI provider routes — OpenAI-compatible endpoints, any local or cloud base_url.
# Flow: pick provider preset -> set API key -> test connection -> fetch models.
from __future__ import annotations

import os
import time

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from harness.llm.client import LLMClient, LLMConnectionError, LLMResponseError
from harness.ui._ai_state import AI_PROVIDER_PRESETS, get_state, public_state, update_state


class ProviderPayload(BaseModel):
    provider: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    api_key_env: str | None = None
    model: str | None = None
    # BF-014: generation controls (max output tokens + context window cap).
    max_tokens: int | None = None
    context_window: int | None = None


class TestPayload(BaseModel):
    base_url: str | None = None
    api_key: str | None = None
    api_key_env: str | None = None


def _looks_like_key(value: str) -> bool:
    """Heuristic: a real secret, not an env var name (sk-…, sk_or_…, BSA…, 30+ chars)."""
    v = value.strip()
    return bool(v) and (v.startswith(("sk-", "sk_", "BSA", "xai-", "gsk_", "hf_")) or (len(v) >= 30 and "-" not in v.replace("_", "")))


def _build_client(base_url: str, api_key: str = "", api_key_env: str = "") -> LLMClient:
    # Forgiveness: if someone pasted a real key into the env-var field, use it as the key.
    if not api_key and _looks_like_key(api_key_env):
        api_key, api_key_env = api_key_env, ""
    return LLMClient(
        base_url=base_url,
        model_name="",
        api_key_env=api_key_env or os.environ.get("HARNESS_LLM_API_KEY_ENV", "none"),
        api_key=api_key or None,
    )


def mount(app: FastAPI) -> None:
    @app.get("/api/models")
    async def list_models(
        base_url: str = Query(default=""),
        api_key: str = Query(default=""),
        api_key_env: str = Query(default=""),
    ):
        state = get_state()
        client = _build_client(
            base_url=base_url or state["base_url"] or "http://localhost:11434/v1",
            api_key=api_key or state.get("api_key", ""),
            api_key_env=api_key_env,
        )
        try:
            models = client.list_models()
            return {"models": models}
        except LLMConnectionError as exc:
            raise HTTPException(503, str(exc))
        except LLMResponseError as exc:
            raise HTTPException(502, str(exc))

    @app.get("/api/ai/presets")
    async def list_presets():
        return {"presets": AI_PROVIDER_PRESETS}

    @app.get("/api/ai/provider")
    async def get_provider():
        return {"provider": public_state(), "presets": AI_PROVIDER_PRESETS}

    @app.post("/api/ai/provider")
    async def save_provider(payload: ProviderPayload):
        fields = payload.model_dump(exclude_none=True)
        base_url = fields.get("base_url")
        if base_url is not None and not base_url.strip():
            raise HTTPException(400, "base_url required")
        # Forgiveness: real key pasted into the env-var field → move it to api_key.
        if not fields.get("api_key") and _looks_like_key(fields.get("api_key_env") or ""):
            fields["api_key"] = fields.pop("api_key_env")
        # BF-014: coerce generation controls — only fields the client actually
        # sent are touched; empty/0/None clears to None (endpoint default).
        for gen_key in ("max_tokens", "context_window"):
            if gen_key not in payload.model_fields_set:
                continue
            raw = getattr(payload, gen_key, None)
            if raw is None or int(raw) <= 0:
                fields[gen_key] = None
            else:
                fields[gen_key] = int(raw)
        state = update_state(**fields)
        # Mirror into the environment so the chat route and tools pick it up.
        if state.get("base_url"):
            os.environ["HARNESS_LLM_BASE_URL"] = state["base_url"]
        if state.get("api_key"):
            os.environ["HARNESS_LLM_API_KEY"] = state["api_key"]
            os.environ["HARNESS_LLM_API_KEY_ENV"] = "HARNESS_LLM_API_KEY"
        return {"provider": public_state()}

    @app.post("/api/ai/test")
    async def test_connection(payload: TestPayload):
        """Test an OpenAI-compatible endpoint: reach /models, report latency + models."""
        state = get_state()
        base_url = (payload.base_url or state["base_url"] or "").strip()
        if not base_url:
            raise HTTPException(400, "base_url required")
        client = _build_client(
            base_url=base_url,
            api_key=payload.api_key or state.get("api_key", ""),
            api_key_env=payload.api_key_env or "",
        )
        started = time.perf_counter()
        try:
            models = client.list_models()
        except LLMConnectionError as exc:
            return {"ok": False, "base_url": base_url, "error": str(exc),
                    "hint": "Is the server running? Check the base URL (include /v1)."}
        except LLMResponseError as exc:
            return {"ok": False, "base_url": base_url, "error": str(exc),
                    "hint": "Endpoint answered but rejected the request — check the API key."}
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {
            "ok": True,
            "base_url": base_url,
            "latency_ms": latency_ms,
            "models_count": len(models),
            "sample_models": [m["id"] for m in models[:5]],
        }
