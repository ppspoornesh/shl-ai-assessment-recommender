from app.models.catalog import CatalogEntry
from app.services.comparison_engine import ComparisonEngine, ComparisonResult


def make_entry(entity_id: str, name: str, *, duration: str | None = None, job_levels: list[str] | None = None, competencies: list[str] | None = None, skills: list[str] | None = None, languages: list[str] | None = None, additional_data: dict | None = None) -> CatalogEntry:
    data = dict(additional_data or {})
    if languages:
        data["languages"] = languages
    return CatalogEntry(
        entity_id=entity_id,
        name=name,
        link="https://example.com/assessment",
        description="Assessment description",
        duration=duration,
        job_levels=job_levels or [],
        competencies=competencies or [],
        skills=skills or [],
        additional_data=data,
    )


def test_comparison_engine_builds_structured_comparison_data() -> None:
    engine = ComparisonEngine()
    assessments = [
        make_entry(
            "1",
            "Python Engineer Assessment",
            duration="30 minutes",
            job_levels=["Senior", "Manager"],
            competencies=["leadership", "communication"],
            skills=["python", "sql"],
            languages=["English"],
            additional_data={"adaptive": "yes", "remote": "yes"},
        ),
        make_entry(
            "2",
            "Java Engineer Assessment",
            duration="20 minutes",
            job_levels=["Mid-Professional"],
            competencies=["communication"],
            skills=["java", "sql"],
            languages=["English"],
            additional_data={"adaptive": "no", "remote": "no"},
        ),
    ]

    result = engine.compare(assessments)

    assert isinstance(result, ComparisonResult)
    assert result.common_features == ["sql", "communication"]
    assert result.differences == ["python vs java", "30 minutes vs 20 minutes", "senior/manager vs mid-professional"]
    assert result.durations == ["30 minutes", "20 minutes"]
    assert result.job_levels == [["Senior", "Manager"], ["Mid-Professional"]]
    assert result.competencies == [["leadership", "communication"], ["communication"]]
    assert result.languages == [["English"], ["English"]]
    assert result.adaptive_support == ["yes", "no"]
    assert result.remote_support == ["yes", "no"]


def test_comparison_engine_handles_more_than_two_assessments() -> None:
    engine = ComparisonEngine()
    assessments = [
        make_entry("1", "Assessment A", duration="10 minutes", job_levels=["Entry-Level"], competencies=["leadership"], skills=["python"], languages=["English"], additional_data={"adaptive": "yes", "remote": "yes"}),
        make_entry("2", "Assessment B", duration="20 minutes", job_levels=["Mid-Professional"], competencies=["communication"], skills=["java"], languages=["English"], additional_data={"adaptive": "no", "remote": "yes"}),
        make_entry("3", "Assessment C", duration="15 minutes", job_levels=["Senior"], competencies=["leadership"], skills=["python"], languages=["French"], additional_data={"adaptive": "yes", "remote": "no"}),
    ]

    result = engine.compare(assessments)

    assert len(result.durations) == 3
    assert len(result.job_levels) == 3
    assert len(result.competencies) == 3
    assert len(result.languages) == 3
    assert result.common_features == ["python", "leadership"]


def test_comparison_engine_requires_at_least_two_assessments() -> None:
    engine = ComparisonEngine()

    result = engine.compare([make_entry("1", "Assessment A")])

    assert result.common_features == []
    assert result.differences == []
    assert result.durations == []
    assert result.job_levels == []
    assert result.competencies == []
    assert result.languages == []
    assert result.adaptive_support == []
    assert result.remote_support == []
