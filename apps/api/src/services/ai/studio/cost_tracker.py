from __future__ import annotations

from typing import Optional

from src.services.ai.studio.token_tracker import TokenUsageRecord


MODEL_RATES: dict[str, dict[str, float]] = {
    # OpenAI
    "gpt-4o": {"input_per_1k": 0.01, "output_per_1k": 0.03},
    "gpt-4o-mini": {"input_per_1k": 0.0015, "output_per_1k": 0.006},
    "gpt-4": {"input_per_1k": 0.03, "output_per_1k": 0.06},
    "gpt-4-turbo": {"input_per_1k": 0.01, "output_per_1k": 0.03},
    "gpt-3.5-turbo": {"input_per_1k": 0.0015, "output_per_1k": 0.002},
    # Anthropic
    "claude-sonnet-4-5": {"input_per_1k": 0.003, "output_per_1k": 0.015},
    "claude-3-opus": {"input_per_1k": 0.015, "output_per_1k": 0.075},
    "claude-3-sonnet": {"input_per_1k": 0.003, "output_per_1k": 0.015},
    "claude-3-haiku": {"input_per_1k": 0.00025, "output_per_1k": 0.00125},
    # Google Gemini
    "gemini-3.5-flash": {"input_per_1k": 0.0005, "output_per_1k": 0.0015},
    "gemini-1.5-pro": {"input_per_1k": 0.00125, "output_per_1k": 0.005},
    "gemini-1.5-flash": {"input_per_1k": 0.0005, "output_per_1k": 0.0015},
    # OpenRouter (defaults — actual rates depend on the upstream model)
    "openai/gpt-4o-mini": {"input_per_1k": 0.0015, "output_per_1k": 0.006},
    "openai/gpt-4o": {"input_per_1k": 0.01, "output_per_1k": 0.03},
}

# Fallback per-provider rates for unknown model names
PROVIDER_FALLBACK: dict[str, dict[str, float]] = {
    "openai": {"input_per_1k": 0.005, "output_per_1k": 0.015},
    "anthropic": {"input_per_1k": 0.008, "output_per_1k": 0.024},
    "gemini": {"input_per_1k": 0.0005, "output_per_1k": 0.0015},
    "openrouter": {"input_per_1k": 0.005, "output_per_1k": 0.015},
    "local": {"input_per_1k": 0.0, "output_per_1k": 0.0},
}


class CostTracker:
    def __init__(self):
        self._total_cost: float = 0.0

    def calculate(self, record: TokenUsageRecord) -> float:
        rates = (
            MODEL_RATES.get(record.model_name)
            or PROVIDER_FALLBACK.get(record.provider, PROVIDER_FALLBACK["openai"])
        )
        cost = (
            (record.prompt_tokens / 1000) * rates["input_per_1k"]
            + (record.completion_tokens / 1000) * rates["output_per_1k"]
        )
        self._total_cost += cost
        return round(cost, 6)

    @property
    def total_cost(self) -> float:
        return round(self._total_cost, 4)

    def reset(self):
        self._total_cost = 0.0
