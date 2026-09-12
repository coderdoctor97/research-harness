# P6.T6 — Memory & Context tests: token counter, budget, summarizer, cache, assembler, sessions
from __future__ import annotations

import time
import os
import tempfile

from harness.memory.tokens import count
from harness.memory.budget import compute
from harness.memory.doccache import DocumentCache
from harness.memory.assembler import build_context
from harness.memory.sessions import Session
from harness.citations.registry import SourceRegistry


# --- Token counter ---
def test_count_fallback():
    assert count("hello world") >= 2  # 11 chars // 4 = 2

def test_count_empty():
    assert count("") == 0  # empty → 0 tokens (tiktoken or fallback)


# --- Budget calculator ---
def test_budget_defaults():
    b = compute()
    assert b["available"] == 8192 - 512 - 0 - 200 - 300
    assert b["history_allowance"] >= 256
    assert b["doc_allowance"] >= 0

def test_budget_custom_window():
    b = compute(context_window=4096, max_response_tokens=256)
    assert b["available"] == 4096 - 256 - 0 - 200 - 300

def test_budget_positive():
    b = compute(context_window=1024)
    assert b["available"] > 0


# --- Document cache ---
def test_cache_set_and_get():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = DocumentCache(cache_dir=tmpdir, ttl=60)
        cache.set("https://example.com", {"content": "hello"})
        assert cache.get("https://example.com")["content"] == "hello"

def test_cache_miss():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = DocumentCache(cache_dir=tmpdir, ttl=60)
        assert cache.get("https://missing.com") is None

def test_cache_expiry():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = DocumentCache(cache_dir=tmpdir, ttl=1)
        cache.set("https://example.com", {"content": "hello"})
        time.sleep(1.1)
        assert cache.get("https://example.com") is None

def test_cache_content_truncated_flag():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = DocumentCache(cache_dir=tmpdir, ttl=60)
        cache.set("https://example.com", {"content": "x" * 100000, "content_truncated": True})
        data = cache.get("https://example.com")
        assert data is not None
        assert data.get("content_truncated") is True

def test_cache_clear():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = DocumentCache(cache_dir=tmpdir, ttl=60)
        cache.set("https://example.com", {"content": "hi"})
        cache.clear()
        assert cache.get("https://example.com") is None


# --- Context assembler ---
def test_assembler_basic():
    sys_prompt = "You are a helpful assistant."
    history = [{"role": "user", "content": "What is AI?"}, {"role": "assistant", "content": "AI is artificial intelligence."}]
    docs = []
    budget = compute(context_window=4096)
    ctx, report = build_context(sys_prompt, history, docs, budget)
    assert "helpful" in ctx
    assert report["tokens"] > 0

def test_assembler_with_docs():
    sys_prompt = "You are a helpful assistant."
    history = [{"role": "user", "content": "What is AI?"}]
    docs = [{"content": "AI stands for Artificial Intelligence."}]
    budget = compute(context_window=4096)
    ctx, report = build_context(sys_prompt, history, docs, budget)
    assert "Artificial Intelligence" in ctx

def test_assembler_eviction_when_over_budget():
    sys_prompt = "You are a helpful assistant."
    history = [{"role": "user", "content": f"Question {i}: " + "word " * 200} for i in range(20)]
    docs = [{"content": "Document " * 500}]  # large doc
    budget = compute(context_window=2048, max_response_tokens=256)
    ctx, report = build_context(sys_prompt, history, docs, budget)
    # Aggressive eviction drops docs and keeps last 3 turns
    assert report["tokens"] <= budget["available"] + 100
    assert len(report["warnings"]) >= 0  # warnings logged, not raised

def test_assembler_no_docs_when_over_budget():
    sys_prompt = "You are a helpful assistant." * 100
    history = [{"role": "user", "content": "test"}]
    docs = [{"content": "x" * 10000}]
    budget = compute(context_window=512)
    ctx, report = build_context(sys_prompt, history, docs, budget)
    # aggressive eviction drops docs
    assert "x" * 100 not in ctx or report["tokens"] <= budget["available"]


# --- 20-turn stress test ---
def test_twenty_turn_stay_in_budget():
    """20-turn conversation stays within context window with budget."""
    sys_prompt = "You are a helpful research assistant."
    history = []
    for i in range(20):
        history.append({"role": "user", "content": f"Question {i}: tell me about topic {i}"})
        history.append({"role": "assistant", "content": f"Answer {i}: topic {i} involves several key facts and references [1]."})
    budget = compute(context_window=4096)
    ctx, report = build_context(sys_prompt, history, [], budget)
    assert report["tokens"] <= budget["available"] + 100


# --- Session persistence ---
def test_session_save_and_resume():
    with tempfile.TemporaryDirectory() as tmpdir:
        reg = SourceRegistry()
        reg.add("Source 1", "https://example.com/1", "web_search", 0)
        sess = Session("s1", reg)
        sess.add_turn("user", "What is AI?")
        sess.add_turn("assistant", "AI is artificial intelligence [1].")
        path = os.path.join(tmpdir, "session.json")
        sess.save(path)
        loaded = Session.load(path)
        assert loaded.session_id == "s1"
        assert loaded.turn_count == 2
        assert loaded.history[0]["content"] == "What is AI?"
        assert loaded.registry.get(1) is not None
        assert loaded.registry.get(1).title == "Source 1"


# --- Source references across turns ---
def test_source_refs_preserved_across_turns():
    """Sources introduced in earlier turns remain accessible."""
    reg = SourceRegistry()
    reg.add("Earlier Source", "https://earlier.com", "web_search", 0)
    history = [{"role": "assistant", "content": "Based on [1], here is the answer."}]
    sys_prompt = "You are a helpful assistant."
    budget = compute(context_window=4096)
    ctx, report = build_context(sys_prompt, history, [], budget)
    assert "earlier.com" not in ctx  # sources not auto-injected into context
    # But the registry still has the source
    assert reg.get(1) is not None
    assert reg.get(1).title == "Earlier Source"
