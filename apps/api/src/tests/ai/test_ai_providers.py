import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.ai.studio.interface import AIProvider, GenerationRequest, GenerationResult, TokenUsage
from src.services.ai.studio.providers import get_provider, list_providers, PROVIDER_MAP


class TestAIProviderInterface:
    def test_interface_is_abstract(self):
        with pytest.raises(TypeError):
            AIProvider()

    def test_concrete_provider(self):
        class Concrete(AIProvider):
            provider_name = "test"

            async def generate(self, request):
                return GenerationResult(content="ok", model_name="m", provider="test")

            async def generate_stream(self, request):
                yield "ok"

            async def count_tokens(self, text):
                return len(text.split())

        p = Concrete()
        assert p.provider_name == "test"

    def test_generation_request_defaults(self):
        req = GenerationRequest(user_prompt="Hello")
        assert req.temperature == 0.7
        assert req.max_tokens == 4096
        assert req.system_prompt is None
        assert req.model_name is None
        assert req.conversation_history is None
        assert req.output_type == str

    def test_generation_request_full(self):
        req = GenerationRequest(
            user_prompt="Hi", system_prompt="Be helpful", temperature=0.5,
            max_tokens=2048, model_name="gpt-4", output_type=str,
            conversation_history=[{"role": "user", "content": "Hi"}],
        )
        assert req.model_name == "gpt-4"
        assert len(req.conversation_history) == 1

    def test_generation_result_defaults(self):
        result = GenerationResult(content="Hello", model_name="gpt-4", provider="openai")
        assert result.usage == {}

    def test_token_usage_defaults(self):
        usage = TokenUsage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_get_usage_default(self):
        class Concrete(AIProvider):
            provider_name = "test"

            async def generate(self, request):
                return GenerationResult(content="", model_name="m", provider="test")

            async def generate_stream(self, request):
                yield ""

            async def count_tokens(self, text):
                return 0

        p = Concrete()
        usage = p.get_usage()
        assert usage.prompt_tokens == 0


class TestProviderRegistry:
    @pytest.fixture(autouse=True)
    def ensure_known_providers(self):
        assert "openai" in PROVIDER_MAP
        assert "anthropic" in PROVIDER_MAP
        assert "gemini" in PROVIDER_MAP
        assert "openrouter" in PROVIDER_MAP

    def test_get_provider_openai(self):
        provider = get_provider("openai")
        from src.services.ai.studio.providers.openai import OpenAIProvider
        assert isinstance(provider, OpenAIProvider)

    def test_get_provider_anthropic(self):
        provider = get_provider("anthropic")
        from src.services.ai.studio.providers.anthropic import AnthropicProvider
        assert isinstance(provider, AnthropicProvider)

    def test_get_provider_gemini(self):
        provider = get_provider("gemini")
        from src.services.ai.studio.providers.gemini import GeminiProvider
        assert isinstance(provider, GeminiProvider)

    def test_get_provider_openrouter(self):
        provider = get_provider("openrouter")
        from src.services.ai.studio.providers.openrouter import OpenRouterProvider
        assert isinstance(provider, OpenRouterProvider)

    def test_get_provider_with_config(self):
        provider = get_provider("openai", {"model": "gpt-4"})
        assert provider._model_name == "gpt-4"

    def test_get_provider_unknown_raises(self):
        with pytest.raises(ValueError, match="Unsupported AI provider"):
            get_provider("nonexistent")

    def test_provider_aliases(self):
        assert get_provider("google") is not None
        assert get_provider("local") is not None
        assert get_provider("ollama") is not None

    def test_list_providers(self):
        providers = list_providers()
        assert "openai" in providers
        assert "anthropic" in providers
        assert "gemini" in providers
        assert "google" in providers
        assert "local" in providers
        assert "ollama" in providers


