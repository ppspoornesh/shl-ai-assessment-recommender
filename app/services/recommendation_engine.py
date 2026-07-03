from __future__ import annotations

from app.models.chat import Recommendation
from app.models.requirements import HiringRequirements
from app.services.ranking_engine import RankedCandidate


class RecommendationEngine:
    """Builds the final list of recommendation objects for the client response."""

    def __init__(self, max_recommendations: int = 6) -> None:
        self._max_recommendations = max_recommendations

    def build_recommendations(self, ranked_candidates: list[RankedCandidate], requirements: HiringRequirements | None = None) -> list[Recommendation]:
        if requirements and requirements.assessment_battery:
            cognitive_candidates = [c for c in ranked_candidates if self._assessment_category(c) == "cognitive"]
            behavioral_candidates = [c for c in ranked_candidates if self._assessment_category(c) == "behavioral"]
            skill_candidates = [c for c in ranked_candidates if self._assessment_category(c) == "skill"]

            selected = []
            # Select up to 2 skill candidates
            selected.extend(skill_candidates[:2])
            # Select 1 cognitive candidate
            if cognitive_candidates:
                selected.append(cognitive_candidates[0])
            # Select 1 behavioral candidate
            if behavioral_candidates:
                selected.append(behavioral_candidates[0])

            # Fill up from remaining ranked_candidates if needed
            selected_ids = {c.entity_id for c in selected}
            for c in ranked_candidates:
                if len(selected) >= self._max_recommendations:
                    break
                if c.entity_id not in selected_ids:
                    selected.append(c)
                    selected_ids.add(c.entity_id)
        else:
            selected = ranked_candidates[:self._max_recommendations]

        recommendations = []
        for candidate in selected:
            explanation = candidate.explanation
            matched_criteria = [
                name
                for name, value in candidate.score_breakdown.items()
                if value > 0
            ]

            if not explanation or not explanation.strip():
                if not matched_criteria:
                    explanation = "No positive ranking criteria matched this assessment."
                else:
                    if len(matched_criteria) == 1:
                        criteria_text = matched_criteria[0]
                    elif len(matched_criteria) == 2:
                        criteria_text = f"{matched_criteria[0]} and {matched_criteria[1]}"
                    else:
                        criteria_text = ", ".join(matched_criteria[:-1]) + f", and {matched_criteria[-1]}"
                    explanation = f"Matched {criteria_text} criteria with a ranking score of {candidate.score}."

            if requirements and requirements.assessment_battery:
                cat = self._assessment_category(candidate)
                if cat == "cognitive":
                    explanation += " (Cognitive Component of the Battery to assess general ability)"
                elif cat == "behavioral":
                    explanation += " (Behavioral Component of the Battery to assess working style)"
                elif cat == "skill":
                    explanation += " (Role-Specific Component of the Battery)"

            recommendations.append(
                Recommendation(
                    entity_id=candidate.entity_id,
                    name=candidate.name,
                    link=candidate.link,
                    description=candidate.description or "",
                    ranking_score=candidate.score,
                    matched_criteria=matched_criteria,
                    explanation=explanation,
                    duration=candidate.duration,
                    job_levels=candidate.job_levels,
                    keys=candidate.keys,
                )
            )
        return recommendations

    def _assessment_category(self, candidate: RankedCandidate) -> str:
        name_lower = candidate.name.lower()
        if any(k in name_lower for k in ["verify", "reasoning", "ability", "cognitive"]):
            return "cognitive"
        if any(k in name_lower for k in ["opq", "personality", "behavior", "leadership style"]):
            return "behavioral"
        return "skill"
