from __future__ import annotations

from app.core.config import settings
from app.models.chat import Recommendation
from app.services.ranking_engine import RankedCandidate


class RecommendationEngine:
    """Transforms ranked assessments into a compact recommendation payload.

    This component is intentionally limited to presentation-oriented formatting:
    it never retrieves candidates, compares assessments, or generates any
    conversational text. It preserves the ranking order and caps the output at
    the top 10 ranked assessments.
    """

    def __init__(self, max_recommendations: int | None = None) -> None:
        self._max_recommendations = max_recommendations if max_recommendations is not None else settings.max_recommendations

    def build_recommendations(self, ranked_candidates: list[RankedCandidate]) -> list[Recommendation]:
        recommendations: list[Recommendation] = []
        for ranked_candidate in ranked_candidates[: self._max_recommendations]:
            matched_criteria = self._matched_criteria(ranked_candidate)
            explanation = self._build_explanation(ranked_candidate, matched_criteria)
            recommendations.append(
                Recommendation(
                    entity_id=ranked_candidate.entity_id,
                    name=ranked_candidate.name,
                    link=str(ranked_candidate.link or ""),
                    description=ranked_candidate.description or "",
                    ranking_score=ranked_candidate.score,
                    matched_criteria=matched_criteria,
                    explanation=explanation,
                    duration=ranked_candidate.duration,
                    job_levels=ranked_candidate.job_levels,
                    keys=ranked_candidate.keys,
                )
            )
        return recommendations

    def _matched_criteria(self, ranked_candidate: RankedCandidate) -> list[str]:
        score_breakdown = ranked_candidate.score_breakdown or {}
        return [name for name, value in score_breakdown.items() if value > 0]

    def _build_explanation(self, ranked_candidate: RankedCandidate, matched_criteria: list[str]) -> str:
        if ranked_candidate.explanation and ranked_candidate.explanation.strip():
            return ranked_candidate.explanation.strip()

        if not matched_criteria:
            return "No positive ranking criteria matched this assessment."

        if len(matched_criteria) == 1:
            criteria_text = matched_criteria[0]
        elif len(matched_criteria) == 2:
            criteria_text = f"{matched_criteria[0]} and {matched_criteria[1]}"
        else:
            criteria_text = ", ".join(matched_criteria[:-1]) + f", and {matched_criteria[-1]}"
        return f"Matched {criteria_text} criteria with a ranking score of {ranked_candidate.score}."
