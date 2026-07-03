from app.llm.grok_provider import GrokProvider
from app.llm.mock_provider import MockProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.provider_factory import ProviderFactory


def test_mock_provider_selected_correctly(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    provider = ProviderFactory.create_provider()

    assert isinstance(provider, MockProvider)


def test_grok_provider_selected_correctly(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "grok")

    provider = ProviderFactory.create_provider()

    assert isinstance(provider, GrokProvider)


def test_openai_provider_selected_correctly(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")

    provider = ProviderFactory.create_provider()

    assert isinstance(provider, OpenAIProvider)
    assert not isinstance(provider, GrokProvider)


def test_default_provider_is_mock(monkeypatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    provider = ProviderFactory.create_provider()

    assert isinstance(provider, MockProvider)


def test_unknown_provider_falls_back_to_mock(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "unknown")

    provider = ProviderFactory.create_provider()

    assert isinstance(provider, MockProvider)
