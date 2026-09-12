# Models route — list models from OpenAI-compatible /models endpoint
from __future__ import annotations

import os
from fastapi import FastAPI, HTTPException, Query

from harness.llm.client import LLMClient, LLMConnectionError, LLMResponseError


def mount(app: FastAPI) -> None:
    @app.get("/api/models")
    async def list_models(base_url: str = Query(default="")):
        client = LLMClient(
            base_url=base_url or os.environ.get("HARNESS_LLM_BASE_URL", "http://localhost:11434/v1"),
            model_name="",
            api_key_env=os.environ.get("HARNESS_LLM_API_KEY_ENV", "none"),
        )
        try:
            models = client.list_models()
            return {"models": models}
        except LLMConnectionError as exc:
            raise HTTPException(503, str(exc))
        except LLMResponseError as exc:
            raise HTTPException(502, str(exc))