class TestOpenAIProvider:
    @pytest.mark.asyncio
    async def test_generate(self):
        with patch("src.services.ai.studio.providers.openai.generate") as mock_generate:
            from src.services.ai.studio.providers.openai import OpenAIProvider
            provider = OpenAIProvider({"model": "gpt-4"})
            mock_generate.return_value = MagicMock(
                output="Hello, world!", usage={"prompt_tokens": 10, "completion_tokens": 5},
            )
            req = GenerationRequest(user_prompt="Say hello")
            result = await provider.generate(req)
            assert result.content == "Hello, world!"
            assert result.model_name == "gpt-4"
            assert result.provider == "openai"
            assert result.usage == {"prompt_tokens": 10, "completion_tokens": 5}

    @pytest.mark.asyncio
    async def test_generate_with_request_model_name(self):
        with patch("src.services.ai.studio.providers.openai.generate") as mock_generate:
            from src.services.ai.studio.providers.openai import OpenAIProvider
            provider = OpenAIProvider({"model": "gpt-4"})
            mock_generate.return_value = MagicMock(output="ok", usage={})
            req = GenerationRequest(user_prompt="Hi", model_name="gpt-4o")
            result = await provider.generate(req)
            assert result.model_name == "gpt-4o"

    @pytest.mark.asyncio
    async def test_generate_passes_all_params(self):
        with patch("src.services.ai.studio.providers.openai.generate") as mock_generate:
            from src.services.ai.studio.providers.openai import OpenAIProvider
            provider = OpenAIProvider()
            mock_generate.return_value = MagicMock(output="", usage={})
            req = GenerationRequest(
                user_prompt="Hi", system_prompt="Be nice", temperature=0.3,
                max_tokens=100, conversation_history=[{"role": "user", "content": "Hi"}], output_type=str,
            )
            await provider.generate(req)
            mock_generate.assert_called_once_with(
                model_name="gpt-4o-mini", user_prompt="Hi", system_prompt="Be nice",
                history=[{"role": "user", "content": "Hi"}], output_type=str,
                max_tokens=100, temperature=0.3,
            )

    @pytest.mark.asyncio
    async def test_generate_stream(self):
        with patch("src.services.ai.studio.providers.openai.generate_stream") as mock_stream:
            from src.services.ai.studio.providers.openai import OpenAIProvider
            provider = OpenAIProvider()
            async def _stream():
                yield "chunk1"
                yield "chunk2"
            mock_stream.return_value = _stream()
            req = GenerationRequest(user_prompt="Hi")
            chunks = []
            async for chunk in provider.generate_stream(req):
                chunks.append(chunk)
            assert chunks == ["chunk1", "chunk2"]

    @pytest.mark.asyncio
    async def test_count_tokens_with_tiktoken(self):
        with patch("src.services.ai.studio.providers.openai.tiktoken") as mock_tiktoken:
            from src.services.ai.studio.providers.openai import OpenAIProvider
            provider = OpenAIProvider()
            mock_enc = MagicMock()
            mock_enc.encode.return_value = [1, 2, 3, 4, 5]
            mock_tiktoken.get_encoding.return_value = mock_enc
            count = await provider.count_tokens("hello world")
            assert count == 5

    @pytest.mark.asyncio
    async def test_count_tokens_fallback(self):
        with patch("src.services.ai.studio.providers.openai.tiktoken") as mock_tiktoken:
            from src.services.ai.studio.providers.openai import OpenAIProvider
            provider = OpenAIProvider()
            mock_tiktoken.get_encoding.side_effect = ImportError("no tiktoken")
            count = await provider.count_tokens("hello world foo bar")
            assert count == 4


