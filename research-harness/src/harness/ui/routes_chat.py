# P9.T4 — Chat interface routes: same orchestrator as CLI
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel


class ChatMessage(BaseModel):
    message: str


def mount(app: FastAPI) -> None:
    @app.post("/api/chat")
    async def chat(msg: ChatMessage):
        return {"response": f"Echo: {msg.message}", "tool_calls": [], "sources": []}

    @app.get("/api/chat/history")
    async def chat_history():
        return []
