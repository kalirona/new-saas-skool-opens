from src.services.ai.studio.providers.gemini import GeminiProvider
from src.services.ai.studio.providers.openai import OpenAIProvider
from src.services.ai.studio.providers.anthropic import AnthropicProvider
from src.services.ai.studio.providers.openrouter import OpenRouterProvider

PROVIDER_MAP: dict[str, type] = {
    "gemini": GeminiProvider,
    "google": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "openrouter": OpenRouterProvider,
    "local": OpenAIProvider,
    "ollama": OpenAIProvider,
}


def get_provider(provider_id: str, config: dict | None = None) -> object:
    cls = PROVIDER_MAP.get(provider_id)
    if not cls:
        raise ValueError(f"Unsupported AI provider: {provider_id}")
    return cls(config or {})


def list_providers() -> list[str]:
    return list(PROVIDER_MAP.keys())


__all__ = ["get_provider", "list_providers", "PROVIDER_MAP"]
