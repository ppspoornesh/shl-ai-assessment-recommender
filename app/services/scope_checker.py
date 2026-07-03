from __future__ import annotations

import re


class ScopeChecker:
    """Rejects requests that fall outside the assessment-recommendation domain.

    This component is intentionally limited to scope validation. It does not retrieve,
    rank, or generate recommendations.
    """

    def __init__(self) -> None:
        self._allowed_terms = [
            "assessment",
            "assessments",
            "test",
            "tests",
            "shl",
            "recommend",
            "recommendation",
            "candidate",
            "role",
            "seniority",
            "skills",
            "hiring",
            "job",
            "position",
            "talent",
            "match",
            "compare",
            "comparison",
            "aptitude",
            "psychometric",
            "screening",
            "interview",
            "engineer",
            "developer",
            "analyst",
            "manager",
            "director",
            "consultant",
            "python",
            "sql",
            "excel",
            "java",
            "javascript",
            "hello",
            "hi",
            "hey",
            "greetings",
        ]
        self._blocked_terms = [
            "poem",
            "recipe",
            "weather",
            "travel",
            "history",
            "physics",
            "song",
        ]

    def check(self, text: str) -> bool:
        if not text or not text.strip():
            return False
        normalized = text.lower()
        if any(term in normalized for term in self._blocked_terms):
            return False
        return any(term in normalized for term in self._allowed_terms)

    def is_in_scope(self, text: str) -> bool:
        return self.check(text)