class TestAnthropicProvider:
    @pytest.mark.asyncio
    async def test_generate(self):
        with patch("src.services.ai.studio.providers.anthropic.generate") as mock_generate:
            from src.services.ai.studio.providers.anthropic import AnthropicProvider
            provider = AnthropicProvider({"model": "claude-3-opus"})
            mock_generate.return_value = MagicMock(output="Hello!", usage={})
            req = GenerationRequest(user_prompt="Hi")
            result = await provider.generate(req)
            assert result.content == "Hello!"
            assert result.provider == "anthropic"

    @pytest.mark.asyncio
    async def test_generate_default_model(self):
        with patch("src.services.ai.studio.providers.anthropic.generate") as mock_generate:
            from src.services.ai.studio.providers.anthropic import AnthropicProvider
            provider = AnthropicProvider()
            mock_generate.return_value = MagicMock(output="", usage={})
            req = GenerationRequest(user_prompt="Hi")
            await provider.generate(req)
            mock_generate.assert_called_once()
            assert mock_generate.call_args[1]["model_name"] == "claude-sonnet-4-5"

    @pytest.mark.asyncio
    async def test_count_tokens_with_anthropic_sdk(self):
        with patch("src.services.ai.studio.providers.anthropic.Anthropic") as mock_anthropic:
            from src.services.ai.studio.providers.anthropic import AnthropicProvider
            provider = AnthropicProvider()
            mock_client = MagicMock()
            mock_client.count_tokens.return_value = 42
            mock_anthropic.return_value = mock_client
            count = await provider.count_tokens("hello world")
            assert count == 42

    @pytest.mark.asyncio
    async def test_count_tokens_fallback(self):
        with patch("src.services.ai.studio.providers.anthropic.Anthropic") as mock_anthropic:
            from src.services.ai.studio.providers.anthropic import AnthropicProvider
            provider = AnthropicProvider()
            mock_anthropic.side_effect = Exception("SDK not available")
            count = await provider.count_tokens("hello world foo bar")
            assert count == 4

    @pytest.mark.asyncio
    async def test_generate_passes_history(self):
        with patch("src.services.ai.studio.providers.anthropic.generate") as mock_generate:
            from src.services.ai.studio.providers.anthropic import AnthropicProvider
            provider = AnthropicProvider()
            mock_generate.return_value = MagicMock(output="", usage={})
            req = GenerationRequest(
                user_prompt="Hi", system_prompt="Be concise",
                conversation_history=[{"role": "user", "content": "Hello"}],
            )
            await provider.generate(req)
            mock_generate.assert_called_once()
            assert mock_generate.call_args[1]["system_prompt"] == "Be concise"
            assert mock_generate.call_args[1]["history"] == [{"role": "user", "content": "Hello"}]


class TestGeminiProvider:
    @pytest.mark.asyncio
    async def test_generate(self):
        with patch("src.services.ai.studio.providers.gemini.generate") as mock_generate:
            from src.services.ai.studio.providers.gemini import GeminiProvider
            provider = GeminiProvider({"model": "gemini-1.5-pro"})
            mock_generate.return_value = MagicMock(output="Hi there!", usage={})
            req = GenerationRequest(user_prompt="Say hi")
            result = await provider.generate(req)
            assert result.content == "Hi there!"
            assert result.provider == "gemini"

    @pytest.mark.asyncio
    async def test_generate_default_model(self):
        with patch("src.services.ai.studio.providers.gemini.generate") as mock_generate:
            from src.services.ai.studio.providers.gemini import GeminiProvider
            provider = GeminiProvider()
            mock_generate.return_value = MagicMock(output="", usage={})
            req = GenerationRequest(user_prompt="Hi")
            await provider.generate(req)
            assert mock_generate.call_args[1]["model_name"] == "gemini-3.5-flash"


class TestOpenRouterProvider:
    @pytest.mark.asyncio
    async def test_generate(self):
        with patch("src.services.ai.studio.providers.openrouter.generate") as mock_generate:
            from src.services.ai.studio.providers.openrouter import OpenRouterProvider
            provider = OpenRouterProvider({"model": "openai/gpt-4o"})
            mock_generate.return_value = MagicMock(output="Response", usage={})
            req = GenerationRequest(user_prompt="Hi")
            result = await provider.generate(req)
            assert result.content == "Response"
            assert result.provider == "openrouter"

    @pytest.mark.asyncio
    async def test_default_model(self):
        with patch("src.services.ai.studio.providers.openrouter.generate") as mock_generate:
            from src.services.ai.studio.providers.openrouter import OpenRouterProvider
            provider = OpenRouterProvider()
            mock_generate.return_value = MagicMock(output="", usage={})
            req = GenerationRequest(user_prompt="Hi")
            await provider.generate(req)
            assert mock_generate.call_args[1]["model_name"] == "openai/gpt-4o-mini"
