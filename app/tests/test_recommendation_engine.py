from app.models.chat import Recommendation
from app.services.ranking_engine import RankedCandidate
from app.services.recommendation_engine import RecommendationEngine


def make_ranked_candidate(entity_id: str, name: str, *, score: float, breakdown: dict[str, float], explanation: str | None = None) -> RankedCandidate:
    return RankedCandidate(
        entity_id=entity_id,
        name=name,
        score=score,
        link="https://example.com/assessments/1",
        description=f"Description for {name}",
        score_breakdown=breakdown,
        explanation=explanation or "",
    )


def test_builds_top_ten_recommendations_in_ranking_order() -> None:
    engine = RecommendationEngine(max_recommendations=10)
    ranked_candidates = [
        make_ranked_candidate(
            "1",
            "Senior Python Engineer",
            score=0.95,
            breakdown={"role": 0.4, "skills": 0.3, "competencies": 0.1, "seniority": 0.1, "duration": 0.05},
        ),
        make_ranked_candidate(
            "2",
            "Java Engineer",
            score=0.9,
            breakdown={"role": 0.4, "skills": 0.3, "seniority": 0.1, "duration": 0.05, "remote": 0.05},
        ),
    ]

    for index in range(3, 13):
        ranked_candidates.append(
            make_ranked_candidate(
                str(index),
                f"Assessment {index}",
                score=float(f"0.{index}"),
                breakdown={"role": 0.4},
            )
        )

    recommendations = engine.build_recommendations(ranked_candidates)

    assert len(recommendations) == 10
    assert all(isinstance(item, Recommendation) for item in recommendations)
    assert recommendations[0].name == "Senior Python Engineer"
    assert recommendations[0].ranking_score == 0.95
    assert recommendations[0].matched_criteria == ["role", "skills", "competencies", "seniority", "duration"]
    assert recommendations[0].explanation == "Matched role, skills, competencies, seniority, and duration criteria with a ranking score of 0.95."
    assert recommendations[-1].name == "Assessment 10"


def test_uses_existing_explanation_when_present() -> None:
    engine = RecommendationEngine()
    ranked_candidates = [
        make_ranked_candidate(
            "7",
            "Leadership Assessment",
            score=0.8,
            breakdown={"role": 0.4, "competencies": 0.4},
            explanation="Strong leadership fit.",
        )
    ]

    recommendations = engine.build_recommendations(ranked_candidates)

    assert recommendations[0].explanation == "Strong leadership fit."
    assert recommendations[0].matched_criteria == ["role", "competencies"]


def test_returns_empty_list_for_empty_input() -> None:
    engine = RecommendationEngine()

    assert engine.build_recommendations([]) == []
