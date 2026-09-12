# Phase 1 smoke tests — P1.T5
from harness.llm.client import LLMClient


def test_client_init():
    c = LLMClient()
    assert c.model_name == "llama3"
