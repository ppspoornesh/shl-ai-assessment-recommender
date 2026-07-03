from __future__ import annotations

from pathlib import Path

from app.llm.base_provider import BaseLLMProvider
from app.llm.provider_factory import ProviderFactory
from app.models.chat import Recommendation
from app.services.comparison_engine import ComparisonResult


class LLMResponseGenerator:
    """Builds a natural-language reply from structured inputs using prompt templates."""

    def __init__(self, provider: BaseLLMProvider | None = None, prompts_dir: str | None = None) -> None:
        self._provider = provider or ProviderFactory.create_provider()
        self._prompts_dir = Path(prompts_dir or Path(__file__).resolve().parent.parent / "prompts")

    def generate_reply(
        self,
        *,
        intent: str,
        recommendations: list[Recommendation],
        comparison_result: ComparisonResult | None = None,
        clarification_question: str | None = None,
    ) -> str:
        template_name = self._template_name(intent, recommendations, comparison_result, clarification_question)
        template = self._load_template(template_name)
        prompt = self._render_prompt(template, intent, recommendations, comparison_result, clarification_question)
        return self._provider.generate(prompt)

    def _template_name(
        self,
        intent: str,
        recommendations: list[Recommendation],
        comparison_result: ComparisonResult | None,
        clarification_question: str | None,
    ) -> str:
        if clarification_question:
            return "clarification_prompt.txt"
        if comparison_result is not None and intent == "compare_options":
            return "comparison_prompt.txt"
        if recommendations:
            return "recommendation_prompt.txt"
        return "refusal_prompt.txt"

    def _render_prompt(
        self,
        template: str,
        intent: str,
        recommendations: list[Recommendation],
        comparison_result: ComparisonResult | None,
        clarification_question: str | None,
    ) -> str:
        system_prompt = self._load_template("system_prompt.txt")
        context = {
            "system_prompt": system_prompt.strip(),
            "intent": intent,
            "recommendations": self._serialize_recommendations(recommendations),
            "comparison_result": self._serialize_comparison(comparison_result),
            "clarification_question": clarification_question or "",
        }
        return template.format(**context)

    def _load_template(self, template_name: str) -> str:
        template_path = self._prompts_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
        return template_path.read_text(encoding="utf-8")

    def _serialize_recommendations(self, recommendations: list[Recommendation]) -> str:
        if not recommendations:
            return "None"
        lines: list[str] = []
        for recommendation in recommendations:
            lines.append(
                f"- {recommendation.name} | score={recommendation.ranking_score} | matched={', '.join(recommendation.matched_criteria) or 'none'} | explanation={recommendation.explanation}"
            )
        return "\n".join(lines)

    def _serialize_comparison(self, comparison_result: ComparisonResult | None) -> str:
        if comparison_result is None:
            return "None"
        parts = [
            f"common_features={', '.join(comparison_result.common_features) or 'none'}",
            f"differences={', '.join(comparison_result.differences) or 'none'}"
        ]
        if comparison_result.use_cases:
            parts.append(f"use_cases={'; '.join(comparison_result.use_cases)}")
        if comparison_result.tradeoffs:
            parts.append(f"tradeoffs={'; '.join(comparison_result.tradeoffs)}")
        if comparison_result.recommendation_guidance:
            parts.append(f"guidance={comparison_result.recommendation_guidance}")
        return "; ".join(parts)
