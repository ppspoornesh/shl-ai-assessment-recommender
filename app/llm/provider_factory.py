from __future__ import annotations

import logging
import os

from app.core.config import settings
from app.llm.base_provider import BaseLLMProvider
from app.llm.grok_provider import GrokProvider
from app.llm.mock_provider import MockProvider
from app.llm.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Builds the active LLM provider from environment configuration."""

    @staticmethod
    def create_provider() -> BaseLLMProvider:
        provider_name = os.getenv("LLM_PROVIDER", settings.llm_provider).strip().lower()

        if provider_name == "grok":
            logger.info("Using Grok LLM provider.")
            return GrokProvider()

        if provider_name == "openai":
            logger.info("Using OpenAI LLM provider.")
            return OpenAIProvider()

        if provider_name != "mock":
            logger.warning("Unknown LLM_PROVIDER=%s; falling back to Mock provider.", provider_name)

        logger.info("Using Mock LLM provider.")
        return MockProvider()
