from __future__ import annotations

from typing import Iterable

from app.models.chat import Message
from app.models.requirements import ExtractionResult, HiringRequirements
from app.services.extraction_rules import (
    CompetencyExtractionRule,
    ExperienceExtractionRule,
    IndustryExtractionRule,
    PersonalityExtractionRule,
    RemoteExtractionRule,
    RoleExtractionRule,
    SeniorityExtractionRule,
    SkillExtractionRule,
)


class RequirementExtractor:
    """Rule-based extractor that turns conversation history into structured hiring requirements."""

    def __init__(self) -> None:
        self._rules = [
            SeniorityExtractionRule(),
            RoleExtractionRule(),
            ExperienceExtractionRule(),
            SkillExtractionRule(),
            CompetencyExtractionRule(),
            PersonalityExtractionRule(),
            IndustryExtractionRule(),
            RemoteExtractionRule(),
        ]

    def parse_conversation(self, conversation: Iterable[Message]) -> ExtractionResult:
        """Parse conversation turns into an ExtractionResult object."""
        requirements = HiringRequirements()
        extracted_entities: list[str] = []
        user_messages = [message.content for message in conversation if message.role == "user"]

        for message in user_messages:
            current = self._parse_message(message)
            requirements = requirements.merge(current)
            extracted_entities.extend(self._collect_entities(current))

        missing_fields = self._collect_missing_fields(requirements)
        confidence = self._calculate_confidence(requirements, missing_fields)

        return ExtractionResult(
            requirements=requirements,
            confidence=confidence,
            missing_fields=missing_fields,
            extracted_entities=sorted(set(extracted_entities)),
        )

    def _parse_message(self, text: str) -> HiringRequirements:
        """Apply each rule to a single user message."""
        requirements = HiringRequirements()
        for rule in self._rules:
            requirements = rule.apply(text, requirements)
        return requirements

    def _collect_entities(self, requirements: HiringRequirements) -> list[str]:
        entities = []
        entities.extend(requirements.technical_skills)
        entities.extend(requirements.competencies)
        entities.extend(requirements.personality_traits)
        if requirements.role:
            entities.append(requirements.role)
        if requirements.industry:
            entities.append(requirements.industry)
        return [entity for entity in entities if entity]

    def _collect_missing_fields(self, requirements: HiringRequirements) -> list[str]:
        missing: list[str] = []
        for field in ["role", "seniority", "years_of_experience", "technical_skills", "competencies", "industry"]:
            value = getattr(requirements, field)
            if not value:
                missing.append(field)
        return missing

    def _calculate_confidence(self, requirements: HiringRequirements, missing_fields: list[str]) -> float:
        score = 0.0
        if requirements.role:
            score += 0.3
        if requirements.seniority:
            score += 0.15
        if requirements.years_of_experience is not None:
            score += 0.15
        if requirements.technical_skills:
            score += 0.15
        if requirements.competencies:
            score += 0.1
        if requirements.industry:
            score += 0.15
        return round(min(score, 1.0), 2) if missing_fields else round(min(score + 0.1, 1.0), 2)
