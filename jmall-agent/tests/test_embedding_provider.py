import pytest

from app.core.config import Settings
from app.services.embedding_provider_factory import EmbeddingProviderFactory
from app.services.embedding_service import EmbeddingService
from app.services.mock_embedding_provider import MockEmbeddingProvider
from app.services.openai_compatible_embedding_provider import OpenAICompatibleEmbeddingProvider


class WrongDimensionProvider:
    provider_name = "wrong-dimension"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


def test_mock_provider_returns_configured_dimension_vector():
    provider = MockEmbeddingProvider(dimension=12)

    embeddings = provider.embed_texts(["中文商品资料"])

    assert len(embeddings) == 1
    assert len(embeddings[0]) == 12


def test_embedding_service_uses_rag_embedding_dimension_for_mock_provider(monkeypatch):
    monkeypatch.delenv("RAG_EMBEDDING_PROVIDER", raising=False)
    settings = Settings(rag_embedding_provider="mock", rag_embedding_dimension="1024", _env_file=None)
    service = EmbeddingService(settings)

    embeddings, provider = service.embed_texts(["中文商品资料"])

    assert provider == "mock-embedding"
    assert len(embeddings) == 1
    assert len(embeddings[0]) == 1024


def test_embedding_service_rejects_dimension_mismatch(monkeypatch):
    monkeypatch.delenv("RAG_EMBEDDING_PROVIDER", raising=False)
    settings = Settings(rag_embedding_provider="mock", rag_embedding_dimension="1024", _env_file=None)
    service = EmbeddingService(settings)
    service.provider = WrongDimensionProvider()

    with pytest.raises(RuntimeError, match="RAG embedding 维度不匹配"):
        service.embed_texts(["中文商品资料"])


def test_openai_compatible_provider_without_api_key_has_clear_error():
    provider = OpenAICompatibleEmbeddingProvider(
        base_url="https://example.test/v1",
        api_key="",
        model="text-embedding",
    )

    with pytest.raises(RuntimeError, match="RAG_EMBEDDING_API_KEY 未配置"):
        provider.embed_texts(["hello"])


def test_provider_factory_selects_by_environment(monkeypatch):
    monkeypatch.delenv("RAG_EMBEDDING_PROVIDER", raising=False)
    mock_provider = EmbeddingProviderFactory(Settings(rag_embedding_provider="mock", _env_file=None)).create()
    real_provider = EmbeddingProviderFactory(
        Settings(
            rag_embedding_provider="openai-compatible",
            rag_embedding_base_url="https://example.test/v1",
            rag_embedding_api_key="sk-test",
            rag_embedding_model="text-embedding",
            _env_file=None,
        )
    ).create()

    assert isinstance(mock_provider, MockEmbeddingProvider)
    assert isinstance(real_provider, OpenAICompatibleEmbeddingProvider)
    assert real_provider.provider_name == "openai-compatible"
