# P6.T4 — Document cache: in-memory + filesystem, TTL, instant re-serve
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any


class DocumentCache:
    def __init__(self, cache_dir: str = ".cache/documents", ttl: int = 3600) -> None:
        self._mem: dict[str, tuple[float, dict]] = {}
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl

    def _key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    def get(self, url: str) -> dict | None:
        k = self._key(url)
        if k in self._mem:
            ts, data = self._mem[k]
            if time.time() - ts > self.ttl:
                del self._mem[k]
                return None
            return data
        fp = self.cache_dir / f"{k}.json"
        if fp.is_file():
            try:
                data = json.loads(fp.read_text())
                ts = data.get("_ts", 0)
                if time.time() - ts > self.ttl:
                    fp.unlink(missing_ok=True)
                    return None
                return data
            except Exception:
                return None
        return None

    def set(self, url: str, data: dict) -> None:
        k = self._key(url)
        data["_ts"] = time.time()
        self._mem[k] = (data["_ts"], data)
        fp = self.cache_dir / f"{k}.json"
        try:
            fp.write_text(json.dumps(data))
        except Exception:
            pass

    def clear(self) -> None:
        self._mem.clear()
        for fp in self.cache_dir.glob("*.json"):
            fp.unlink(missing_ok=True)
