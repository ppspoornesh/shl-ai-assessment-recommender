from app.llm.base_provider import BaseLLMProvider
from app.llm.mock_provider import MockProvider
from app.models.chat import Recommendation
from app.services.comparison_engine import ComparisonResult
from app.services.llm_response_generator import LLMResponseGenerator


class RecordingProvider(BaseLLMProvider):
    def __init__(self, response: str = "Generated reply") -> None:
        self.response = response
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


def make_recommendation(name: str, score: float) -> Recommendation:
    return Recommendation(
        entity_id=name.lower().replace(" ", "-"),
        name=name,
        link="https://example.com/assessment",
        description=f"Description for {name}",
        ranking_score=score,
        matched_criteria=["role", "skills"],
        explanation="Strong match for the request.",
    )


def test_uses_recommendation_template_with_recommendations() -> None:
    provider = RecordingProvider()
    generator = LLMResponseGenerator(provider=provider)

    reply = generator.generate_reply(
        intent="initial_request",
        recommendations=[make_recommendation("Senior Python Engineer", 0.95)],
    )

    assert reply == provider.response
    assert len(provider.prompts) == 1
    assert "Senior Python Engineer" in provider.prompts[0]
    assert "0.95" in provider.prompts[0]
    assert "initial_request" in provider.prompts[0]


def test_uses_comparison_template_when_comparison_result_exists() -> None:
    provider = RecordingProvider()
    generator = LLMResponseGenerator(provider=provider)
    comparison_result = ComparisonResult(common_features=["python", "sql"], differences=["python vs java"])

    generator.generate_reply(
        intent="compare_options",
        recommendations=[make_recommendation("Python Engineer", 0.9)],
        comparison_result=comparison_result,
    )

    assert len(provider.prompts) == 1
    assert "python" in provider.prompts[0]
    assert "sql" in provider.prompts[0]
    assert "python vs java" in provider.prompts[0]


def test_uses_clarification_template_when_question_is_provided() -> None:
    provider = RecordingProvider()
    generator = LLMResponseGenerator(provider=provider)

    generator.generate_reply(
        intent="clarify_requirements",
        recommendations=[],
        clarification_question="Which seniority level matters most?",
    )

    assert len(provider.prompts) == 1
    assert "Which seniority level matters most?" in provider.prompts[0]


def test_uses_refusal_template_when_there_are_no_recommendations() -> None:
    provider = RecordingProvider()
    generator = LLMResponseGenerator(provider=provider)

    generator.generate_reply(intent="initial_request", recommendations=[])

    assert len(provider.prompts) == 1
    assert any(word in provider.prompts[0].lower() for word in ["refusal", "unable", "suitable", "politely"])


def test_llm_response_generator_works_with_mock_provider() -> None:
    generator = LLMResponseGenerator(provider=MockProvider())

    reply = generator.generate_reply(
        intent="initial_request",
        recommendations=[make_recommendation("Senior Python Engineer", 0.95)],
    )

    assert reply == "Based on the hiring requirements you've shared, I have identified the top SHL assessments for this position. For a Senior Python Developer, the strongest match is designed to evaluate core competencies and relevant technical capabilities."
