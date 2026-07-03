from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.models.catalog import CatalogEntry
from app.models.requirements import HiringRequirements


class RankedCandidate(BaseModel):
    """A candidate assessment with a deterministic weighted score and explanation."""

    model_config = ConfigDict(extra="ignore")

    entity_id: str
    name: str
    score: float
    link: str | None = None
    description: str | None = None
    duration: str | None = None
    job_levels: list[str] = Field(default_factory=list)
    keys: list[str] = Field(default_factory=list)
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    explanation: str


class RankingEngine:
    """Scores candidates deterministically using configurable weighted attributes.

    This component does not retrieve candidates or generate recommendations. It only
    evaluates an existing candidate set against the current requirements.
    """

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self._weights = self._normalize_weights(weights or self._default_weights())

    def rank(self, candidates: list[CatalogEntry], requirements: HiringRequirements) -> list[RankedCandidate]:
        ranked = []
        for candidate in candidates:
            score_breakdown = self._score_candidate(candidate, requirements)
            total_score = round(sum(score_breakdown.values()), 2)
            ranked.append(
                RankedCandidate(
                    entity_id=candidate.entity_id,
                    name=candidate.name,
                    score=total_score,
                    link=str(candidate.link),
                    description=candidate.description,
                    duration=candidate.duration,
                    job_levels=candidate.job_levels,
                    keys=candidate.keys,
                    score_breakdown=score_breakdown,
                    explanation=self._build_explanation(candidate, score_breakdown),
                )
            )

        return sorted(
            ranked,
            key=lambda item: (
                -item.score,
                -item.score_breakdown.get("skills", 0.0),
                -item.score_breakdown.get("role", 0.0),
                -item.score_breakdown.get("seniority", 0.0),
                item.name.lower(),
                item.entity_id,
            ),
        )

    def _score_candidate(self, candidate: CatalogEntry, requirements: HiringRequirements) -> dict[str, float]:
        breakdown = {
            "role": self._score_role(candidate, requirements),
            "skills": self._score_skills(candidate, requirements),
            "competencies": self._score_competencies(candidate, requirements),
            "seniority": self._score_seniority(candidate, requirements),
            "duration": self._score_duration(candidate, requirements),
            "remote": self._score_remote(candidate, requirements),
        }
        return {
            name: round(self._weights[name] * breakdown[name], 2)
            for name in ["role", "skills", "competencies", "seniority", "duration", "remote"]
        }

    def _score_role(self, candidate: CatalogEntry, requirements: HiringRequirements) -> float:
        if not requirements.role:
            return 0.0
        search_text = self._build_search_text(candidate)
        normalized_role = requirements.role.lower()
        candidate_name = candidate.name.lower()
        primary_function = (candidate.primary_function or "").lower()

        # 1. Exact substring match in name or primary function
        if normalized_role in candidate_name or normalized_role in primary_function:
            return 1.0

        # 2. Analyze individual terms in the role
        role_words = [w for w in normalized_role.split() if len(w) > 2]
        if not role_words:
            return 0.0

        # Classify words in the role
        known_skills = {"python", "sql", "excel", "java", "javascript", "typescript", "c++", "go", "rust", "ruby", "scala", "swift", "c#", "dotnet", "net"}

        skill_words = [w for w in role_words if w in known_skills]
        generic_words = [w for w in role_words if w not in known_skills]

        # Check matches in search_text
        matched_skills = [w for w in skill_words if w in search_text]
        matched_generics = [w for w in generic_words if w in search_text]

        # If the role only has skill words
        if not generic_words:
            if len(matched_skills) == len(skill_words):
                return 1.0
            elif matched_skills:
                return 0.6
            return 0.0

        # If the role only has generic/other words
        if not skill_words:
            if len(matched_generics) == len(generic_words):
                return 1.0
            elif matched_generics:
                return 0.5
            return 0.0

        # If the role has both skill words and generic words (e.g. "java developer")
        if matched_skills and matched_generics:
            return 0.85
        elif matched_skills:
            # Matches technology but not the generic role (e.g. "Core Java" for "Java Developer")
            return 0.60
        elif matched_generics:
            # Matches generic role but not the technology (e.g. "ASP.NET Developer" for "Java Developer")
            # This is a generic match but wrong tech, so rank it very low!
            return 0.10

        return 0.0

    def _score_skills(self, candidate: CatalogEntry, requirements: HiringRequirements) -> float:
        if not requirements.technical_skills:
            return 0.0
        candidate_skills = {skill.lower() for skill in candidate.skills}
        search_text = self._build_search_text(candidate)
        requested_skills = [skill.lower() for skill in requirements.technical_skills if skill.strip()]
        if not requested_skills:
            return 0.0

        overlaps = [
            skill
            for skill in requested_skills
            if skill in candidate_skills or skill in search_text
        ]
        if not overlaps:
            return 0.0
        return len(set(overlaps)) / len(set(requested_skills))

    def _score_competencies(self, candidate: CatalogEntry, requirements: HiringRequirements) -> float:
        if not requirements.competencies:
            return 0.0
        candidate_competencies = {competency.lower() for competency in candidate.competencies}
        search_text = self._build_search_text(candidate)
        overlaps = [
            competency
            for competency in requirements.competencies
            if competency.lower() in candidate_competencies or competency.lower() in search_text
        ]
        if not overlaps:
            return 0.0
        return 1.0

    def _score_seniority(self, candidate: CatalogEntry, requirements: HiringRequirements) -> float:
        if not requirements.seniority:
            return 0.0
        normalized_seniority = requirements.seniority.lower()
        for level in candidate.job_levels:
            if normalized_seniority in level.lower():
                return 1.0
        return 0.0

    def _score_duration(self, candidate: CatalogEntry, requirements: HiringRequirements) -> float:
        if candidate.duration:
            return 1.0
        return 0.0

    def _score_remote(self, candidate: CatalogEntry, requirements: HiringRequirements) -> float:
        if requirements.remote is None:
            return 0.0
        return 1.0

    def _build_explanation(self, candidate: CatalogEntry, score_breakdown: dict[str, float]) -> str:
        labels = {
            "role": "role fit",
            "skills": "technical skill coverage",
            "competencies": "competency alignment",
            "seniority": "seniority match",
            "duration": "available duration",
            "remote": "delivery preference",
        }
        parts = [labels[name] for name, value in score_breakdown.items() if value > 0]
        if not parts:
            return "No strong match signals were found for this assessment."
        return f"{candidate.name} matched on {self._format_list(parts)}."

    def _format_list(self, values: list[str]) -> str:
        if len(values) == 1:
            return values[0]
        if len(values) == 2:
            return f"{values[0]} and {values[1]}"
        return ", ".join(values[:-1]) + f", and {values[-1]}"

    def _build_search_text(self, candidate: CatalogEntry) -> str:
        parts = [
            candidate.name,
            candidate.description,
            candidate.primary_function or "",
            " ".join(candidate.skills),
            " ".join(candidate.competencies),
            " ".join(candidate.keys),
        ]
        return " ".join(part for part in parts if part).lower()

    def _normalize_weights(self, weights: dict[str, float]) -> dict[str, float]:
        normalized = {
            "role": weights.get("role", 0.35),
            "skills": weights.get("skills", 0.40),
            "competencies": weights.get("competencies", 0.1),
            "seniority": weights.get("seniority", 0.1),
            "duration": weights.get("duration", 0.05),
            "remote": weights.get("remote", 0.0),
        }
        total = sum(normalized.values())
        if total <= 0:
            raise ValueError("Ranking weights must sum to a positive value.")
        return normalized

    def _default_weights(self) -> dict[str, float]:
        return {
            "role": float(getattr(settings, "ranking_role_weight", 0.35)),
            "skills": float(getattr(settings, "ranking_skills_weight", 0.40)),
            "competencies": float(getattr(settings, "ranking_competencies_weight", 0.10)),
            "seniority": float(getattr(settings, "ranking_seniority_weight", 0.10)),
            "duration": float(getattr(settings, "ranking_duration_weight", 0.05)),
            "remote": float(getattr(settings, "ranking_remote_weight", 0.00)),
        }
