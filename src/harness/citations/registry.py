# P5.T1 — SourceRegistry: assign sequential IDs, persist across turns, reference table
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Source:
    id: int
    title: str
    url: str
    tool_name: str
    turn: int
    content_preview: str = ""


class SourceRegistry:
    def __init__(self) -> None:
        self._sources: dict[int, Source] = {}
        self._url_map: dict[str, int] = {}
        self._next_id = 1

    def add(self, title: str, url: str, tool_name: str, turn: int, content_preview: str = "") -> int:
        if url in self._url_map:
            return self._url_map[url]
        sid = self._next_id
        self._next_id += 1
        src = Source(id=sid, title=title, url=url, tool_name=tool_name, turn=turn, content_preview=content_preview)
        self._sources[sid] = src
        self._url_map[url] = sid
        return sid

    def get(self, sid: int) -> Source | None:
        return self._sources.get(sid)

    def get_by_url(self, url: str) -> Source | None:
        sid = self._url_map.get(url)
        return self._sources.get(sid) if sid else None

    def reference_table(self) -> str:
        lines = []
        for src in self._sources.values():
            lines.append(f"[Source {src.id}] {src.title} | {src.url}")
        return "\n".join(lines)

    def clear(self) -> None:
        self._sources.clear()
        self._url_map.clear()
        self._next_id = 1

    def all(self) -> list[Source]:
        return list(self._sources.values())
