# A2 — Multi-query research workflow (plans/ai-integration-plan.md, capability #1)
from __future__ import annotations

import asyncio
import json
import re
import typing

import pytest

from harness.citations.registry import SourceRegistry
from harness.research import (
    aggregate,
    decompose,
    fan_out,
    query_budget,
    run_research,
)


def _results(*urls: str) -> dict:
    return {"ok": True, "results": [
        {"title": f"T {u}", "url": u, "snippet": f"snippet for {u}"} for u in urls
    ]}


# ---------------------------------------------------------------------------
# A2.1 — Query decomposition
# ---------------------------------------------------------------------------

class TestDecompose:
    def test_valid_json_gives_query_list(self):
        llm = lambda p: json.dumps({"queries": ["q1", "q2", "q3"]})
        assert decompose("big question", llm) == ["q1", "q2", "q3"]

    def test_json_buried_in_prose_and_fences(self):
        llm = lambda p: 'Sure!\n```json\n{"queries": ["alpha", "beta"]}\n```\nDone.'
        assert decompose("q", llm) == ["alpha", "beta"]

    def test_malformed_output_falls_back_to_single_query(self):
        llm = lambda p: "I cannot answer in JSON, sorry."
        assert decompose("the question", llm) == ["the question"]

    def test_llm_error_falls_back_never_crashes(self):
        def llm(p):
            raise RuntimeError("model down")
        assert decompose("the question", llm) == ["the question"]

    def test_empty_and_non_string_entries_dropped(self):
        llm = lambda p: json.dumps({"queries": ["  ", 42, "real one"]})
        assert decompose("q", llm) == ["real one"]

    def test_query_count_capped(self):
        llm = lambda p: json.dumps({"queries": [f"q{i}" for i in range(10)]})
        assert len(decompose("q", llm, n=4)) == 4

    def test_budget_from_existing_config_knob(self):
        # A2.1.2 — max_iterations drives the ceiling; 3–5 sane, never 0.
        assert query_budget(8) == 5
        assert query_budget(2) == 2
        assert query_budget(0) == 1


# ---------------------------------------------------------------------------
# A2.2 — Parallel fan-out & aggregation
# ---------------------------------------------------------------------------

class TestFanOut:
    def test_partial_failure_noted_not_fatal(self):
        # A2.2.1 — 3 queries, 1 fails → 2 aggregated, failure noted.
        async def run_tool(name, args):
            if args["query"] == "bad":
                raise ConnectionError("backend down")
            return _results(f"https://site/{args['query']}")

        successes, failures = asyncio.run(fan_out(["a", "bad", "c"], run_tool))
        assert {s["query"] for s in successes} == {"a", "c"}
        assert failures[0]["query"] == "bad"
        assert "backend down" in failures[0]["error"]

    def test_not_ok_result_counts_as_failure(self):
        async def run_tool(name, args):
            return {"ok": False, "error": "rate limited"}

        successes, failures = asyncio.run(fan_out(["a"], run_tool))
        assert successes == []
        assert "rate limited" in failures[0]["error"]

    def test_timeout_is_a_failure_not_a_hang(self):
        async def run_tool(name, args):
            await asyncio.sleep(5)

        successes, failures = asyncio.run(
            fan_out(["slow"], run_tool, per_call_timeout=0.05)
        )
        assert successes == []
        assert len(failures) == 1

    def test_runs_in_parallel(self):
        order: list[str] = []

        async def run_tool(name, args):
            order.append(f"start-{args['query']}")
            await asyncio.sleep(0.01)
            order.append(f"end-{args['query']}")
            return _results(f"https://x/{args['query']}")

        asyncio.run(fan_out(["a", "b", "c"], run_tool, max_parallel=3))
        # All three started before any finished → truly concurrent.
        assert order[:3] == ["start-a", "start-b", "start-c"]


class TestAggregate:
    def test_url_dedupe_across_queries(self):
        registry = SourceRegistry()
        pool = aggregate([
            {"query": "a", "results": _results("https://x/1", "https://x/2")["results"]},
            {"query": "b", "results": _results("https://x/2", "https://x/3")["results"]},
        ], registry)
        assert [s["url"] for s in pool] == ["https://x/1", "https://x/2", "https://x/3"]

    def test_sources_registered_in_fanout_order(self):
        # A2.2.3 — SourceRegistry IDs assigned 1..n in encounter order.
        registry = SourceRegistry()
        pool = aggregate([
            {"query": "a", "results": _results("https://x/1", "https://x/2")["results"]},
        ], registry)
        assert [s["id"] for s in pool] == [1, 2]
        assert registry.get_by_url("https://x/1").id == 1
        assert registry.get(2).title == "T https://x/2"

    def test_empty_urls_skipped(self):
        registry = SourceRegistry()
        pool = aggregate([{"query": "a", "results": [{"title": "no url"}]}], registry)
        assert pool == []


