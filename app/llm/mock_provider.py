from __future__ import annotations

import re

from app.llm.base_provider import BaseLLMProvider


class MockProvider(BaseLLMProvider):
    """Deterministic provider used for local development and tests."""

    def generate(self, prompt: str) -> str:
        if "Clarification question:" in prompt or "Clarification needed:" in prompt:
            question = self._extract_section(prompt, "Clarification question:") or self._extract_section(prompt, "Clarification needed:")
            return question or "Based on the hiring requirements you've shared, I need a few more details before recommending the best SHL assessments. Could you please specify the target role or key technical skills?"

        if "Comparison summary:" in prompt or "Comparison Details:" in prompt:
            recs_text = self._extract_section(prompt, "Recommendations:")
            role_title = "the role"
            if "java" in recs_text.lower():
                role_title = "Java Developer"
            elif "python" in recs_text.lower():
                role_title = "Python Developer"

            is_senior = "seniority" in recs_text.lower() or "senior" in recs_text.lower()
            prefix = f"For a {'Senior ' if is_senior else ''}{role_title}"
            return f"Here is a comparison of the recommended assessments to help you select the best fit for your team. {prefix}, the main differences lie in the depth of technical knowledge required and the target job levels."

        if "Recommendations:" in prompt and "None" not in self._extract_section(prompt, "Recommendations:"):
            recs_text = self._extract_section(prompt, "Recommendations:")
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
