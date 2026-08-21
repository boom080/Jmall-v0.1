from typing import Protocol

from app.core.config import Settings
from app.services.mock_embedding_provider import MockEmbeddingProvider
from app.services.openai_compatible_embedding_provider import OpenAICompatibleEmbeddingProvider


class EmbeddingProvider(Protocol):
    provider_name: str

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...


class EmbeddingProviderFactory:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create(self) -> EmbeddingProvider:
        provider = (self.settings.rag_embedding_provider or "").strip().lower()
        if provider in ("", "mock", "mock-embedding", "dev"):
            return MockEmbeddingProvider(self.settings.resolved_embedding_dimension())
        if provider in ("openai", "openai-compatible", "qwen", "dashscope", "bailian"):
            return OpenAICompatibleEmbeddingProvider(
                base_url=self.settings.rag_embedding_base_url,
                api_key=self.settings.rag_embedding_api_key,
                model=self.settings.rag_embedding_model,
                timeout_seconds=self.settings.ai_timeout_seconds,
                dimension=self.settings.resolved_embedding_dimension(),
            )
        raise ValueError(f"不支持的 RAG_EMBEDDING_PROVIDER: {self.settings.rag_embedding_provider}")
