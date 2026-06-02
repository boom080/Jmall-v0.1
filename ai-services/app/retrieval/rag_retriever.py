from typing import Any, Dict, List, Optional

from app.core.config import Settings
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.services.embedding_service import EmbeddingService


class RagRetriever:
    def __init__(
        self,
        settings: Settings,
        repository: KnowledgeBaseRepository,
        embedding_service: EmbeddingService,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.embedding_service = embedding_service

    def retrieve(
        self,
        knowledge_base_id: Optional[str],
        query: str,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        if not self.settings.ai_rag_enabled:
            return []
        if not knowledge_base_id or not query.strip():
            return []

        query_embeddings, provider = self.embedding_service.embed_texts([query])
        query_embedding = query_embeddings[0] if query_embeddings else []
        if not query_embedding:
            return []

        chunks = self.repository.search_chunks(
            knowledge_base_id=knowledge_base_id,
            query_embedding=query_embedding,
            top_k=top_k or self.settings.rag_top_k or self.settings.ai_rag_top_k,
            min_score=self.settings.rag_min_score,
        )
        for chunk in chunks:
            chunk.setdefault("embeddingProvider", provider)
        return chunks
