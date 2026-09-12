# P10.T4 — Dedup cache tests
from __future__ import annotations

import pytest
from harness.memory.dedup import DedupCache, params_hash
from harness.registry.tool import ToolResult


def test_params_hash_deterministic():
    assert params_hash({"query": "AI"}) == params_hash({"query": "AI"})


def test_params_hash_differs():
    assert params_hash({"query": "AI"}) != params_hash({"query": "ML"})


def test_dedup_cache_hit():
    cache = DedupCache()
    r1 = ToolResult(ok=True, data="result1")
    cache.put("web_search", {"query": "AI"}, r1)
    cached = cache.get("web_search", {"query": "AI"})
    assert cached is r1


def test_dedup_cache_miss():
    cache = DedupCache()
    assert cache.get("web_search", {"query": "AI"}) is None


def test_dedup_cache_clear():
    cache = DedupCache()
    r1 = ToolResult(ok=True, data="x")
    cache.put("t", {"a": 1}, r1)
    cache.clear()
    assert cache.get("t", {"a": 1}) is None
