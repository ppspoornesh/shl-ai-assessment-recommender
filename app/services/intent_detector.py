from __future__ import annotations

from typing import Iterable

from app.models.chat import Message


class IntentDetector:
    """Lightweight rule-based detector for conversational intents."""

    def detect_intent(self, conversation: Iterable[Message]) -> str:
        messages = [message.content.lower().strip() for message in conversation if message.role == "user"]
        if not messages:
            return "unknown"

        latest = messages[-1]

        # 1. Greeting
        if any(latest.startswith(kw) or latest == kw for kw in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]):
            if len(latest.split()) < 4:
                return "greeting"

        # 2. Compare options
        if any(keyword in latest for keyword in ["compare", "comparison", "vs", "versus", "top two", "differences between"]):
            return "compare_options"

        # 3. Assessment battery request
        if any(keyword in latest for keyword in ["battery", "batteries", "suite", "package", "bundle", "technical + personality", "personality + technical"]):
            return "assessment_battery_request"

        # 4. Development request
        if any(keyword in latest for keyword in ["development", "training", "grow", "coaching", "upskilling", "learn"]):
            return "development_request"

        # 5. Promotion request
        if any(keyword in latest for keyword in ["promotion", "promote", "successor", "succession"]):
            return "promotion_request"

        # 6. Clarification response
        if any(keyword in latest for keyword in ["not sure", "unclear", "which", "what kind", "help me choose", "prefer"]):
            return "clarify_requirements"

        # 7. Refinement
        if any(keyword in latest for keyword in ["actually", "instead", "change", "refine", "update", "make it", "rather than"]):
            return "refine_request"

        if len(messages) > 1:
            return "refine_request"

        return "initial_request"
