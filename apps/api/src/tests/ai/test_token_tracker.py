import pytest
from src.services.ai.studio.token_tracker import TokenUsageTracker, TokenUsageRecord


class TestTokenUsageRecord:
    def test_total_tokens_is_sum(self):
        record = TokenUsageRecord(
            provider="openai", model_name="gpt-4o",
            prompt_tokens=10, completion_tokens=20,
        )
        assert record.total_tokens == 30

    def test_default_values(self):
        record = TokenUsageRecord(provider="openai", model_name="gpt-4")
        assert record.prompt_tokens == 0
        assert record.completion_tokens == 0
        assert record.total_tokens == 0
        assert record.request_id is None

    def test_with_request_id(self):
        record = TokenUsageRecord(
            provider="anthropic", model_name="claude-3-opus",
            prompt_tokens=100, completion_tokens=50, request_id="req_123",
        )
        assert record.request_id == "req_123"
        assert record.total_tokens == 150


class TestTokenUsageTracker:
    @pytest.fixture
    def tracker(self):
        return TokenUsageTracker()

    def test_record_returns_record(self, tracker):
        record = tracker.record("openai", "gpt-4o", prompt_tokens=5, completion_tokens=10)
        assert isinstance(record, TokenUsageRecord)
        assert record.total_tokens == 15

    def test_total_prompt_tokens(self, tracker):
        tracker.record("openai", "gpt-4o", prompt_tokens=10, completion_tokens=0)
        tracker.record("anthropic", "claude-3", prompt_tokens=20, completion_tokens=0)
        assert tracker.total_prompt_tokens == 30

    def test_total_completion_tokens(self, tracker):
        tracker.record("openai", "gpt-4o", prompt_tokens=0, completion_tokens=15)
        tracker.record("anthropic", "claude-3", prompt_tokens=0, completion_tokens=25)
        assert tracker.total_completion_tokens == 40

    def test_total_tokens(self, tracker):
        tracker.record("openai", "gpt-4o", prompt_tokens=10, completion_tokens=5)
        tracker.record("anthropic", "claude-3", prompt_tokens=20, completion_tokens=10)
        assert tracker.total_tokens == 45

    def test_records_property_returns_copy(self, tracker):
        tracker.record("openai", "gpt-4o")
        records = tracker.records
        records.clear()
        assert len(tracker.records) == 1

    def test_reset_clears_all(self, tracker):
        tracker.record("openai", "gpt-4o")
        tracker.record("anthropic", "claude-3")
        tracker.reset()
        assert tracker.total_tokens == 0
        assert len(tracker.records) == 0

    def test_summary(self, tracker):
        tracker.record("openai", "gpt-4o", prompt_tokens=10, completion_tokens=5)
        summary = tracker.summary()
        assert summary["total_prompt_tokens"] == 10
        assert summary["total_completion_tokens"] == 5
        assert summary["total_tokens"] == 15
        assert summary["request_count"] == 1

    def test_summary_with_multiple_records(self, tracker):
        tracker.record("openai", "gpt-4o", prompt_tokens=10, completion_tokens=5)
        tracker.record("anthropic", "claude-3", prompt_tokens=20, completion_tokens=10)
        summary = tracker.summary()
        assert summary["total_tokens"] == 45
        assert summary["request_count"] == 2

    def test_empty_summary(self, tracker):
        summary = tracker.summary()
        assert summary["total_tokens"] == 0
        assert summary["request_count"] == 0
