from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.requirements import HiringRequirements


class CompletenessResult(BaseModel):
    """Result of checking whether a requirements object is ready for recommendations."""

    model_config = ConfigDict(extra="ignore")

    complete: bool
    missing_fields: list[str] = Field(default_factory=list)
    next_required_field: str | None = None
    reasoning: str


class RequirementCompletenessChecker:
    """Determines whether a requirements object has the minimum information needed for recommendations.

    This checker is intentionally limited to readiness assessment. It does not generate
    questions or suggest follow-up prompts.
    """

    def __init__(self) -> None:
        self._mandatory_fields = ["role", "seniority", "technical_skills"]

    def check(self, requirements: HiringRequirements) -> CompletenessResult:
        missing_fields = [field for field in self._mandatory_fields if not self._has_value(requirements, field)]

        if not missing_fields:
            return CompletenessResult(
                complete=True,
                missing_fields=[],
                next_required_field=None,
                reasoning="Requirements are complete: role, seniority, and technical skills are present.",
            )

        next_required_field = missing_fields[0]
        return CompletenessResult(
            complete=False,
            missing_fields=missing_fields,
            next_required_field=next_required_field,
            reasoning=(
                "Requirements are not yet ready for recommendations because the following mandatory "
                f"fields are missing: {', '.join(missing_fields)}."
            ),
        )

    def _has_value(self, requirements: HiringRequirements, field_name: str) -> bool:
        value = getattr(requirements, field_name)
        if field_name == "technical_skills":
            return bool(value)
        return bool(value)
