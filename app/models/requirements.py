from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HiringRequirements(BaseModel):
    """Strongly typed structure for hiring requirements extracted from conversation history."""

    model_config = ConfigDict(extra="ignore")

    role: str | None = None
    seniority: str | None = None
    years_of_experience: int | None = None
    technical_skills: list[str] = Field(default_factory=list)
    competencies: list[str] = Field(default_factory=list)
    personality_traits: list[str] = Field(default_factory=list)
    industry: str | None = None
    preferred_languages: list[str] = Field(default_factory=list)
    duration_limit: str | None = None
    remote: bool | None = None
    additional_constraints: list[str] = Field(default_factory=list)

    def merge(self, other: HiringRequirements) -> HiringRequirements:
        """Return a new requirements object by merging another into this one."""
        merged = self.model_copy(deep=True)

        if other.role:
            merged.role = other.role

        if other.seniority:
            merged.seniority = other.seniority

        if other.years_of_experience is not None:
            merged.years_of_experience = other.years_of_experience

        merged.technical_skills = self._merge_unique(merged.technical_skills, other.technical_skills)
        merged.competencies = self._merge_unique(merged.competencies, other.competencies)
        merged.personality_traits = self._merge_unique(merged.personality_traits, other.personality_traits)
        merged.preferred_languages = self._merge_unique(merged.preferred_languages, other.preferred_languages)
        merged.additional_constraints = self._merge_unique(merged.additional_constraints, other.additional_constraints)

        if other.industry:
            merged.industry = other.industry

        if other.duration_limit:
            merged.duration_limit = other.duration_limit

        if other.remote is not None:
            merged.remote = other.remote

        return merged

    @staticmethod
    def _merge_unique(existing: list[str], additions: list[str]) -> list[str]:
        combined = existing.copy()
        for item in additions:
            normalized = item.strip()
            if normalized and normalized not in combined:
                combined.append(normalized)
        return combined


class ExtractionResult(BaseModel):
    """Structured output for a requirement extraction pass."""

    model_config = ConfigDict(extra="ignore")

    requirements: HiringRequirements
    confidence: float
    missing_fields: list[str] = Field(default_factory=list)
    extracted_entities: list[str] = Field(default_factory=list)
