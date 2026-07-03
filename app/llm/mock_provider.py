from __future__ import annotations

import re

from app.llm.base_provider import BaseLLMProvider


class MockProvider(BaseLLMProvider):
    """Deterministic provider used for local development and tests."""

    def generate(self, prompt: str) -> str:
        intent_match = re.search(r"Intent:\s*(?P<intent>[a-zA-Z_]+)", prompt)
        intent = intent_match.group("intent").strip() if intent_match else ""

        # Clarification Check
        if "Clarification question:" in prompt or "Clarification needed:" in prompt:
            question = self._extract_section(prompt, "Clarification question:") or self._extract_section(prompt, "Clarification needed:")
            return question or "Based on the hiring requirements you've shared, I need a few more details before recommending the best SHL assessments. Could you please specify the target role or key technical skills?"

        # Greeting Check
        if intent == "greeting" or "hello" in prompt.lower()[:20] or "hi" in prompt.lower()[:20]:
            return "Hello! I am your SHL assessment advisor. I can help you select, compare, and customize the perfect set of assessments for your hiring, promotion, or development needs. To get started, what role and seniority level are you looking to assess?"

        # Comparison Check
        if intent == "compare_options" or "Comparison summary:" in prompt or "Comparison Details:" in prompt:
            recs_text = self._extract_section(prompt, "Recommendations:")
            role_title = "the role"
            if "java" in recs_text.lower():
                role_title = "Java Developer"
            elif "python" in recs_text.lower():
                role_title = "Python Developer"

            is_senior = "seniority" in recs_text.lower() or "senior" in recs_text.lower()
            prefix = f"For a {'Senior ' if is_senior else ''}{role_title}"
            return f"Here is a comparison of the recommended assessments to help you select the best fit for your team. {prefix}, the main differences lie in the depth of technical knowledge required and the target job levels."

        # Battery Check
        if intent == "assessment_battery_request" or "battery" in prompt.lower() or "battery" in intent:
            return "Based on the hiring requirements you've shared, I have configured a balanced SHL assessment battery. This suite integrates cognitive aptitude, occupational personality characteristics, and specific technical skills to ensure a holistic evaluation of the candidate."

        # Standard recommendations with potential fallback/no direct
        if "Recommendations:" in prompt and "None" not in self._extract_section(prompt, "Recommendations:"):
            recs_text = self._extract_section(prompt, "Recommendations:")

            # Check for fallback
            if "no direct" in recs_text.lower() or "fallback" in recs_text.lower() or "alternative" in recs_text.lower():
                return "Based on the hiring requirements you've shared, please note that no direct assessment exists in the SHL catalog for this technology. I have identified the closest capability-based alternatives to evaluate relevant engineering proficiency and core logic."

            role_title = "your role"
            if "java" in recs_text.lower():
                role_title = "Java Developer"
            elif "python" in recs_text.lower():
                role_title = "Python Developer"

            is_senior = "seniority" in recs_text.lower() or "senior" in recs_text.lower()
            prefix = f"For a {'Senior ' if is_senior else ''}{role_title}"
            return f"Based on the hiring requirements you've shared, I have identified the top SHL assessments for this position. {prefix}, the strongest match is designed to evaluate core competencies and relevant technical capabilities."

        return "Based on the hiring requirements you've shared, I could not find any matching SHL assessments in the catalog. Please let me know if you would like to adjust the criteria."

    def _extract_section(self, prompt: str, label: str) -> str:
        pattern = rf"{re.escape(label)}\s*(?P<value>.*?)(?:\n\n|$)"
        match = re.search(pattern, prompt, flags=re.DOTALL)
        if not match:
            return ""
        return match.group("value").strip()
