from app.services.clarification_manager import ClarificationManager
from app.services.requirement_completeness_checker import CompletenessResult


def test_missing_role_yields_role_question() -> None:
    manager = ClarificationManager()
    result = CompletenessResult(
        complete=False,
        missing_fields=["role"],
        next_required_field="role",
        reasoning="Role is missing.",
    )

    question = manager.build_question(result)

    assert question == "What role are you targeting?"


def test_missing_seniority_yields_seniority_question() -> None:
    manager = ClarificationManager()
    result = CompletenessResult(
        complete=False,
        missing_fields=["seniority"],
        next_required_field="seniority",
        reasoning="Seniority is missing.",
    )

    question = manager.build_question(result)

    assert question == "What seniority level are you targeting?"


def test_missing_technical_skills_yields_skills_question() -> None:
    manager = ClarificationManager()
    result = CompletenessResult(
        complete=False,
        missing_fields=["technical_skills"],
        next_required_field="technical_skills",
        reasoning="Technical skills are missing.",
    )

    question = manager.build_question(result)

    assert question == "Which technical skills are required for this role?"


def test_multiple_missing_fields_use_highest_priority_only() -> None:
    manager = ClarificationManager()
    result = CompletenessResult(
        complete=False,
        missing_fields=["role", "seniority", "technical_skills"],
        next_required_field="role",
        reasoning="Several fields are missing.",
    )

    question = manager.build_question(result)

    assert question == "What role are you targeting?"


def test_complete_requirements_return_no_question() -> None:
    manager = ClarificationManager()
    result = CompletenessResult(
        complete=True,
        missing_fields=[],
        next_required_field=None,
        reasoning="Requirements are complete.",
    )

    question = manager.build_question(result)

    assert question is None
