from __future__ import annotations

import re


class PromptGuard:
    """Rejects obvious prompt injection and instruction override attempts.

    This component is intentionally limited to safety screening. It does not perform
    business logic, retrieval, ranking, or response generation.
    """

    def __init__(self) -> None:
        self._patterns = [
            r"ignore\s+previous\s+instructions",
            r"forget\s+(?:all\s+)?(?:previous|prior)\s+instructions",
            r"override\s+(?:the\s+)?(?:system|developer|previous)\s+instructions",
            r"system\s+prompt",
            r"developer\s+message",
            r"reveal\s+the\s+prompt",
            r"jailbreak",
            r"act\s+as",
            r"you\s+are\s+now",
        ]

    def check(self, text: str) -> bool:
        if not text or not text.strip():
            return False
        normalized = text.lower()
        return not any(re.search(pattern, normalized) for pattern in self._patterns)

    def is_safe(self, text: str) -> bool:
        return self.check(text)
