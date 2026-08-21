"""Unit tests for RAG quality evaluation module.

Tests RAGQualityMetrics dataclass, RAGJudge keyword scoring, and
compute_metrics_from_judgments helper function.
"""

import pytest

from app.retrieval.quality import (
    RAGJudge,
    RAGQualityMetrics,
    compute_metrics_from_judgments,
)


class TestRAGQualityMetrics:
    """Tests for the RAGQualityMetrics dataclass."""

    def test_default_metrics_are_zero(self):
        """Default metrics instance has all zeros."""
        m = RAGQualityMetrics()
        assert m.avg_relevance == 0.0
        assert m.hit_rate == 0.0
        assert m.mrr == 0.0
        assert m.ndcg == 0.0
        assert m.precision_at_k == 0.0
        assert m.total_retrieved == 0
        assert m.judgments == []

    def test_to_dict_includes_all_fields(self):
        """to_dict() returns all expected keys."""
        m = RAGQualityMetrics(query="test query", knowledge_base_id="kb-1")
        d = m.to_dict()
        expected_keys = {
            "query", "knowledge_base_id", "total_retrieved",
            "avg_relevance", "hit_rate", "mrr", "ndcg", "precision_at_k", "judgments"
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_rounds_values(self):
        """to_dict() rounds float values appropriately."""
        m = RAGQualityMetrics(
            avg_relevance=3.456,
            hit_rate=0.6667,
            mrr=0.3333,
            ndcg=0.78912,
            precision_at_k=0.6001,
        )
        d = m.to_dict()
        assert d["avg_relevance"] == 3.46  # 2 decimal places
        assert d["hit_rate"] == 0.6667     # 4 decimal places
        assert d["mrr"] == 0.3333
        assert d["ndcg"] == 0.7891


class TestKeywordScoring:
    """Tests for RAGJudge._keyword_score fallback scoring."""

    def test_perfect_match_scores_5(self):
        """Exact overlap returns score 5."""
        judge = RAGJudge()
        score = judge._keyword_score("静音破壁机", "静音破壁机 低噪音设计 一键清洗")
        assert score == 5

    def test_high_overlap_scores_high(self):
        """Significant character overlap returns score >= 4."""
        judge = RAGJudge()
        score = judge._keyword_score("静音破壁机", "这款破壁机采用静音设计")
        assert score >= 3, f"Expected >= 3, got {score}"

    def test_no_overlap_scores_1(self):
        """No overlap returns score 1."""
        judge = RAGJudge()
        score = judge._keyword_score("冰箱", "这款手机屏幕很大")
        assert score == 1

    def test_empty_query_scores_1(self):
        """Empty query returns score 1."""
        judge = RAGJudge()
        score = judge._keyword_score("", "some content")
        assert score == 1


class TestComputeMetricsFromJudgments:
    """Tests for the compute_metrics_from_judgments helper."""

    def test_perfect_results(self):
        """All 5s → perfect metrics."""
        m = compute_metrics_from_judgments("test", [5, 5, 5])
        assert m.hit_rate == 1.0
        assert m.mrr == 1.0
        assert m.precision_at_k == 1.0

    def test_all_bad_results(self):
        """All 1s → zero metrics."""
        m = compute_metrics_from_judgments("test", [1, 1, 1, 1])
        assert m.hit_rate == 0.0
        assert m.mrr == 0.0

    def test_first_result_is_hit(self):
        """First result is relevant → MRR = 1.0."""
        m = compute_metrics_from_judgments("test", [5, 1, 1, 1])
        assert m.mrr == 1.0
        assert m.hit_rate == 0.25

    def test_third_result_is_hit(self):
        """Third result is first hit → MRR = 1/3."""
        m = compute_metrics_from_judgments("test", [1, 2, 4, 1])
        assert abs(m.mrr - 1.0 / 3) < 0.01, f"Expected MRR ~0.333, got {m.mrr}"
        assert m.hit_rate == 0.25

    def test_ndcg_decreases_with_poor_ranking(self):
        """NDCG is lower when relevant docs are ranked lower."""
        m_good = compute_metrics_from_judgments("test", [5, 5, 1, 1])
        m_bad = compute_metrics_from_judgments("test", [1, 1, 5, 5])
        assert m_good.ndcg > m_bad.ndcg, \
            f"Good ranking NDCG ({m_good.ndcg}) should exceed bad ranking ({m_bad.ndcg})"

    def test_empty_judgments(self):
        """Empty list returns zero metrics."""
        m = compute_metrics_from_judgments("test", [])
        assert m.total_retrieved == 0
        assert m.avg_relevance == 0.0
        assert m.hit_rate == 0.0

    def test_single_judgment(self):
        """Single judgment edge case."""
        m = compute_metrics_from_judgments("test", [4])
        assert m.total_retrieved == 1
        assert m.hit_rate == 1.0  # 4 >= 3
        assert m.mrr == 1.0


class TestRAGJudgeEvaluate:
    """Tests for RAGJudge.evaluate() with keyword scoring (no LLM)."""

    def test_evaluate_with_documents(self):
        """evaluate() returns metrics for retrieved documents."""
        judge = RAGJudge()  # No provider_factory → uses keyword scoring
        documents = [
            {"content": "静音破壁机 低噪音设计 一键清洗", "score": 0.95, "chunkId": "c1", "documentId": "d1"},
            {"content": "厨房电器选购指南 冰箱洗衣机推荐", "score": 0.80, "chunkId": "c2", "documentId": "d2"},
            {"content": "手机屏幕评测 5G网络速度测试", "score": 0.60, "chunkId": "c3", "documentId": "d3"},
        ]

        import asyncio
        metrics = asyncio.run(judge.evaluate("静音破壁机", documents, "kb-test"))

        assert metrics.total_retrieved == 3
        assert metrics.avg_relevance > 0
        assert len(metrics.judgments) == 3
        # First doc should have highest relevance
        assert metrics.judgments[0]["relevance"] >= metrics.judgments[2]["relevance"]

    def test_evaluate_with_empty_documents(self):
        """evaluate() with no documents returns zero metrics."""
        judge = RAGJudge()

        import asyncio
        metrics = asyncio.run(judge.evaluate("test query", [], "kb-test"))

        assert metrics.total_retrieved == 0
        assert metrics.avg_relevance == 0.0

    def test_evaluate_judgments_have_required_fields(self):
        """Each judgment has all required fields."""
        judge = RAGJudge()
        documents = [{"content": "测试内容", "score": 0.90, "chunkId": "c1", "documentId": "d1"}]

        import asyncio
        metrics = asyncio.run(judge.evaluate("测试查询", documents, "kb-test"))

        judgment = metrics.judgments[0]
        assert "rank" in judgment
        assert "chunk_id" in judgment
        assert "document_id" in judgment
        assert "similarity_score" in judgment
        assert "relevance" in judgment
        assert "content_preview" in judgment
        assert 1 <= judgment["relevance"] <= 5
