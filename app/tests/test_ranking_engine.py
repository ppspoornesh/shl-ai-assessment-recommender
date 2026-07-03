from app.models.catalog import CatalogEntry
from app.models.requirements import HiringRequirements
from app.services.ranking_engine import RankingEngine


def make_entry(entity_id: str, name: str, *, skills: list[str] | None = None, competencies: list[str] | None = None, job_levels: list[str] | None = None, duration: str | None = None, primary_function: str | None = None) -> CatalogEntry:
    return CatalogEntry(
        entity_id=entity_id,
        name=name,
        link="https://example.com/assessment",
        description="Assessment description",
        skills=skills or [],
        competencies=competencies or [],
        job_levels=job_levels or [],
        duration=duration,
        primary_function=primary_function,
    )


def test_ranks_candidates_with_weighted_scores_and_explanations() -> None:
    engine = RankingEngine(weights={"role": 0.4, "skills": 0.3, "competencies": 0.1, "seniority": 0.1, "duration": 0.05, "remote": 0.0})
    requirements = HiringRequirements(
        role="software engineer",
        seniority="senior",
        technical_skills=["python"],
        competencies=["leadership"],
    )
    candidates = [
        make_entry("1", "Senior Software Engineer Assessment", skills=["python"], competencies=["leadership"], job_levels=["Senior"], duration="30 minutes", primary_function="software engineering"),
        make_entry("2", "Python Basics Assessment", skills=["python"], competencies=[], job_levels=["Entry-Level"], duration="15 minutes", primary_function="programming"),
    ]

    ranked = engine.rank(candidates, requirements)

    assert ranked[0].entity_id == "1"
    assert ranked[1].entity_id == "2"
    assert ranked[0].score == 0.95
    assert ranked[0].score_breakdown["role"] == 0.4
    assert ranked[0].score_breakdown["skills"] == 0.3
    assert ranked[0].score_breakdown["competencies"] == 0.1
    assert ranked[0].score_breakdown["seniority"] == 0.1
    assert ranked[0].score_breakdown["duration"] == 0.05
    assert ranked[0].score_breakdown["remote"] == 0.0


def test_uses_configuration_weights() -> None:
    engine = RankingEngine(weights={"role": 0.5, "skills": 0.2, "competencies": 0.1, "seniority": 0.1, "duration": 0.05, "remote": 0.05})
    requirements = HiringRequirements(role="engineer", technical_skills=["java"])
    candidates = [make_entry("3", "Java Engineer Assessment", skills=["java"], job_levels=["Mid-Professional"], duration="20 minutes")]

    ranked = engine.rank(candidates, requirements)

    assert ranked[0].score == 0.75
    assert ranked[0].score_breakdown["role"] == 0.5
    assert ranked[0].score_breakdown["skills"] == 0.2


def test_returns_zero_score_for_non_matching_candidates() -> None:
    engine = RankingEngine()
    requirements = HiringRequirements(role="software engineer", technical_skills=["python"])
    candidates = [make_entry("4", "Finance Operations Assessment", skills=["excel"])]

    ranked = engine.rank(candidates, requirements)

    assert ranked[0].score == 0.0
    assert ranked[0].score_breakdown["role"] == 0.0
    assert ranked[0].score_breakdown["skills"] == 0.0


def test_scores_are_deterministic_for_same_input() -> None:
    engine = RankingEngine()
    requirements = HiringRequirements(role="software engineer", technical_skills=["python"], seniority="senior")
    candidates = [make_entry("5", "Python Engineering Assessment", skills=["python"], job_levels=["Senior"], duration="25 minutes")]

    first = engine.rank(candidates, requirements)
    second = engine.rank(candidates, requirements)

    assert first[0].score == second[0].score
    assert first[0].score_breakdown == second[0].score_breakdown


def test_scores_skills_from_catalog_text_when_structured_skills_are_missing() -> None:
    engine = RankingEngine(weights={"role": 0.4, "skills": 0.3, "competencies": 0.1, "seniority": 0.1, "duration": 0.05, "remote": 0.0})
    requirements = HiringRequirements(role="developer", technical_skills=["python"])
    candidates = [
        CatalogEntry(
            entity_id="6",
            name="Python Developer Assessment",
            link="https://example.com/assessment",
            description="Measures Python programming knowledge.",
            skills=[],
        )
    ]

    ranked = engine.rank(candidates, requirements)

    assert ranked[0].score_breakdown["role"] == 0.4
    assert ranked[0].score_breakdown["skills"] == 0.3
