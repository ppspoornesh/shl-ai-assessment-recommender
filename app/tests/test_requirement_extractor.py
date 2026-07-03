from app.models.chat import Message
from app.services.requirement_extractor import RequirementExtractor


def test_requirement_extractor_merges_multiple_turns() -> None:
    extractor = RequirementExtractor()
    conversation = [
        Message(role="user", content="We need a senior software engineer role in technology with Python and SQL."),
        Message(role="assistant", content="Sure, what experience level are you targeting?"),
        Message(role="user", content="At least 5 years experience, remote is preferred, and strong leadership."),
    ]

    result = extractor.parse_conversation(conversation)

    assert result.requirements.role == "software engineer"
    assert result.requirements.seniority == "senior"
    assert result.requirements.industry == "technology"
    assert result.requirements.years_of_experience == 5
    assert "python" in result.requirements.technical_skills
    assert "sql" in result.requirements.technical_skills
    assert result.requirements.remote is True
    assert "leadership" in result.requirements.competencies
    assert 0.0 <= result.confidence <= 1.0


def test_requirement_extractor_preserves_previous_information_on_refinement() -> None:
    extractor = RequirementExtractor()
    conversation = [
        Message(role="user", content="I need a product manager role with strong communication skills."),
        Message(role="assistant", content="Do you have a preferred industry?"),
        Message(role="user", content="Prefer finance, and also look for analytical and collaborative candidates."),
    ]

    result = extractor.parse_conversation(conversation)

    assert result.requirements.role == "product manager"
    assert result.requirements.industry == "finance"
    assert "communication" in result.requirements.competencies
    assert "analytical" in result.requirements.personality_traits
    assert "collaborative" in result.requirements.personality_traits


def test_requirement_extractor_handles_noisy_input() -> None:
    extractor = RequirementExtractor()
    conversation = [
        Message(role="user", content="Please find me a senior data analyst, ideally with SQL and Excel, in retail."),
    ]

    result = extractor.parse_conversation(conversation)

    assert result.requirements.role == "data analyst"
    assert result.requirements.seniority == "senior"
    assert result.requirements.industry == "retail"
    assert "sql" in result.requirements.technical_skills
    assert "excel" in result.requirements.technical_skills


def test_requirement_extractor_supports_reordered_history() -> None:
    extractor = RequirementExtractor()
    conversation = [
        Message(role="user", content="Remote is preferred."),
        Message(role="assistant", content="Got it."),
        Message(role="user", content="Need a senior engineer with Python."),
    ]

    result = extractor.parse_conversation(conversation)

    assert result.requirements.remote is True
    assert result.requirements.role == "engineer"
    assert result.requirements.seniority == "senior"
    assert "python" in result.requirements.technical_skills


def test_requirement_extractor_handles_contradictory_refinements() -> None:
    extractor = RequirementExtractor()
    conversation = [
        Message(role="user", content="We need a senior product manager with leadership skills."),
        Message(role="user", content="Actually, make it junior instead."),
    ]

    result = extractor.parse_conversation(conversation)

    assert result.requirements.seniority == "junior"
    assert result.requirements.role == "product manager"


def test_requirement_extractor_reports_incomplete_requirements() -> None:
    extractor = RequirementExtractor()
    conversation = [
        Message(role="user", content="I need help finding a candidate."),
    ]

    result = extractor.parse_conversation(conversation)

    assert result.requirements.role is None
    assert result.missing_fields
    assert result.confidence < 0.6
