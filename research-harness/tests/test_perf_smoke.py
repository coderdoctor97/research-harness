# P10.T2 — Perf smoke test
from __future__ import annotations

import time
import pytest
from harness.memory.doccache import DocumentCache


def test_cache_hit_fast_path():
    cache = DocumentCache(cache_dir=".cache/test_doc_perf", ttl=60)
    cache.set("url1", {"content": "cached content"})
    start = time.monotonic()
    r = cache.get("url1")
    elapsed = time.monotonic() - start
    assert r is not None
    assert elapsed < 0.01  # < 10ms for cache hit
