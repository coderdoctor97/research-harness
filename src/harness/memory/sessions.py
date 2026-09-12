# P6.T6 — Session persistence + SourceRegistry persistence + 20-turn stress test
from __future__ import annotations

import json
import time
from pathlib import Path
from harness.citations.registry import SourceRegistry, Source


class Session:
    def __init__(self, session_id: str, registry: SourceRegistry) -> None:
        self.session_id = session_id
        self.registry = registry
        self.history: list[dict] = []
        self.summary: str = ""
        self.created_at = time.time()
        self.turn_count = 0

    def add_turn(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content, "turn": self.turn_count})
        self.turn_count += 1

    def save(self, path: str | Path) -> None:
        data = {
            "session_id": self.session_id,
            "history": self.history,
            "summary": self.summary,
            "turn_count": self.turn_count,
            "created_at": self.created_at,
            "sources": [
                {"id": s.id, "title": s.title, "url": s.url, "tool_name": s.tool_name, "turn": s.turn}
                for s in self.registry.all()
            ],
        }
        Path(path).write_text(json.dumps(data))

    @classmethod
    def load(cls, path: str | Path) -> "Session":
        data = json.loads(Path(path).read_text())
        reg = SourceRegistry()
        for s in data.get("sources", []):
            src = Source(id=s["id"], title=s["title"], url=s["url"], tool_name=s["tool_name"], turn=s["turn"])
            reg._sources[s["id"]] = src
            reg._url_map[s["url"]] = s["id"]
            reg._next_id = max(reg._next_id, s["id"] + 1)
        sess = cls(data["session_id"], reg)
        sess.history = data.get("history", [])
        sess.summary = data.get("summary", "")
        sess.turn_count = data.get("turn_count", 0)
        sess.created_at = data.get("created_at", time.time())
        return sess
