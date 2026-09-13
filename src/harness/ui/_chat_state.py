"""Chat session store (shown in the sidebar's session history).

Sessions persist in .harness-state.json (section 'chat_sessions') so the
sidebar history survives server restarts — same guarantee as the provider
config (bugfix.json BF-012).
"""
from __future__ import annotations

import time
import uuid

from harness.ui._ai_state import load_section, persist_section

MAX_SESSIONS = 50
MAX_MESSAGES_PER_SESSION = 200

_SESSION_SECTION = "chat_sessions"

_sessions: list[dict] = []


def _load_sessions() -> None:
    saved = load_section(_SESSION_SECTION)
    if isinstance(saved, list):
        _sessions.extend(s for s in saved if isinstance(s, dict) and s.get("id"))


def _persist_sessions() -> None:
    persist_section(_SESSION_SECTION, _sessions)


_load_sessions()


def create_session(title: str = "") -> dict:
    session = {
        "id": uuid.uuid4().hex[:12],
        "title": (title or "New session").strip()[:60] or "New session",
        "created": time.time(),
        "updated": time.time(),
        "messages": [],
    }
    _sessions.insert(0, session)
    if len(_sessions) > MAX_SESSIONS:
        _sessions.pop()
    _persist_sessions()
    return session


def get_session(session_id: str) -> dict | None:
    for s in _sessions:
        if s["id"] == session_id:
            return s
    return None


def list_sessions() -> list[dict]:
    out = [
        {
            "id": s["id"],
            "title": s["title"],
            "created": s["created"],
            "updated": s["updated"],
            "message_count": len(s["messages"]),
        }
        for s in _sessions
    ]
    out.sort(key=lambda x: x["updated"], reverse=True)
    return out


def delete_session(session_id: str) -> bool:
    for i, s in enumerate(_sessions):
        if s["id"] == session_id:
            _sessions.pop(i)
            _persist_sessions()
            return True
    return False


def append_message(session: dict, message: dict) -> None:
    session["messages"].append(message)
    session["updated"] = time.time()
    if len(session["messages"]) > MAX_MESSAGES_PER_SESSION:
        session["messages"] = session["messages"][-MAX_MESSAGES_PER_SESSION:]
    _persist_sessions()
