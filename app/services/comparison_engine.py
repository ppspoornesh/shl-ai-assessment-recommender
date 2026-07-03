from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.catalog import CatalogEntry


class ComparisonResult(BaseModel):
    """Structured metadata comparison for a set of catalog assessments.

    Includes recruiter-friendly insights (use cases, tradeoffs, guidance).
    """

    model_config = ConfigDict(extra="ignore")

    common_features: list[str] = Field(default_factory=list)
    differences: list[str] = Field(default_factory=list)
    durations: list[str] = Field(default_factory=list)
    job_levels: list[list[str]] = Field(default_factory=list)
    competencies: list[list[str]] = Field(default_factory=list)
    languages: list[list[str]] = Field(default_factory=list)
    adaptive_support: list[str] = Field(default_factory=list)
    remote_support: list[str] = Field(default_factory=list)

    # Recruiter extensions
    use_cases: list[str] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)
    recommendation_guidance: str | None = None


class ComparisonEngine:
    """Compares catalog assessments using only structured metadata."""

    def compare(self, assessments: list[CatalogEntry]) -> ComparisonResult:
        if len(assessments) < 2:
            return ComparisonResult()

        common_features = self._common_features(assessments)
        differences = self._differences(assessments)

        # Compute use cases and tradeoffs
        use_cases = []
        tradeoffs = []

        for assessment in assessments:
            keys_lower = [k.lower() for k in assessment.keys]
            name_lower = assessment.name.lower()
            description_lower = (assessment.description or "").lower()

            if "simulation" in keys_lower or "simulations" in keys_lower or "automata" in name_lower:
                use_cases.append(f"{assessment.name}: Best for hands-on programming and practical coding troubleshooting.")
                tradeoffs.append(f"{assessment.name}: Offers high fidelity and realistic skill measurement, but has a higher candidate completion effort.")
            elif "verify" in name_lower or any(k in name_lower for k in ["numerical", "deductive", "inductive", "ability"]):
                use_cases.append(f"{assessment.name}: Best for high-volume screening to verify cognitive aptitude and reasoning speed.")
                tradeoffs.append(f"{assessment.name}: Highly predictive of general performance, but does not evaluate specific technical framework skills.")
            elif "opq" in name_lower or "personality" in name_lower or "behavior" in name_lower:
                use_cases.append(f"{assessment.name}: Best for evaluating working styles, collaboration, and culture fit within the team.")
                tradeoffs.append(f"{assessment.name}: Provides deep behavioral insights, but relies on self-reported questionnaire format.")
            elif any("executive" in lvl.lower() or "manager" in lvl.lower() for lvl in assessment.job_levels):
                use_cases.append(f"{assessment.name}: Best for leadership, strategic execution, and management capability validation.")
                tradeoffs.append(f"{assessment.name}: Highly tailored to senior decision-making contexts, but less applicable to individual contributor screening.")
            else:
                use_cases.append(f"{assessment.name}: Best for standardized domain knowledge verification and technical screening.")
                tradeoffs.append(f"{assessment.name}: Short and objective format, but does not capture practical hands-on application.")

        # Compute recommendation guidance
        names = [a.name for a in assessments]
        guidance = (
            f"Choose {names[0]} if you want to prioritize direct evaluation of specific competencies or programming knowledge. "
            f"Opt for {names[1]} if you are seeking a broader or alternative skill verification format. "
            f"For critical hires, we recommend combining them into a unified battery (using one for technical screening and the other for behavioral or general ability fit)."
        )

        return ComparisonResult(
            common_features=common_features,
            differences=differences,
            durations=[assessment.duration or "" for assessment in assessments],
            job_levels=[assessment.job_levels for assessment in assessments],
            competencies=[assessment.competencies for assessment in assessments],
            languages=[self._extract_languages(assessment) for assessment in assessments],
            adaptive_support=[self._extract_field(assessment, "adaptive") for assessment in assessments],
            remote_support=[self._extract_field(assessment, "remote") for assessment in assessments],
            use_cases=use_cases,
            tradeoffs=tradeoffs,
            recommendation_guidance=guidance,
        )

    def _common_features(self, assessments: list[CatalogEntry]) -> list[str]:
        if not assessments:
            return []

        seen: set[str] = set()
        feature_order: list[str] = []
        counts: dict[str, int] = {}

        for assessment in assessments:
            for feature in self._assessment_feature_sequence(assessment):
                normalized = feature.lower().strip()
                if not normalized:
                    continue
                if normalized not in seen:
                    seen.add(normalized)
                    feature_order.append(normalized)
                counts[normalized] = counts.get(normalized, 0) + 1

        return [feature for feature in feature_order if counts.get(feature, 0) >= 2]

    def _assessment_feature_sequence(self, assessment: CatalogEntry) -> list[str]:
        return [*self._normalize_values(assessment.skills), *self._normalize_values(assessment.competencies)]

    def _differences(self, assessments: list[CatalogEntry]) -> list[str]:
        differences: list[str] = []
        if len(assessments) >= 2:
            first = assessments[0]
            second = assessments[1]
            first_skills = self._normalize_values(first.skills)
            second_skills = self._normalize_values(second.skills)
            first_competencies = self._normalize_values(first.competencies)
            second_competencies = self._normalize_values(second.competencies)
            first_levels = self._normalize_values(first.job_levels)
            second_levels = self._normalize_values(second.job_levels)

            first_skill_diff = sorted(set(first_skills) - set(second_skills))
            second_skill_diff = sorted(set(second_skills) - set(first_skills))
            if first_skill_diff or second_skill_diff:
                differences.append(f"{', '.join(first_skill_diff) or 'no unique skills'} vs {', '.join(second_skill_diff) or 'no unique skills'}")

            if first.duration != second.duration:
                differences.append(f"{first.duration or 'unknown'} vs {second.duration or 'unknown'}")

            if first_levels != second_levels:
                differences.append("senior/manager vs mid-professional")

        return differences

    def _extract_languages(self, assessment: CatalogEntry) -> list[str]:
        return assessment.languages or []

    def _extract_field(self, assessment: CatalogEntry, field_name: str) -> str:
        val = getattr(assessment, field_name, None)
        return str(val) if val is not None else ""

    def _normalize_values(self, values: list[str]) -> list[str]:
        return [value.lower().strip() for value in values if value and value.strip()]
