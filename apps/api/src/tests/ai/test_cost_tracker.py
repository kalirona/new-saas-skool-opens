import pytest
from src.services.ai.studio.cost_tracker import CostTracker, MODEL_RATES, PROVIDER_FALLBACK
from src.services.ai.studio.token_tracker import TokenUsageRecord


class TestModelRates:
    def test_known_models_have_rates(self):
        assert "gpt-4o" in MODEL_RATES
        assert "gpt-4o-mini" in MODEL_RATES
        assert "claude-sonnet-4-5" in MODEL_RATES
        assert "gemini-3.5-flash" in MODEL_RATES
        assert "openai/gpt-4o-mini" in MODEL_RATES

    def test_rates_are_positive(self):
        for model, rates in MODEL_RATES.items():
            assert rates["input_per_1k"] >= 0
            assert rates["output_per_1k"] >= 0


class TestCostTrackerCalculate:
    @pytest.fixture
    def tracker(self):
        return CostTracker()

    def test_calculates_gpt4o_cost(self, tracker):
        record = TokenUsageRecord(
            provider="openai", model_name="gpt-4o",
            prompt_tokens=1000, completion_tokens=500,
        )
        cost = tracker.calculate(record)
        expected = (1000 / 1000) * 0.01 + (500 / 1000) * 0.03
        assert cost == round(expected, 6)

    def test_calculates_gpt4o_mini_cost(self, tracker):
        record = TokenUsageRecord(
            provider="openai", model_name="gpt-4o-mini",
            prompt_tokens=2000, completion_tokens=1000,
        )
        cost = tracker.calculate(record)
        expected = (2000 / 1000) * 0.0015 + (1000 / 1000) * 0.006
        assert cost == round(expected, 6)

    def test_falls_back_to_provider_rates(self, tracker):
        record = TokenUsageRecord(
            provider="openai", model_name="unknown-model-42",
            prompt_tokens=1000, completion_tokens=1000,
        )
        cost = tracker.calculate(record)
        expected = (1000 / 1000) * 0.005 + (1000 / 1000) * 0.015
        assert cost == round(expected, 6)

    def test_falls_back_to_default_for_unknown_provider(self, tracker):
        record = TokenUsageRecord(
            provider="nonexistent", model_name="unknown",
            prompt_tokens=1000, completion_tokens=1000,
        )
        cost = tracker.calculate(record)
        expected = (1000 / 1000) * 0.005 + (1000 / 1000) * 0.015
        assert cost == round(expected, 6)

    def test_zero_cost_for_local_model(self, tracker):
        record = TokenUsageRecord(
            provider="local", model_name="local-model",
            prompt_tokens=5000, completion_tokens=5000,
        )
        cost = tracker.calculate(record)
        assert cost == 0.0

    def test_zero_tokens_cost_zero(self, tracker):
        record = TokenUsageRecord(
            provider="openai", model_name="gpt-4o",
            prompt_tokens=0, completion_tokens=0,
        )
        cost = tracker.calculate(record)
        assert cost == 0.0

    def test_tracks_total_cost(self, tracker):
        tracker.calculate(TokenUsageRecord(provider="openai", model_name="gpt-4o", prompt_tokens=1000, completion_tokens=500))
        tracker.calculate(TokenUsageRecord(provider="openai", model_name="gpt-4o-mini", prompt_tokens=2000, completion_tokens=1000))
        assert tracker.total_cost > 0

    def test_reset(self, tracker):
        tracker.calculate(TokenUsageRecord(provider="openai", model_name="gpt-4o", prompt_tokens=1000, completion_tokens=500))
        tracker.reset()
        assert tracker.total_cost == 0.0

    def test_rounding_precision(self, tracker):
        record = TokenUsageRecord(
            provider="openai", model_name="gpt-4o-mini",
            prompt_tokens=1, completion_tokens=1,
        )
        cost = tracker.calculate(record)
        assert isinstance(cost, float)
        assert cost > 0

    def test_anthropic_rates(self, tracker):
        record = TokenUsageRecord(
            provider="anthropic", model_name="claude-3-haiku",
            prompt_tokens=1000, completion_tokens=500,
        )
        cost = tracker.calculate(record)
        expected = (1000 / 1000) * 0.00025 + (500 / 1000) * 0.00125
        assert cost == round(expected, 6)

    def test_gemini_rates(self, tracker):
        record = TokenUsageRecord(
            provider="gemini", model_name="gemini-1.5-pro",
            prompt_tokens=1000, completion_tokens=500,
        )
        cost = tracker.calculate(record)
        expected = (1000 / 1000) * 0.00125 + (500 / 1000) * 0.005
        assert cost == round(expected, 6)
