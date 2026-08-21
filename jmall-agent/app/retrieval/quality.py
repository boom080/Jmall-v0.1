"""RAG retrieval quality evaluation using LLM-as-Judge.

Provides:
- RAGQualityMetrics: Structured quality metrics (hit_rate, MRR, NDCG, etc.)
- RAGJudge: Uses LLM to score relevance of each retrieved document (1-5 scale)
- compute_metrics_from_judgments: Compute metrics from pre-existing judgments

Usage:
    judge = RAGJudge(provider_factory, cost_tracker)
    metrics = await judge.evaluate(query, documents, kb_id)
    print(f"Hit rate: {metrics.hit_rate:.2%}, MRR: {metrics.mrr:.3f}")
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RAGQualityMetrics:
    """Quality metrics for a single RAG retrieval evaluation."""

    query: str = ""
    knowledge_base_id: str = ""
    total_retrieved: int = 0
    avg_relevance: float = 0.0
    hit_rate: float = 0.0
    mrr: float = 0.0
    ndcg: float = 0.0
    precision_at_k: float = 0.0
    judgments: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "knowledge_base_id": self.knowledge_base_id,
            "total_retrieved": self.total_retrieved,
            "avg_relevance": round(self.avg_relevance, 2),
            "hit_rate": round(self.hit_rate, 4),
            "mrr": round(self.mrr, 4),
            "ndcg": round(self.ndcg, 4),
            "precision_at_k": round(self.precision_at_k, 4),
            "judgments": self.judgments,
        }


class RAGJudge:
    """LLM-as-Judge for scoring relevance of retrieved documents.

    Uses an LLM (typically a cheap model like deepseek-chat) to judge how
    relevant each retrieved chunk is to the original query. Falls back to
    keyword overlap scoring when the LLM is unavailable.
    """

    # Threshold: relevance >= this value is considered a "hit"
    HIT_THRESHOLD = 3

    def __init__(
        self,
        provider_factory=None,
        cost_tracker=None,
    ) -> None:
        self.provider_factory = provider_factory
        self.cost_tracker = cost_tracker

    def score_relevance(self, query: str, document: str) -> int:
        """Score a single document's relevance to a query (1-5).

        Args:
            query: The original search query.
            document: The retrieved document/chunk content.

        Returns:
            Relevance score: 1 (irrelevant) to 5 (perfect match).
        """
        # Use LLM-based scoring
        try:
            prompt = (
                f"请评估以下文档片段与查询的相关性，打1-5分：\n\n"
                f"查询：{query}\n\n"
                f"文档片段：{document[:1500]}\n\n"
                f"评分标准：\n"
                f"1 - 完全不相关\n"
                f"2 - 略微相关（提到了相关话题但无法回答查询）\n"
                f"3 - 相关（包含部分有用信息）\n"
                f"4 - 高度相关（大部分内容直接回答查询）\n"
                f"5 - 完全匹配（精确回答了查询问题）\n\n"
                f"只输出数字（1-5），不要输出其他内容。"
            )

            messages = [
                {"role": "system", "content": "你是RAG检索质量评估专家。只输出1-5的数字评分。"},
                {"role": "user", "content": prompt},
            ]

            result = self.provider_factory.chat(
                provider_name="deepseek",
                model_name="deepseek-chat",
                messages=messages,
                temperature=0.0,
                max_tokens=10,
            )

            # Track cost for the judge call
            if self.cost_tracker:
                try:
                    self.cost_tracker.track(
                        provider=result.get("provider", "unknown"),
                        model=result.get("model", "unknown"),
                        input_tokens=result.get("input_tokens", 0),
                        output_tokens=result.get("output_tokens", 0),
                        agent_type="rag_judge",
                    )
                except Exception:
                    logger.debug("Failed to track RAG judge cost", exc_info=True)

            content = result.get("content", "").strip()
            # Extract the first digit found
            for char in content:
                if char.isdigit():
                    score = int(char)
                    if 1 <= score <= 5:
                        return score
            # Fallback: default to neutral
            return 3
        except Exception as exc:
            logger.warning("LLM judge failed for query '%s', using keyword fallback: %s", query[:50], exc)
            return self._keyword_score(query, document)

    def _keyword_score(self, query: str, document: str) -> int:
        """Simple keyword overlap scoring as fallback when LLM is unavailable.

        Computes Jaccard-like overlap between query terms and document terms.
        """
        # Extract meaningful tokens (simple whitespace + CJK char split)
        query_chars = set(query.lower().replace(" ", ""))
        doc_chars = set(document.lower().replace(" ", ""))

        if not query_chars:
            return 1

        # Character-level overlap for CJK support
        overlap = len(query_chars & doc_chars)
        ratio = overlap / len(query_chars)

        if ratio >= 0.6:
            return 5
        elif ratio >= 0.4:
            return 4
        elif ratio >= 0.2:
            return 3
        elif ratio >= 0.1:
            return 2
        return 1

    async def evaluate(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        knowledge_base_id: str = "",
    ) -> RAGQualityMetrics:
        """Evaluate retrieval quality for a query against retrieved documents.

        Scores each document's relevance using the LLM judge, then computes
        standard IR metrics: hit_rate, MRR, NDCG, precision@k.

        Args:
            query: The original search query.
            documents: Retrieved documents with 'content' and 'score' fields.
            knowledge_base_id: The knowledge base ID (for reporting).

        Returns:
            RAGQualityMetrics with all computed metrics and per-document judgments.
        """
        metrics = RAGQualityMetrics(
            query=query,
            knowledge_base_id=knowledge_base_id,
            total_retrieved=len(documents),
        )

        if not documents:
            return metrics

        judgments = []

        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            similarity_score = float(doc.get("score", 0.0))

            relevance = self.score_relevance(query, content)

            judgments.append({
                "rank": i + 1,
                "chunk_id": doc.get("chunkId", ""),
                "document_id": doc.get("documentId", ""),
                "similarity_score": round(similarity_score, 4),
                "relevance": relevance,
                "content_preview": content[:200],
            })

        metrics.judgments = judgments

        # Compute aggregate metrics
        relevances = [j["relevance"] for j in judgments]
        n = len(relevances)

        # Average relevance
        metrics.avg_relevance = sum(relevances) / n if n > 0 else 0.0

        # Hit rate: fraction with relevance >= threshold
        hits = sum(1 for r in relevances if r >= self.HIT_THRESHOLD)
        metrics.hit_rate = hits / n if n > 0 else 0.0

        # MRR: reciprocal rank of first relevant document
        for i, r in enumerate(relevances):
            if r >= self.HIT_THRESHOLD:
                metrics.mrr = 1.0 / (i + 1)
                break

        # NDCG: using relevance as the gain value
        dcg = sum(
            (2 ** r - 1) / math.log2(i + 2)
            for i, r in enumerate(relevances)
        )
        # Ideal DCG: perfect ranking (all 5s)
        idcg = sum(
            (2 ** 5 - 1) / math.log2(i + 2)
            for i in range(n)
        )
        metrics.ndcg = dcg / idcg if idcg > 0 else 0.0

        # Precision@k
        metrics.precision_at_k = hits / n if n > 0 else 0.0

        logger.info(
            "RAG quality eval for '%s': avg_relevance=%.2f hit_rate=%.2f mrr=%.3f ndcg=%.3f",
            query[:50], metrics.avg_relevance, metrics.hit_rate, metrics.mrr, metrics.ndcg,
        )

        return metrics


def compute_metrics_from_judgments(
    query: str,
    judgments: List[int],
    knowledge_base_id: str = "",
) -> RAGQualityMetrics:
    """Compute metrics from pre-existing relevance judgments (no LLM calls).

    Useful for testing or when ground-truth judgments are available.

    Args:
        query: The original search query.
        judgments: List of relevance scores (1-5), one per retrieved document.
        knowledge_base_id: The knowledge base ID (for reporting).

    Returns:
        RAGQualityMetrics with computed metrics.
    """
    metrics = RAGQualityMetrics(
        query=query,
        knowledge_base_id=knowledge_base_id,
        total_retrieved=len(judgments),
        judgments=[
            {"rank": i + 1, "relevance": j}
            for i, j in enumerate(judgments)
        ],
    )

    if not judgments:
        return metrics

    n = len(judgments)
    metrics.avg_relevance = sum(judgments) / n
    hits = sum(1 for j in judgments if j >= 3)
    metrics.hit_rate = hits / n

    for i, j in enumerate(judgments):
        if j >= 3:
            metrics.mrr = 1.0 / (i + 1)
            break

    dcg = sum((2 ** j - 1) / math.log2(i + 2) for i, j in enumerate(judgments))
    idcg = sum((2 ** 5 - 1) / math.log2(i + 2) for i in range(n))
    metrics.ndcg = dcg / idcg if idcg > 0 else 0.0
    metrics.precision_at_k = hits / n

    return metrics