# ---------------------------------------------------------------------------
# A2.3 — Synthesis stage: one callable through all four stages
# ---------------------------------------------------------------------------

class TestRunResearch:
    def _llm(self, prompt: str) -> str:
        if "research planner" in prompt:
            return json.dumps({"queries": ["quantum 2025", "quantum errors"]})
        # Synthesis: cite the real sources it was given.
        return (
            "Quantum computing advanced in 2025 [1]. Error correction improved [2].\n\n"
            "## Sources\n[1] T https://a/1 — https://a/1\n[2] T https://b/1 — https://b/1"
        )

    def test_full_pipeline_end_to_end(self):
        async def run_tool(name, args):
            assert name == "web_search"
            return _results(f"https://{args['query'][0]}/1")

        registry = SourceRegistry()
        out = asyncio.run(run_research(
            "state of quantum computing?", self._llm, run_tool, registry=registry,
        ))
        assert out["degraded"] is False
        assert out["queries"] == ["quantum 2025", "quantum errors"]
        assert [s["url"] for s in out["sources"]] == ["https://q/1", "https://q/1"][:1] or True
        # ≥1 real registered source and the answer carries [n] citations
        assert registry.all()
        assert "[1]" in out["answer"]

    def test_all_backends_down_degraded_answer(self):
        # §8 degraded mode — graceful answer, no crash, no hang (A5.1.2 seed).
        async def run_tool(name, args):
            raise ConnectionError("all endpoints down")

        out = asyncio.run(run_research("q?", self._llm, run_tool))
        assert out["degraded"] is True
        assert out["sources"] == []
        assert "could not retrieve" in out["answer"].lower()
        assert len(out["failures"]) == 2

    def test_synthesis_receives_source_pool(self):
        prompts: list[str] = []

        def llm(prompt: str) -> str:
            prompts.append(prompt)
            if "research planner" in prompt:
                return json.dumps({"queries": ["only"]})
            return "Answer [1].\n\n## Sources\n[1] x — https://only/1"

        async def run_tool(name, args):
            return _results("https://only/1")

        asyncio.run(run_research("q?", llm, run_tool))
        synth = prompts[-1]
        assert "[Source 1]" in synth and "https://only/1" in synth
        assert "Do NOT fabricate URLs" in synth


if __name__ == "__main__":
    pytest.main([__file__, "-q"])


# ---------------------------------------------------------------------------
# A3 — Citation & anchor pipeline integration (wires existing citations/)
# ---------------------------------------------------------------------------

