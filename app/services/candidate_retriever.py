from __future__ import annotations

from rapidfuzz import fuzz

from app.models.catalog import CatalogEntry
from app.models.requirements import HiringRequirements
from app.services.catalog_loader import CatalogLoader


TECH_FALLBACKS = {
    "rust": {
        "alternatives": ["Linux Programming (General)", "Smart Interview Live Coding", "C++ Programming (New)"],
        "reason": "No direct Rust assessment exists in the SHL catalog. We recommend C++ Programming and Linux Programming as the closest alternatives for systems programming and Smart Interview Live Coding for general coding proficiency."
    },
    "go": {
        "alternatives": ["Smart Interview Live Coding", "Linux Programming (General)"],
        "reason": "No direct Go/Golang assessment exists in the SHL catalog. We recommend Smart Interview Live Coding to evaluate hands-on backend development and Linux Programming for backend systems proficiency."
    },
    "golang": {
        "alternatives": ["Smart Interview Live Coding", "Linux Programming (General)"],
        "reason": "No direct Go/Golang assessment exists in the SHL catalog. We recommend Smart Interview Live Coding to evaluate hands-on backend development and Linux Programming for backend systems proficiency."
    },
    "typescript": {
        "alternatives": ["JavaScript (New)", "Smart Interview Live Coding"],
        "reason": "No direct TypeScript assessment exists in the SHL catalog. We recommend the JavaScript assessment as the closest technology match and Smart Interview Live Coding for general coding proficiency."
    },
    "vue": {
        "alternatives": ["ReactJS (New)", "Automata Front End", "JavaScript (New)"],
        "reason": "No direct Vue.js assessment exists in the SHL catalog. We recommend ReactJS or Automata Front End as the closest modern frontend technology alternatives."
    },
    "vuejs": {
        "alternatives": ["ReactJS (New)", "Automata Front End", "JavaScript (New)"],
        "reason": "No direct Vue.js assessment exists in the SHL catalog. We recommend ReactJS or Automata Front End as the closest modern frontend technology alternatives."
    },
    "swift": {
        "alternatives": ["Automata Front End", "Smart Interview Live Coding"],
        "reason": "No direct Swift or iOS-specific assessment exists in the SHL catalog. We recommend Automata Front End and Smart Interview Live Coding to evaluate logic and UI coding proficiency."
    },
    "kotlin": {
        "alternatives": ["Core Java (Advanced Level) (New)", "Android Development (New)"],
        "reason": "No direct Kotlin assessment exists in the SHL catalog. We recommend Android Development and Core Java as the closest alternatives to evaluate mobile and object-oriented programming skills."
    }
}


class CandidateRetriever:
    """Selects candidate assessments from the catalog for a given requirement set."""

    def __init__(self, catalog_loader: CatalogLoader | None = None) -> None:
        from app.services.catalog_loader import get_catalog_loader
        self._catalog_loader = catalog_loader or get_catalog_loader()

    def retrieve(self, requirements: HiringRequirements) -> list[CatalogEntry]:
        if not requirements.role and not requirements.technical_skills and not requirements.industry:
            return []

        candidates = []
        for entry in self._catalog_loader.catalog:
            if self._matches_requirements(entry, requirements):
                candidates.append(entry)

        # 1. Check for fallback mappings
        fallback_names = set()
        for skill in requirements.technical_skills:
            skill_lower = skill.lower()
            if skill_lower in TECH_FALLBACKS:
                fallback_names.update(TECH_FALLBACKS[skill_lower]["alternatives"])

        # 2. Check if assessment battery is requested, inject standard components
        if requirements.assessment_battery:
            battery_standards = [
                "Occupational Personality Questionnaire OPQ32r",
                "SHL Verify Interactive G+",
                "Verify - General Ability Screen",
                "Verify - Deductive Reasoning",
                "Verify - Inductive Reasoning (2014)"
            ]
            fallback_names.update(battery_standards)

        # If we have fallback/battery names to fetch, retrieve them directly by exact name matching
        if fallback_names:
            existing_ids = {c.entity_id for c in candidates}
            for entry in self._catalog_loader.catalog:
                if entry.name in fallback_names and entry.entity_id not in existing_ids:
                    candidates.append(entry)

        return candidates

    def _matches_requirements(self, entry: CatalogEntry, requirements: HiringRequirements) -> bool:
        if self._matches_metadata(entry, requirements):
            return True

        if self._matches_fuzzy(entry, requirements):
            return True

        return self._matches_keywords(entry, requirements)

    def _matches_metadata(self, entry: CatalogEntry, requirements: HiringRequirements) -> bool:
        if requirements.role and self._looks_like_role_match(entry, requirements.role):
            return True

        if requirements.technical_skills and self._matches_skills(entry, requirements.technical_skills):
            return True

        if not requirements.role and not requirements.technical_skills:
            if requirements.seniority and self._matches_seniority(entry, requirements.seniority):
                return True
            if requirements.industry and self._matches_industry(entry, requirements.industry):
                return True

        return False

    def _looks_like_role_match(self, entry: CatalogEntry, role: str) -> bool:
        entry_text = self._build_search_text(entry).lower()
        role_terms = [role.lower()]
        if "software" in role.lower() and "engineer" in role.lower():
            role_terms.append("engineering")
        return any(term in entry_text for term in role_terms)

    def _matches_skills(self, entry: CatalogEntry, technical_skills: list[str]) -> bool:
        entry_skills = {skill.lower() for skill in entry.skills}
        return any(skill.lower() in entry_skills for skill in technical_skills)

    def _matches_seniority(self, entry: CatalogEntry, seniority: str) -> bool:
        normalized_seniority = seniority.lower()
        return any(normalized_seniority in value.lower() for value in entry.job_levels)

    def _matches_industry(self, entry: CatalogEntry, industry: str) -> bool:
        normalized_industry = industry.lower()
        return any(normalized_industry == value.lower() for value in entry.target_industries)

    def _matches_fuzzy(self, entry: CatalogEntry, requirements: HiringRequirements) -> bool:
        search_text = self._build_search_text(entry)
        query_parts: list[str] = []
        if requirements.role:
            query_parts.append(requirements.role)
        if requirements.technical_skills:
            query_parts.extend(requirements.technical_skills)

        if not query_parts:
            return False

        query = " ".join(query_parts)
        score = fuzz.partial_ratio(query.lower(), search_text.lower())
        return score >= 55

    def _matches_keywords(self, entry: CatalogEntry, requirements: HiringRequirements) -> bool:
        entry_text = self._build_search_text(entry).lower()
        normalized_requirements = [requirements.role.lower()] if requirements.role else []
        normalized_requirements.extend(skill.lower() for skill in requirements.technical_skills)

        return any(term in entry_text for term in normalized_requirements if term)

    def _build_search_text(self, entry: CatalogEntry) -> str:
        parts = [entry.name, entry.description, " ".join(entry.skills), " ".join(entry.job_levels), " ".join(entry.target_industries)]
        return " ".join(part for part in parts if part)
