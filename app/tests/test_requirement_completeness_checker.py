from app.models.requirements import HiringRequirements
from app.services.requirement_completeness_checker import RequirementCompletenessChecker


def test_complete_requirements_are_marked_complete() -> None:
    checker = RequirementCompletenessChecker()
    requirements = HiringRequirements(
        role="software engineer",
        seniority="senior",
        technical_skills=["python"],
    )

    result = checker.check(requirements)

    assert result.complete is True
    assert result.missing_fields == []
    assert result.next_required_field is None
    assert "complete" in result.reasoning.lower()


def test_missing_role_is_reported() -> None:
    checker = RequirementCompletenessChecker()
    requirements = HiringRequirements(seniority="senior", technical_skills=["python"])

    result = checker.check(requirements)

    assert result.complete is False
    assert result.missing_fields == ["role"]
    assert result.next_required_field == "role"
    assert "role" in result.reasoning.lower()


def test_missing_seniority_is_reported() -> None:
    checker = RequirementCompletenessChecker()
    requirements = HiringRequirements(role="product manager", technical_skills=["communication"])

    result = checker.check(requirements)

    assert result.complete is False
    assert result.missing_fields == ["seniority"]
    assert result.next_required_field == "seniority"


def test_missing_skills_are_reported() -> None:
    checker = RequirementCompletenessChecker()
    requirements = HiringRequirements(role="data analyst", seniority="junior")

    result = checker.check(requirements)

    assert result.complete is False
    assert result.missing_fields == ["technical_skills"]
    assert result.next_required_field == "technical_skills"


def test_multiple_missing_fields_are_reported() -> None:
    checker = RequirementCompletenessChecker()
    requirements = HiringRequirements()

    result = checker.check(requirements)

    assert result.complete is False
    assert result.missing_fields == ["role", "seniority", "technical_skills"]
    assert result.next_required_field == "role"


def test_refinement_preserves_completeness() -> None:
    checker = RequirementCompletenessChecker()
    initial = HiringRequirements(role="software engineer", seniority="senior", technical_skills=["python"])
    refined = initial.merge(HiringRequirements(industry="finance", competencies=["leadership"]))

    result = checker.check(refined)

    assert result.complete is True
    assert result.missing_fields == []
    assert result.next_required_field is None