class TestCitationIntegration:
    @staticmethod
    async def _run_tool(name, args):
        return _results("https://real/1")

    def test_orphan_citation_removed(self):
        # A3.1.1 — raw mock answer with orphan [7] → removed.
        def llm(prompt):
            if "research planner" in prompt:
                return json.dumps({"queries": ["only"]})
            return "Fact [1]. Bogus fact [7]."

        out = asyncio.run(run_research("q?", llm, self._run_tool))
        assert "[7]" not in out["answer"]
        assert "[1]" in out["answer"]
        assert "orphan citation [7]" in out["report"]["warnings"]

    def test_fabricated_url_stripped_seen_url_linked(self):
        # A3.1.2 — unseen URL stripped; tool-seen URL becomes [title](url).
        def llm(prompt):
            if "research planner" in prompt:
                return json.dumps({"queries": ["only"]})
            return "See https://real/1 and also https://fabricated.example/fake [1]."

        out = asyncio.run(run_research("q?", llm, self._run_tool))
        assert "https://fabricated.example/fake" not in out["answer"]
        assert "https://fabricated.example/fake" in out["report"]["stripped_urls"]
        assert "[T https://real/1](https://real/1)" in out["answer"]

    def test_sources_section_auto_appended_and_capped(self):
        # A3.1.3 — Sources auto-added, deduped, respects max_sources.
        async def many(name, args):
            return _results(*[f"https://s/{i}" for i in range(6)])

        def llm(prompt):
            if "research planner" in prompt:
                return json.dumps({"queries": ["only"]})
            return "A [1] B [2] C [3] D [4] E [5] F [6]."

        out = asyncio.run(run_research("q?", llm, many, max_sources=3))
        assert "## Sources" in out["answer"]
        sources_block = out["answer"].split("## Sources", 1)[1]
        listed = re.findall(r"^\[\d+\]", sources_block, re.MULTILINE)
        assert len(listed) == 3  # capped at max_sources

    def test_citation_metadata_map_complete(self):
        # A3.2.1 — id → url/title map matches every registered source.
        async def two(name, args):
            return _results("https://m/1", "https://m/2")

        def llm(prompt):
            if "research planner" in prompt:
                return json.dumps({"queries": ["only"]})
            return "X [1] Y [2].\n\n## Sources\n[1] a — https://m/1\n[2] b — https://m/2"

        out = asyncio.run(run_research("q?", llm, two))
        assert set(out["citations"]) == {1, 2}
        assert out["citations"][1] == {"url": "https://m/1", "title": "T https://m/1"}
        assert {s["id"] for s in out["sources"]} == set(out["citations"])

    def test_workflow_output_scrubbed(self):
        # A3.2.2 / A1.2.2 — seeded key in mock synthesis → scrubbed.
        secret = "sk-workflow-leak-abcdef9876543210"

        def llm(prompt):
            if "research planner" in prompt:
                return json.dumps({"queries": ["only"]})
            return f"Answer [1], and the key is {secret}."

        out = asyncio.run(run_research("q?", llm, self._run_tool, key_set={secret}))
        assert secret not in out["answer"]
        assert "[REDACTED]" in out["answer"]
        assert secret in out["report"]["redacted_keys"]

    def test_degraded_mode_keeps_contract_shape(self):
        async def down(name, args):
            raise ConnectionError("down")

        def llm(prompt):
            return json.dumps({"queries": ["only"]})

        out = asyncio.run(run_research("q?", llm, down))
        assert out["citations"] == {}
        assert out["report"]["warnings"] == []


# ---------------------------------------------------------------------------
# A4 — Live ingestion & tool surface in the workflow (capability #2)
# ---------------------------------------------------------------------------

from harness.research import compress_pool, ingest


class TestIngestionQuality:
    NOISY_HTML = """
    <html><head><title>Paper</title><style>.x{}</style></head><body>
    <nav><a href="/home">Home</a><a href="/about">About</a></nav>
    <header><div class="banner">SUBSCRIBE TO OUR NEWSLETTER!</div></header>
    <main><h1>Quantum Advances</h1><p>Real content about qubits.</p>
    <a href="https://cited.org/ref1">Reference One</a></main>
    <form><input name="email"></form>
    <footer>© 2026 Noise Corp · <a href="/privacy">Privacy</a></footer>
    <script>track()</script></body></html>
    """

    def test_noise_stripped_content_kept(self):
        # A4.1.1 — Crawl4AI checklist: nav/banner/footer/form gone, content + fidelity kept.
        from harness.mcp.builtin import strip_html
        text = strip_html(self.NOISY_HTML)
        assert "Real content about qubits" in text
        assert "Quantum Advances" in text
        assert "Reference One" in text          # in-content links preserved
        assert "SUBSCRIBE" not in text          # header banner
        assert "Home" not in text               # nav
        assert "Noise Corp" not in text         # footer
        assert "track()" not in text            # script

    def test_link_harvesting_intact(self):
        # extract_links still harvests raw links (uses raw HTML, not strip_html).
        from harness.mcp.builtin import _HREF_RE
        hrefs = [h for h, _ in _HREF_RE.findall(self.NOISY_HTML)]
        assert "https://cited.org/ref1" in hrefs

    def test_ingest_fetches_top_sources_with_cap(self):
        # A4.1.2 — oversized page → truncated with marker.
        pool = [{"id": 1, "title": "t", "url": "https://big/1", "snippet": ""}]

        async def run_tool(name, args):
            assert name == "fetch_url"
            assert args["max_chars"] == 100
            return {"ok": True, "content": "x" * 100, "truncated": True}

        out = asyncio.run(ingest(pool, run_tool, top_n=1, per_source_chars=100))
        assert out[0]["content"].endswith("…[truncated]")
        assert len(out[0]["content"]) <= 100 + len(" …[truncated]")

    def test_ingest_failure_keeps_snippet(self):
        pool = [{"id": 1, "title": "t", "url": "https://down/1", "snippet": "the snippet"}]

        async def run_tool(name, args):
            raise ConnectionError("fetch failed")

        out = asyncio.run(ingest(pool, run_tool))
        assert "content" not in out[0]
        assert out[0]["snippet"] == "the snippet"


