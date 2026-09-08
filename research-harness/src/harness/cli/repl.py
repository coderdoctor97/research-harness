"""Interactive CLI REPL for the harness."""

from __future__ import annotations

import asyncio
import logging
import sys

from harness.config import HarnessConfig, load_config
from harness.llm.client import LLMClient
from harness.llm.exceptions import LLMConnectionError, LLMResponseError

logger = logging.getLogger(__name__)


def _print_banner() -> None:
    print("Local LLM Research Harness — type your question, /quit to exit.")


async def _run_repl(cfg: HarnessConfig) -> None:
    async with LLMClient(
        base_url=cfg.base_url,
        model_name=cfg.model_name,
        api_key=cfg.api_key,
        timeout=cfg.timeout,
    ) as client:
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

            messages = [{"role": "user", "content": user_input}]
            try:
                response = await client.chat(messages)
            except LLMConnectionError as exc:
                print(f"[connection error] {exc}")
                continue
            except LLMResponseError as exc:
                print(f"[server error] {exc}")
                continue
            print(response)


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
