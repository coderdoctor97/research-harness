# P2.T1 — Pydantic schema for plan.md §2 (harness + endpoints + custom_endpoints)
from __future__ import annotations

from pydantic import BaseModel, Field


class EndpointDef(BaseModel):
    url: str = Field(description="OpenAI-compatible base URL or template with {{placeholders}}")
    method: str = Field(default="POST")
    api_key_env: str = Field(default="none")
    timeout: float = Field(default=30.0)
    retries: int = Field(default=2)
    retry_after: bool = Field(default=True)


class CustomEndpointDef(BaseModel):
    name: str = Field(description="Tool name exposed to the model")
    description: str = Field(default="")
    endpoint: EndpointDef
    parameters: dict = Field(default_factory=dict)
    tool_mapping: str | None = Field(default=None, description="Maps to builtin tool if provided")


class HarnessConfig(BaseModel):
    llm: dict = Field(description="{base_url, model_name, api_key_env, timeout, max_iterations}")
    endpoints: list[EndpointDef] = Field(default_factory=list)
    custom_endpoints: list[CustomEndpointDef] = Field(default_factory=list)
