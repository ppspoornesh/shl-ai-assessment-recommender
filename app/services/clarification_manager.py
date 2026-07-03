from __future__ import annotations

from app.services.requirement_completeness_checker import CompletenessResult


class ClarificationManager:
    """Builds a single, concise clarification question from completeness results.

    This component is intentionally limited to question generation. It does not decide
    recommendation eligibility or modify requirements.
    """

    def build_question(self, completeness_result: CompletenessResult) -> str | None:
        if completeness_result.complete:
            return None

        field = completeness_result.next_required_field or (completeness_result.missing_fields[0] if completeness_result.missing_fields else None)
        if not field:
            return None

        templates = {
            "role": "What role are you targeting?",
            "seniority": "What seniority level are you targeting?",
            "technical_skills": "Which technical skills are required for this role?",
        }

        return templates.get(field)
