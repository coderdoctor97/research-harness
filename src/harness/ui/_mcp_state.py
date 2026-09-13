"""Shared in-memory state for MCP servers (used by routes_mcp and routes_config).

Seeded with the built-in FREE services so browsing works out of the box:
  - builtin-fetcher : endpoint fetcher (fetch_url, extract_links)
  - builtin-search  : DuckDuckGo web search (web_search)
Manual/command-based servers can be added on top (optional).
"""
from __future__ import annotations

from harness.mcp.builtin import server_entries

_mcp_servers: list[dict] = server_entries()


def restore_defaults() -> None:
    """Re-add any missing built-in servers."""
    existing = {s.get("name") for s in _mcp_servers}
    for entry in server_entries():
        if entry["name"] not in existing:
            _mcp_servers.append(entry)
