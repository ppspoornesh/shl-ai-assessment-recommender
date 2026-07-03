from __future__ import annotations

from app.core.config import settings
from app.llm.openai_provider import OpenAIProvider


class GrokProvider(OpenAIProvider):
    """xAI Grok provider using the OpenAI-compatible chat completions API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        super().__init__(
            api_key=api_key if api_key is not None else settings.grok_api_key,
            model=model or settings.grok_model,
            base_url=base_url or settings.grok_base_url,
            timeout_seconds=timeout_seconds,
        )

    def generate(self, prompt: str) -> str:
        if not self._api_key:
            raise ValueError("GROK_API_KEY is required when LLM_PROVIDER=grok.")
        return super().generate(prompt)
