# P2.T5 — Hot-reload watcher (polling ≤5s, atomic swap)
from __future__ import annotations

import hashlib
import threading
from pathlib import Path


class HotReloadWatcher:
    def __init__(self, path: str | Path, callback, interval: float = 2.0):
        self.path = Path(path)
        self.callback = callback
        self.interval = interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._last_hash = ""

    def start(self) -> None:
        self._last_hash = self._hash()
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=self.interval * 2)

    def _hash(self) -> str:
        try:
            return hashlib.md5(self.path.read_bytes()).hexdigest()
        except Exception:
            return ""

    def _run(self) -> None:
        while not self._stop.is_set():
            import time

            time.sleep(self.interval)
            h = self._hash()
            if h and h != self._last_hash:
                self._last_hash = h
                try:
                    self.callback()
                except Exception:
                    pass
