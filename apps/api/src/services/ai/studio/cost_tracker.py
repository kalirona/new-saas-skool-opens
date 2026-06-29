from __future__ import annotations

from typing import Optional

from src.services.ai.studio.token_tracker import TokenUsageRecord


PROVIDER_RATES: dict[str, dict[str, float]] = {
    "gemini": {
        "input_per_1k": 0.0005,
        "output_per_1k": 0.0015,
    },
    "openai": {
        "input_per_1k": 0.005,
        "output_per_1k": 0.015,
    },
    "anthropic": {
        "input_per_1k": 0.008,
        "output_per_1k": 0.024,
    },
    "openrouter": {
        "input_per_1k": 0.005,
        "output_per_1k": 0.015,
    },
    "local": {
        "input_per_1k": 0.0,
        "output_per_1k": 0.0,
    },
}


class CostTracker:
    def __init__(self):
        self._total_cost: float = 0.0

    def calculate(self, record: TokenUsageRecord) -> float:
        rates = PROVIDER_RATES.get(record.provider, PROVIDER_RATES["openai"])
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
