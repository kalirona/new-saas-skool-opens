from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TokenUsageRecord:
    provider: str
    model_name: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    request_id: Optional[str] = None


class TokenUsageTracker:
    def __init__(self):
        self._records: list[TokenUsageRecord] = []

    def record(
        self,
        provider: str,
        model_name: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        request_id: Optional[str] = None,
    ) -> TokenUsageRecord:
        record = TokenUsageRecord(
            provider=provider,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            request_id=request_id,
        )
        self._records.append(record)
        return record

    @property
    def total_prompt_tokens(self) -> int:
        return sum(r.prompt_tokens for r in self._records)

    @property
    def total_completion_tokens(self) -> int:
        return sum(r.completion_tokens for r in self._records)

    @property
    def total_tokens(self) -> int:
        return sum(r.total_tokens for r in self._records)

    @property
    def records(self) -> list[TokenUsageRecord]:
        return list(self._records)

    def reset(self):
        self._records.clear()

    def summary(self) -> dict:
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "request_count": len(self._records),
        }
