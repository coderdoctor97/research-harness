# P10.T2 — Perf smoke test
from __future__ import annotations

import time

from harness.llm.client import LLMClient
from harness.memory.doccache import DocumentCache


def test_cache_hit_fast_path():
    cache = DocumentCache(cache_dir=".cache/test_doc_perf", ttl=60)
    cache.set("url1", {"content": "cached content"})
    start = time.monotonic()
    r = cache.get("url1")
    elapsed = time.monotonic() - start
    assert r is not None
    assert elapsed < 0.01  # < 10ms for cache hit


def test_llm_client_reuses_httpx_client_per_endpoint_config():
    before = LLMClient.pool_size()

    c1 = LLMClient(base_url="http://pool.example/v1", model_name="a", timeout=7.0)
    c2 = LLMClient(base_url="http://pool.example/v1", model_name="b", timeout=7.0)
    c3 = LLMClient(base_url="http://other-pool.example/v1", model_name="a", timeout=7.0)

    assert c1.client is c2.client
    assert c1.client is not c3.client
    assert LLMClient.pool_size() >= before + 2
