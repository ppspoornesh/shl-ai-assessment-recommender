from __future__ import annotations

from typing import Iterable

from app.models.chat import Message


class IntentDetector:
    """Lightweight rule-based detector for conversational intents."""

    def detect_intent(self, conversation: Iterable[Message]) -> str:
        messages = [message.content.lower() for message in conversation if message.role == "user"]
        if not messages:
            return "unknown"

        latest = messages[-1]

        if any(keyword in latest for keyword in ["compare", "comparison", "vs", "versus", "top two"]):
            return "compare_options"

        if any(keyword in latest for keyword in ["not sure", "unclear", "which", "what kind", "help me choose", "prefer"]):
            return "clarify_requirements"

        if any(keyword in latest for keyword in ["actually", "instead", "change", "refine", "update", "make it", "rather than"]):
            return "refine_request"

        if len(messages) > 1:
            return "refine_request"

        return "initial_request"
