from typing import Any, Dict, List, Optional

from app.core.config import Settings
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.services.embedding_service import EmbeddingService


def assess_rag_quality(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Simple heuristics-based RAG quality assessment.

    Evaluates retrieval quality from the returned chunk scores without
    any extra LLM calls.  The existing scoring (cosine similarity / dot
    product) is *higher is better*.

    Returns a lightweight dict meant to be stored in the orchestration
    state (``rag_quality``) so downstream agents and observability
    tooling can inspect retrieval health.

    Thresholds (cosine-similarity scale, roughly 0–1):
        * top1 >= 0.8  → high
        * top1 >= 0.5  → medium
        * top1 >  0    → low
        * no chunks    → empty
    """
    if not chunks:
        return {
            "quality": "empty",
            "top1_score": 0.0,
            "avg_score": 0.0,
            "result_count": 0,
        }

    scores = [float(c.get("score") or 0) for c in chunks]
    top1 = scores[0]
    avg = sum(scores) / len(scores)

    if top1 >= 0.8:
        quality = "high"
    elif top1 >= 0.5:
        quality = "medium"
    else:
        quality = "low"

    return {
        "quality": quality,
        "top1_score": round(top1, 4),
        "avg_score": round(avg, 4),
        "result_count": len(chunks),
    }


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
