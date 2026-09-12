# P10.T5 — Multi-model prompt tuning tests
from __future__ import annotations

from harness.loop.prompts import build_system_prompt, get_profile
from harness.registry.index import ToolRegistry


def test_llama3_profile():
    p = get_profile("llama3")
    assert p["name"] == "Llama 3"


def test_mistral_profile():
    p = get_profile("mistral")
    assert p["name"] == "Mistral"


def test_qwen_falls_back():
    p = get_profile("")
    assert p["name"] == "Llama 3"


def test_build_prompt_includes_tools():
    reg = ToolRegistry()
    reg.register(__import__("harness.tools.builtin.compute", fromlist=["ComputeTool"]).ComputeTool())
    prompt = build_system_prompt(reg, model_name="llama3")
    assert "compute" in prompt
    assert "research assistant" in prompt


def test_build_prompt_mistral_style():
    reg = ToolRegistry()
    prompt = build_system_prompt(reg, model_name="mistral")
    assert "concise" in prompt.lower()
