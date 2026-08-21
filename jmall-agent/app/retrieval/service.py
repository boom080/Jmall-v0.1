import logging
from typing import Any, Dict, List, Optional

from app.retrieval.quality import RAGJudge, RAGQualityMetrics
from app.retrieval.rag_retriever import RagRetriever

logger = logging.getLogger(__name__)


class RetrievalService(RagRetriever):
    """RAG retrieval service with optional quality evaluation.

    Extends RagRetriever with LLM-as-Judge quality measurement capabilities.
    """

    async def evaluate_quality(
        self,
        query: str,
        knowledge_base_id: str,
        top_k: int = 5,
        provider_factory=None,
        cost_tracker=None,
    ) -> RAGQualityMetrics:
        """Evaluate RAG retrieval quality for a query.

        Runs retrieval, then scores each result's relevance using LLM-as-Judge.

        Args:
            query: The search query to evaluate.
            knowledge_base_id: The knowledge base to search against.
            top_k: Number of documents to retrieve.
            provider_factory: Provider factory for LLM judge calls.
            cost_tracker: Cost tracker for judge API costs.

        Returns:
            RAGQualityMetrics with relevance scores and aggregate metrics.
        """
        # Step 1: Run retrieval
        documents: List[Dict[str, Any]] = self.retrieve(
            knowledge_base_id=knowledge_base_id,
            query=query,
            top_k=top_k,
        )

        if not documents:
            logger.info("RAG quality eval: no documents retrieved for '%s'", query[:50])
            return RAGQualityMetrics(
                query=query,
                knowledge_base_id=knowledge_base_id,
                total_retrieved=0,
            )

        # Step 2: Score relevance using LLM judge (or keyword fallback)
        judge = RAGJudge(
            provider_factory=provider_factory,
            cost_tracker=cost_tracker,
        )
        metrics = await judge.evaluate(query, documents, knowledge_base_id)
        return metrics
