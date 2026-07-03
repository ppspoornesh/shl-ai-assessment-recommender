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
    """Scores candidates deterministically using configurable weighted attributes."""

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
                    explanation=self._build_explanation(candidate, score_breakdown, requirements),
                )
            )

        # Sort by score, then skills coverage, then role fit, then seniority, then name, then entity_id
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
            "purpose": self._score_purpose(candidate, requirements),
            "industry": self._score_industry(candidate, requirements),
            "language": self._score_language(candidate, requirements),
            "adaptive": self._score_adaptive(candidate, requirements),
        }
        return {
            name: round(self._weights[name] * breakdown[name], 2)
            for name in ["role", "skills", "competencies", "seniority", "duration", "remote", "purpose", "industry", "language", "adaptive"]
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

        known_skills = {"python", "sql", "excel", "java", "javascript", "typescript", "c++", "go", "rust", "ruby", "scala", "swift", "c#", "dotnet", "net"}

        skill_words = [w for w in role_words if w in known_skills]
        generic_words = [w for w in role_words if w not in known_skills]

        matched_skills = [w for w in skill_words if w in search_text]
        matched_generics = [w for w in generic_words if w in search_text]

        if not generic_words:
            if len(matched_skills) == len(skill_words):
                return 1.0
            elif matched_skills:
                return 0.6
            return 0.0

        if not skill_words:
            if len(matched_generics) == len(generic_words):
                return 1.0
            elif matched_generics:
                return 0.5
            return 0.0

        if matched_skills and matched_generics:
            return 0.85
        elif matched_skills:
            return 0.60
        elif matched_generics:
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

    def _score_purpose(self, candidate: CatalogEntry, requirements: HiringRequirements) -> float:
        if not requirements.assessment_purpose:
            return 0.0
        purpose = requirements.assessment_purpose.lower()
        search_text = self._build_search_text(candidate)

        if purpose == "development":
            if any(k in search_text for k in ["development", "training", "coaching", "upskilling", "360"]):
                return 1.0
        elif purpose in ["screening", "screening hiring", "hiring"]:
            if any(k in search_text for k in ["screening", "selection", "recruitment", "hiring", "pre-employment", "pre employment"]):
                return 1.0
        elif purpose in ["promotion", "internal mobility", "leadership succession"]:
            if any(k in search_text for k in ["promotion", "succession", "mobility", "potential", "transition"]):
                return 1.0
        elif purpose == "graduate hiring":
            if any("graduate" in level.lower() or "entry-level" in level.lower() for level in candidate.job_levels):
                return 1.0
        elif purpose == "executive hiring":
            if any("executive" in level.lower() or "director" in level.lower() for level in candidate.job_levels):
                return 1.0
        elif purpose == "safety critical":
            if "safety" in search_text or "critical" in search_text:
                return 1.0

        return 0.0

    def _score_industry(self, candidate: CatalogEntry, requirements: HiringRequirements) -> float:
        if not requirements.industry:
            return 0.0
        industry = requirements.industry.lower()
        search_text = self._build_search_text(candidate)
        if any(industry == ind.lower() for ind in candidate.target_industries) or industry in search_text:
            return 1.0
        return 0.0

    def _score_language(self, candidate: CatalogEntry, requirements: HiringRequirements) -> float:
        if not requirements.preferred_languages:
            return 0.0
        search_text = self._build_search_text(candidate)
        cand_langs = [l.lower() for l in candidate.languages] if candidate.languages else []
        for lang in requirements.preferred_languages:
            lang_lower = lang.lower()
            if lang_lower in cand_langs or lang_lower in search_text:
                return 1.0
        return 0.0

    def _score_adaptive(self, candidate: CatalogEntry, requirements: HiringRequirements) -> float:
        if candidate.adaptive and candidate.adaptive.lower() in ["yes", "true", "y"]:
            return 1.0
        return 0.0

    def _build_explanation(self, candidate: CatalogEntry, score_breakdown: dict[str, float], requirements: HiringRequirements) -> str:
        from app.services.candidate_retriever import TECH_FALLBACKS

        # Check for fallback alternative description overrides
        for skill in requirements.technical_skills:
            skill_lower = skill.lower()
            if skill_lower in TECH_FALLBACKS:
                fb = TECH_FALLBACKS[skill_lower]
                if candidate.name in fb["alternatives"]:
                    return fb["reason"]

        labels = {
            "role": "role fit",
            "skills": "technical skill coverage",
            "competencies": "competency alignment",
            "seniority": "seniority match",
            "duration": "available duration",
            "remote": "delivery preference",
            "purpose": "assessment purpose fit",
            "industry": "industry sector alignment",
            "language": "preferred language support",
            "adaptive": "adaptive testing format",
        }
        parts = [labels[name] for name, value in score_breakdown.items() if value > 0 and name in labels]
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
        # Keeps custom weights passed in unit tests intact
        normalized = {
            "role": weights.get("role", 0.0),
            "skills": weights.get("skills", 0.0),
            "competencies": weights.get("competencies", 0.0),
            "seniority": weights.get("seniority", 0.0),
            "duration": weights.get("duration", 0.0),
            "remote": weights.get("remote", 0.0),
            "purpose": weights.get("purpose", 0.0),
            "industry": weights.get("industry", 0.0),
            "language": weights.get("language", 0.0),
            "adaptive": weights.get("adaptive", 0.0),
        }
        total = sum(normalized.values())
        if total <= 0:
            raise ValueError("Ranking weights must sum to a positive value.")
        return normalized

    def _default_weights(self) -> dict[str, float]:
        return {
            "role": 0.20,
            "skills": 0.25,
            "competencies": 0.10,
            "seniority": 0.10,
            "duration": 0.05,
            "remote": 0.05,
            "purpose": 0.10,
            "industry": 0.05,
            "language": 0.05,
            "adaptive": 0.05,
        }
