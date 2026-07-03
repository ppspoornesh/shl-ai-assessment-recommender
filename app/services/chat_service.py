from __future__ import annotations

import logging
from typing import Sequence

from app.models.catalog import CatalogEntry
from app.models.chat import ChatRequest, ChatResponse, Recommendation
from app.services.candidate_retriever import CandidateRetriever
from app.services.clarification_manager import ClarificationManager
from app.services.comparison_engine import ComparisonEngine, ComparisonResult
from app.services.intent_detector import IntentDetector
from app.services.llm_response_generator import LLMResponseGenerator
from app.services.prompt_guard import PromptGuard
from app.services.ranking_engine import RankedCandidate, RankingEngine
from app.services.recommendation_engine import RecommendationEngine
from app.services.requirement_completeness_checker import RequirementCompletenessChecker
from app.services.requirement_extractor import RequirementExtractor
from app.services.response_formatter import ResponseFormatter
from app.services.scope_checker import ScopeChecker

logger = logging.getLogger(__name__)


class ChatService:
    """Coordinates the full chat pipeline without owning domain logic."""

    def __init__(
        self,
        *,
        prompt_guard: PromptGuard | None = None,
        scope_checker: ScopeChecker | None = None,
        intent_detector: IntentDetector | None = None,
        requirement_extractor: RequirementExtractor | None = None,
        completeness_checker: RequirementCompletenessChecker | None = None,
        clarification_manager: ClarificationManager | None = None,
        candidate_retriever: CandidateRetriever | None = None,
        ranking_engine: RankingEngine | None = None,
        comparison_engine: ComparisonEngine | None = None,
        recommendation_engine: RecommendationEngine | None = None,
        response_generator: LLMResponseGenerator | None = None,
        response_formatter: ResponseFormatter | None = None,
    ) -> None:
        self.prompt_guard = prompt_guard or PromptGuard()
        self.scope_checker = scope_checker or ScopeChecker()
        self.intent_detector = intent_detector or IntentDetector()
        self.requirement_extractor = requirement_extractor or RequirementExtractor()
        self.completeness_checker = completeness_checker or RequirementCompletenessChecker()
        self.clarification_manager = clarification_manager or ClarificationManager()
        self.candidate_retriever = candidate_retriever or CandidateRetriever()
        self.ranking_engine = ranking_engine or RankingEngine()
        self.comparison_engine = comparison_engine or ComparisonEngine()
        self.recommendation_engine = recommendation_engine or RecommendationEngine()
        self.response_generator = response_generator or LLMResponseGenerator()
        self.response_formatter = response_formatter or ResponseFormatter()

    async def handle_chat(self, request: ChatRequest) -> ChatResponse:
        logger.info("Handling chat request with %d conversation messages", len(request.conversation))

        query = request.conversation[-1].content.strip()

        if not self.prompt_guard.is_safe(query):
            reply = "I can help with SHL assessment recommendations, but I cannot process prompt injection attempts."
            return self._format(reply=reply, recommendations=[])

        if not self.scope_checker.is_in_scope(query):
            reply = "I can only help with SHL assessment recommendations and related hiring requirements."
            return self._format(reply=reply, recommendations=[])

        intent = self.intent_detector.detect_intent(request.conversation)
        extraction_result = self.requirement_extractor.parse_conversation(request.conversation)
        completeness_result = self.completeness_checker.check(extraction_result.requirements)

        if not completeness_result.complete:
            clarification_question = self.clarification_manager.build_question(completeness_result)
            reply = self._build_reply(
                intent="clarify_requirements",
                recommendations=[],
                clarification_question=clarification_question,
            )
            return self._format(reply=reply, recommendations=[])

        candidates = self.candidate_retriever.retrieve(extraction_result.requirements)
        ranked_candidates = self.ranking_engine.rank(candidates, extraction_result.requirements)
        recommendations = self.recommendation_engine.build_recommendations(ranked_candidates)
        comparison_result = self._compare_ranked_candidates(candidates, ranked_candidates) if intent == "compare_options" else None
        reply = self._build_reply(
            intent=intent,
            recommendations=recommendations,
            comparison_result=comparison_result,
        )

        return self._format(reply=reply, recommendations=recommendations)

    def _compare_ranked_candidates(
        self,
        candidates: list[CatalogEntry],
        ranked_candidates: list[RankedCandidate],
    ) -> ComparisonResult | None:
        if len(ranked_candidates) < 2:
            return None

        candidates_by_id = {candidate.entity_id: candidate for candidate in candidates}
        ranked_assessments = [
            candidates_by_id[ranked_candidate.entity_id]
            for ranked_candidate in ranked_candidates[:3]
            if ranked_candidate.entity_id in candidates_by_id
        ]
        if len(ranked_assessments) < 2:
            return None
        return self.comparison_engine.compare(ranked_assessments)

    def _build_reply(
        self,
        *,
        intent: str,
        recommendations: list[Recommendation],
        comparison_result: ComparisonResult | None = None,
        clarification_question: str | None = None,
    ) -> str:
        try:
            return self.response_generator.generate_reply(
                intent=intent,
                recommendations=recommendations,
                comparison_result=comparison_result,
                clarification_question=clarification_question,
            )
        except ValueError as e:
            logger.info("LLM provider is not configured: %s; using deterministic fallback reply.", e)
        except Exception as e:
            logger.error("LLM generation failed: %s; using deterministic fallback reply.", e, exc_info=True)

        if clarification_question:
            return clarification_question

        if comparison_result is not None:
            return (
                "I compared the strongest matching SHL assessments for the role and skills you shared. "
                "The ranked options below highlight the most relevant differences."
            )

        if recommendations:
            return (
                "Considering the role and skills you've provided, these SHL assessments are the strongest matches. "
                "They are ranked by fit against the hiring requirements."
            )

        return (
            "I couldn't find a suitable SHL assessment for those requirements. "
            "Please refine the role, seniority, or required skills and I can try again."
        )

    def _format(self, *, reply: str, recommendations: Sequence[Recommendation]) -> ChatResponse:
        payload = self.response_formatter.format(
            reply=reply,
            recommendations=list(recommendations),
            end_of_conversation=False,
        )
        return ChatResponse(**payload)
