from typing import List, Tuple

from app.core.config import Settings
from app.services.embedding_provider_factory import EmbeddingProviderFactory


class EmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider = EmbeddingProviderFactory(settings).create()

    def embed_texts(self, texts: List[str]) -> Tuple[List[List[float]], str]:
        normalized = [item.strip() for item in texts if item and item.strip()]
        if not normalized:
            return [], self.provider.provider_name
        embeddings = self.provider.embed_texts(normalized)
        self._validate_dimensions(embeddings)
        return embeddings, self.provider.provider_name

    def _validate_dimensions(self, embeddings: List[List[float]]) -> None:
        expected = self.settings.resolved_embedding_dimension()
        for index, embedding in enumerate(embeddings):
            actual = len(embedding or [])
            if actual != expected:
                raise RuntimeError(
                    "RAG embedding 维度不匹配: "
                    f"provider={self.provider.provider_name}, "
                    f"index={index}, expected={expected}, actual={actual}. "
                    "请确认 RAG_EMBEDDING_MODEL、RAG_EMBEDDING_DIMENSION 与数据库 vector 维度一致。"
                )
