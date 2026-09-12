# P4.T2 — Loop state machine (§4 Steps 1–7)
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from harness.loop.parser import classify, CallType, ToolCall


@dataclass
class LoopState:
    messages: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 8
    strike_count: int = 0
    done: bool = False
    final_answer: str = ""

    def step(self, response_text: str) -> dict:
        """Process one model response; return event dict."""
        ctype, payload = classify(response_text)
        if ctype == CallType.FINAL_ANSWER:
            self.done = True
            self.final_answer = payload if isinstance(payload, str) else ""
            return {"type": "final_answer", "text": self.final_answer}
        if ctype == CallType.TOOL_CALL:
            tc = payload
            if self.iteration >= self.max_iterations:
                return {"type": "force_final", "text": response_text}
            self.iteration += 1
            return {"type": "tool_call", "name": tc.name, "arguments": tc.arguments}
        self.strike_count += 1
        if self.strike_count >= 5:
            self.done = True
            return {"type": "tools_off", "text": "I cannot answer with the available tools."}
        return {"type": "malformed", "strikes": self.strike_count}
