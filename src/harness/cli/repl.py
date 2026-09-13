"""Interactive CLI REPL for the harness."""

from __future__ import annotations

import asyncio
import logging
import sys

from harness.config import HarnessConfig, load_config
from harness.llm.client import LLMClient, LLMConnectionError, LLMResponseError
from harness.loop.agent import run_chat_stream
from harness.mcp.builtin import builtin_tool_registry
from harness.registry.index import ToolRegistry

logger = logging.getLogger(__name__)


def _print_banner() -> None:
    print("Local LLM Research Harness — type your question, /quit to exit.")


async def _print_streaming_response(client: LLMClient, registry: ToolRegistry, prompt: str) -> None:
    streamed = False
    final_text = ""
    async for event in run_chat_stream(client, registry, prompt):
        if event["type"] == "token":
            streamed = True
            print(event["text"], end="", flush=True)
        elif event["type"] == "final":
            final_text = event.get("response", "")
    if not streamed and final_text:
        print(final_text, end="", flush=True)
    print()


async def _run_repl(cfg: HarnessConfig) -> None:
    client = LLMClient(
        base_url=cfg.base_url,
        model_name=cfg.model_name,
        api_key=cfg.api_key,
        timeout=cfg.timeout,
    )
    registry = builtin_tool_registry()
    _print_banner()
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return

        if not user_input:
            continue
        if user_input.lower() in ("/quit", "/exit", "/q"):
            print("Bye.")
            return

        try:
            await _print_streaming_response(client, registry, user_input)
        except LLMConnectionError as exc:
            print(f"[connection error] {exc}")
        except LLMResponseError as exc:
            print(f"[server error] {exc}")


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI."""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    cfg = load_config()
    try:
        asyncio.run(_run_repl(cfg))
    except Exception as exc:  # noqa: BLE001
        print(f"[fatal] {exc}", file=sys.stderr)
        return 1
    return 0
