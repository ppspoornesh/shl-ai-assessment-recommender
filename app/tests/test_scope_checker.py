from app.services.scope_checker import ScopeChecker


def test_scope_checker_accepts_assessment_related_requests() -> None:
    checker = ScopeChecker()

    assert checker.check("Recommend SHL assessments for a senior software engineer") is True
    assert checker.is_in_scope("Find an assessment for a data analyst") is True


def test_scope_checker_rejects_out_of_domain_requests() -> None:
    checker = ScopeChecker()

    assert checker.check("Write me a poem about the ocean") is False
    assert checker.is_in_scope("Explain quantum physics") is False