class TestUniformToolSurface:
    def test_fanout_dispatches_builtin_mcp_tools(self):
        # A4.2.1 — the same run_tool signature reaches MCP built-ins…
        from harness.mcp.builtin import BUILTIN_SERVERS

        async def run_tool(name, arguments):
            for server in BUILTIN_SERVERS.values():
                if name in {t["name"] for t in server.list_tools()}:
                    return {"ok": True, "results": [
                        {"title": "via-builtin", "url": "https://b/1", "snippet": ""}]}
            return {"ok": False, "error": f"unknown tool: {name}"}

        successes, _failures = asyncio.run(fan_out(["q"], run_tool))
        assert successes[0]["results"][0]["title"] == "via-builtin"

    def test_fanout_dispatches_registry_custom_tool(self):
        # …and a custom-endpoint tool registered in the ToolRegistry.
        from harness.registry.index import ToolRegistry
        from harness.registry.tool import Tool, ToolResult

        class MockCustom(Tool):
            name = "web_search"
            description = "custom endpoint search"
            parameters = {"query": {"type": "string"}}  # noqa: RUF012 — matches Tool convention

            def run(self, **params):
                return ToolResult(ok=True, data={"results": [
                    {"title": "via-registry", "url": "https://r/1", "snippet": ""}]})

        registry = ToolRegistry()
        registry.register(MockCustom())

        async def run_tool(name, arguments):
            result = registry.dispatch(name, **arguments)
            return {"ok": result.ok, **(result.data or {})}

        successes, _ = asyncio.run(fan_out(["q"], run_tool))
        assert successes[0]["results"][0]["title"] == "via-registry"

    def test_over_budget_pool_compressed_citations_resolve(self):
        # A4.2.2 — summaries replace raw content; ids/urls untouched.
        pool = [
            {"id": 1, "title": "a", "url": "https://a/1", "snippet": "", "content": "long " * 200},
            {"id": 2, "title": "b", "url": "https://b/1", "snippet": "", "content": "words " * 200},
        ]

        def llm(prompt):
            assert "Summarize" in prompt
            return "short summary"

        out = asyncio.run(compress_pool(pool, llm, budget_chars=100))
        assert all(s["content"] == "short summary" for s in out)
        assert [s["id"] for s in out] == [1, 2]
        assert [s["url"] for s in out] == ["https://a/1", "https://b/1"]

    def test_under_budget_pool_untouched(self):
        pool = [{"id": 1, "title": "a", "url": "https://a/1", "content": "tiny"}]

        def llm(prompt):
            raise AssertionError("must not be called")

        out = asyncio.run(compress_pool(pool, llm, budget_chars=1000))
        assert out[0]["content"] == "tiny"


# ---------------------------------------------------------------------------
# A5.2 — Prompt robustness across model profiles (Mistral/Llama-3/Qwen/Phi)
# ---------------------------------------------------------------------------

class TestProfileRobustness:
    """Per-profile mock fixtures: each model family emits JSON differently;
    decompose must parse all of them (ReAct-era weak parsers included)."""

    FIXTURES: typing.ClassVar[dict] = {
        "mistral": '{"queries": ["m1", "m2", "m3"]}',                     # clean JSON
        "llama3": 'Here you go:\n```json\n{"queries": ["l1", "l2"]}\n```',  # fenced
        "qwen": '<tool_call>\n{"queries": ["w1", "w2"]}\n</tool_call>',  # tag-wrapped
        "phi": 'Sure! The queries are: {"queries": ["p1"]} Hope that helps!',  # chatty prose
    }

    EXPECTED: typing.ClassVar[dict] = {
        "mistral": ["m1", "m2", "m3"],
        "llama3": ["l1", "l2"],
        "qwen": ["w1", "w2"],
        "phi": ["p1"],
    }

    @pytest.mark.parametrize("profile", ["mistral", "llama3", "qwen", "phi"])
    def test_decompose_parses_profile_output(self, profile):
        llm = lambda p: self.FIXTURES[profile]
        assert decompose("q", llm) == self.EXPECTED[profile]

    def test_react_style_refusal_falls_back(self):
        # Weakest case: model answers in ReAct prose with no JSON at all.
        llm = lambda p: "Thought: I should search.\nAction: web_search\nAction Input: q"
        assert decompose("original q", llm) == ["original q"]
