from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path

from app.models.requirements import HiringRequirements


class ExtractionRule(ABC):
    """Base interface for a single extraction rule."""

    @abstractmethod
    def apply(self, text: str, requirements: HiringRequirements) -> HiringRequirements:
        """Apply the rule to the given text and update the requirements."""


class SeniorityExtractionRule(ExtractionRule):
    def apply(self, text: str, requirements: HiringRequirements) -> HiringRequirements:
        text_lower = text.lower()
        preferred_order = ["senior", "junior", "principal", "executive", "director", "lead", "mid-level", "mid level"]
        for keyword in preferred_order:
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, text_lower):
                return requirements.model_copy(update={"seniority": keyword})
        return requirements


class RoleExtractionRule(ExtractionRule):
    def apply(self, text: str, requirements: HiringRequirements) -> HiringRequirements:
        text_lower = text.lower()
        patterns = [
            r"\b(?:need|seeking|looking for|find me|find|hire|hiring|searching for)\s+(?:an?|the)?\s*(?P<role>[^,.;:!?]+?)(?=\s+(?:role|position|job|with|in|for|and|,|\.|$))",
            r"\b(?:role|position|job title)\s*(?:is|:|for|as)?\s*(?P<role>[^,.;:!?]+?)(?=\s+(?:in|with|who|that|for|as|on|,|\.|$))",
            r"\b(?P<role>product manager|software engineer|data analyst|engineer|analyst|manager|developer|designer|director|architect|scientist|consultant)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match and match.groupdict().get("role"):
                extracted = match.group("role").strip()
                normalized = self._normalize_role(extracted)
                generic_roles = {"developer", "engineer", "analyst", "manager", "designer", "director", "architect", "scientist", "consultant"}
                if normalized in generic_roles:
                    normalized = self._extract_with_modifier(text_lower, normalized)
                if normalized:
                    return requirements.model_copy(update={"role": normalized})

        known_roles = [
            "product manager",
            "software engineer",
            "data analyst",
            "call center agent",
            "customer service representative",
            "sales representative",
            "engineer",
            "analyst",
            "manager",
            "developer",
            "designer",
            "director",
            "architect",
            "scientist",
            "consultant",
            "agent",
            "representative",
            "sales",
            "support",
            "specialist",
            "assistant",
            "associate",
            "nurse",
            "worker",
        ]
        for role in known_roles:
            if role in text_lower:
                combined_role = self._extract_with_modifier(text_lower, role)
                return requirements.model_copy(update={"role": combined_role})

        return requirements

    def _extract_with_modifier(self, text_lower: str, role: str) -> str:
        stop_words = {
            "a", "an", "the", "need", "hiring", "seeking", "looking", "for", "with", "to", "at", "in", "of", "and",
            "or", "find", "hire", "is", "senior", "junior", "principal", "lead", "executive", "director",
            "mid-level", "mid level", "role", "position", "job", "candidate", "candidates"
        }
        match = re.search(rf"\b(?P<modifier>[a-zA-Z\+#\-]+)\s+{re.escape(role)}\b", text_lower)
        if match:
            mod = match.group("modifier").strip()
            if mod not in stop_words and len(mod) > 1:
                return f"{mod} {role}"
        return role

    def _normalize_role(self, role: str) -> str:
        normalized = role.strip()
        if normalized.startswith("senior "):
            normalized = normalized[len("senior "):]
        if normalized.startswith("junior "):
            normalized = normalized[len("junior "):]
        if normalized.startswith("principal "):
            normalized = normalized[len("principal "):]
        if normalized.startswith("lead "):
            normalized = normalized[len("lead "):]
        if normalized.startswith("director "):
            normalized = normalized[len("director "):]
        if normalized.startswith("executive "):
            normalized = normalized[len("executive "):]
        return normalized.strip()


class ExperienceExtractionRule(ExtractionRule):
    def apply(self, text: str, requirements: HiringRequirements) -> HiringRequirements:
        patterns = [
            r"\b(?P<years>[0-9]+)\s*(?:\+\s*)?(?:years|yrs|year)\b",
            r"\b(?:minimum|at least)\s*(?P<years>[0-9]+)\s*(?:years|yrs|year)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match and match.groupdict().get("years"):
                return requirements.model_copy(update={"years_of_experience": int(match.group("years"))})
        return requirements


class SkillExtractionRule(ExtractionRule):
    def apply(self, text: str, requirements: HiringRequirements) -> HiringRequirements:
        technical_skills = self._load_known_skills()
        found = [skill for skill in technical_skills if re.search(rf"\b{re.escape(skill)}\b", text.lower())]
        if not found:
            return requirements

        updated = list(requirements.technical_skills)
        for skill in found:
            if skill not in updated:
                updated.append(skill)
        return requirements.model_copy(update={"technical_skills": updated})

    def _load_known_skills(self) -> list[str]:
        config_path = Path(__file__).resolve().parent.parent / "config" / "technical_skills.json"
        if not config_path.exists():
            return []
        with config_path.open("r", encoding="utf-8") as config_file:
            data = json.load(config_file)
        return [item.lower() for item in data.get("technical_skills", [])]


class CompetencyExtractionRule(ExtractionRule):
    def apply(self, text: str, requirements: HiringRequirements) -> HiringRequirements:
        terms = [
            "leadership",
            "communication",
            "problem solving",
            "teamwork",
            "analysis",
            "creativity",
            "decision making",
            "adaptability",
        ]
        found = [term for term in terms if term in text.lower()]
        if not found:
            return requirements
        updated = list(requirements.competencies)
        for term in found:
            if term not in updated:
                updated.append(term)
        return requirements.model_copy(update={"competencies": updated})


class PersonalityExtractionRule(ExtractionRule):
    def apply(self, text: str, requirements: HiringRequirements) -> HiringRequirements:
        terms = [
            "analytical",
            "collaborative",
            "resilient",
            "detail oriented",
            "curious",
            "strategic",
            "empathetic",
            "driven",
        ]
        found = [term for term in terms if term in text.lower()]
        if not found:
            return requirements
        updated = list(requirements.personality_traits)
        for term in found:
            if term not in updated:
                updated.append(term)
        return requirements.model_copy(update={"personality_traits": updated})


class IndustryExtractionRule(ExtractionRule):
    def apply(self, text: str, requirements: HiringRequirements) -> HiringRequirements:
        terms = [
            "finance",
            "technology",
            "healthcare",
            "retail",
            "manufacturing",
            "government",
            "education",
            "energy",
            "transportation",
            "pharma",
            "insurance",
        ]
        for term in terms:
            if re.search(rf"\b{re.escape(term)}\b", text.lower()):
                return requirements.model_copy(update={"industry": term})
        return requirements


class RemoteExtractionRule(ExtractionRule):
    def apply(self, text: str, requirements: HiringRequirements) -> HiringRequirements:
        text_lower = text.lower()
        if "remote" in text_lower:
            return requirements.model_copy(update={"remote": True})
        if "onsite" in text_lower:
            return requirements.model_copy(update={"remote": False})
        if "hybrid" in text_lower:
            return requirements.model_copy(update={"remote": True})
        return requirements


class DepartmentExtractionRule(ExtractionRule):
    def apply(self, text: str, requirements: HiringRequirements) -> HiringRequirements:
        text_lower = text.lower()
        departments = [
            "sales", "finance", "engineering", "healthcare", "call center", "customer support",
            "customer service", "administration", "human resources", "hr", "marketing", "operations", "ops"
        ]
        for dept in departments:
            if re.search(rf"\b{re.escape(dept)}\b", text_lower):
                return requirements.model_copy(update={"department": dept})
        return requirements


class SoftSkillsExtractionRule(ExtractionRule):
    def apply(self, text: str, requirements: HiringRequirements) -> HiringRequirements:
        text_lower = text.lower()
        skills = [
            "communication", "empathy", "teamwork", "collaboration", "active listening", "problem solving",
            "negotiation", "creativity", "adaptability", "critical thinking", "patience", "conflict resolution",
            "presentation", "interpersonal", "leadership", "time management"
        ]
        found = [skill for skill in skills if skill in text_lower]
        if not found:
            return requirements
        updated = list(requirements.soft_skills)
        for skill in found:
            if skill not in updated:
                updated.append(skill)
        return requirements.model_copy(update={"soft_skills": updated})


class CertificationsExtractionRule(ExtractionRule):
    def apply(self, text: str, requirements: HiringRequirements) -> HiringRequirements:
        text_lower = text.lower()
        certs = ["pmp", "aws", "certified", "certification", "certifications", "ccna", "prince2", "scrum master", "cpa", "cfa", "safe"]
        found = [cert for cert in certs if cert in text_lower]
        if not found:
            return requirements
        updated = list(requirements.certifications)
        for cert in found:
            if cert not in updated:
                updated.append(cert)
        return requirements.model_copy(update={"certifications": updated})


class LanguageAccentLocationExtractionRule(ExtractionRule):
    def apply(self, text: str, requirements: HiringRequirements) -> HiringRequirements:
        text_lower = text.lower()
        
        # Languages
        languages = ["english", "spanish", "french", "german", "mandarin", "japanese", "italian", "portuguese", "hindi"]
        found_langs = [lang for lang in languages if re.search(rf"\b{re.escape(lang)}\b", text_lower)]
        updated_langs = list(requirements.preferred_languages)
        for lang in found_langs:
            if lang not in updated_langs:
                updated_langs.append(lang)
        requirements = requirements.model_copy(update={"preferred_languages": updated_langs})

        # Accent
        accents = {
            "us": "us", "uk": "uk", "british": "uk", "american": "us", "indian": "indian",
            "australian": "australian", "neutral": "neutral"
        }
        for kw, accent in accents.items():
            if re.search(rf"\b{re.escape(kw)}\s*accent\b", text_lower) or re.search(rf"\baccent\s*{re.escape(kw)}\b", text_lower):
                requirements = requirements.model_copy(update={"accent": accent})
                break

        # Location
        locations = ["new york", "london", "san francisco", "tokyo", "paris", "berlin", "chicago", "boston"]
        for loc in locations:
            if re.search(rf"\b{re.escape(loc)}\b", text_lower):
                requirements = requirements.model_copy(update={"location": loc})
                break
        return requirements


class AssessmentPurposeExtractionRule(ExtractionRule):
    def apply(self, text: str, requirements: HiringRequirements) -> HiringRequirements:
        text_lower = text.lower()
        
        purposes = {
            "screening": ["screening", "hiring", "recruitment", "selection", "pre-employment", "pre employment", "new hire"],
            "promotion": ["promotion", "promote", "promotions", "career path", "career transition"],
            "development": ["development", "training", "grow", "coaching", "upskilling", "performance"],
            "internal mobility": ["internal mobility", "mobility", "transfer", "internal hire", "internal transfer"],
            "leadership succession": ["succession", "succession planning", "leadership pipeline", "leadership succession"],
            "graduate hiring": ["graduate", "graduates", "campus", "entry level", "entry-level", "graduate hiring"],
            "executive hiring": ["executive", "executives", "c-level", "director", "executive hiring"],
            "safety critical": ["safety critical", "safety-critical", "hazardous", "safety"]
        }
        
        for purpose, keywords in purposes.items():
            if any(re.search(rf"\b{re.escape(kw)}\b", text_lower) for kw in keywords):
                requirements = requirements.model_copy(update={"assessment_purpose": purpose})
                break
        return requirements


class RemoteOnsiteHybridExtractionRule(ExtractionRule):
    def apply(self, text: str, requirements: HiringRequirements) -> HiringRequirements:
        text_lower = text.lower()
        updates = {}
        if "hybrid" in text_lower:
            updates["hybrid"] = True
            updates["remote"] = True
            updates["onsite"] = False
        elif "onsite" in text_lower or "on-site" in text_lower:
            updates["onsite"] = True
            updates["remote"] = False
            updates["hybrid"] = False
        elif "remote" in text_lower:
            updates["remote"] = True
            updates["hybrid"] = False
            updates["onsite"] = False

        if "battery" in text_lower or "batteries" in text_lower or "technical + personality" in text_lower:
            updates["assessment_battery"] = True

        if updates:
            return requirements.model_copy(update=updates)
        return requirements
