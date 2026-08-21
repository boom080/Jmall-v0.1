"""Unit tests for the simple heuristic RAG quality assessment.

Tests the ``assess_rag_quality()`` function that evaluates retrieval
quality purely from chunk scores — no LLM calls involved.
"""

import pytest

from app.retrieval.rag_retriever import assess_rag_quality


class TestEmptyResults:
    def test_empty_list_returns_empty_quality(self):
        result = assess_rag_quality([])
        assert result == {
            "quality": "empty",
            "top1_score": 0.0,
            "avg_score": 0.0,
            "result_count": 0,
        }

    def test_none_equivalent_handled_as_empty_in_practice(self):
        """Callers should pass a list; the function expects chunks list."""
        # This test documents the expected input contract.
        # assess_rag_quality only handles lists; None would raise.
        result = assess_rag_quality([])
        assert result["quality"] == "empty"


class TestQualityLevels:
    def test_high_quality_when_top1_above_08(self):
        chunks = [
            {"score": 0.92, "content": "relevant content"},
            {"score": 0.75, "content": "less relevant"},
            {"score": 0.60, "content": "even less"},
        ]
        result = assess_rag_quality(chunks)
        assert result["quality"] == "high"
        assert result["top1_score"] == 0.92
        assert result["result_count"] == 3

    def test_medium_quality_when_top1_between_05_and_08(self):
        chunks = [
            {"score": 0.72, "content": "moderately relevant"},
            {"score": 0.45, "content": "weak"},
        ]
        result = assess_rag_quality(chunks)
        assert result["quality"] == "medium"
        assert result["top1_score"] == 0.72
        assert result["result_count"] == 2

    def test_medium_quality_at_boundary_08_exclusive(self):
        chunks = [{"score": 0.79, "content": "just below high"}]
        result = assess_rag_quality(chunks)
        assert result["quality"] == "medium"

    def test_low_quality_when_top1_below_05(self):
        chunks = [
            {"score": 0.35, "content": "weak match"},
            {"score": 0.20, "content": "even weaker"},
        ]
        result = assess_rag_quality(chunks)
        assert result["quality"] == "low"
        assert result["top1_score"] == 0.35
        assert result["result_count"] == 2

    def test_high_quality_at_exact_boundary_08(self):
        chunks = [{"score": 0.8, "content": "boundary"}]
        result = assess_rag_quality(chunks)
        assert result["quality"] == "high"

    def test_medium_quality_at_exact_boundary_05(self):
        chunks = [{"score": 0.5, "content": "boundary"}]
        result = assess_rag_quality(chunks)
        assert result["quality"] == "medium"


class TestScoreCalculations:
    def test_avg_score_is_mean_of_all_scores(self):
        chunks = [
            {"score": 0.90},
            {"score": 0.70},
            {"score": 0.50},
            {"score": 0.30},
        ]
        result = assess_rag_quality(chunks)
        expected_avg = (0.90 + 0.70 + 0.50 + 0.30) / 4
        assert result["avg_score"] == round(expected_avg, 4)
        assert result["top1_score"] == 0.90
        assert result["result_count"] == 4

    def test_single_chunk(self):
        chunks = [{"score": 0.85}]
        result = assess_rag_quality(chunks)
        assert result["top1_score"] == 0.85
        assert result["avg_score"] == 0.85
        assert result["result_count"] == 1
        assert result["quality"] == "high"

    def test_scores_rounded_to_4_decimal_places(self):
        chunks = [{"score": 0.123456}]
        result = assess_rag_quality(chunks)
        assert result["top1_score"] == 0.1235  # rounded
        assert result["avg_score"] == 0.1235


class TestMissingScoreDefaults:
    def test_missing_score_field_defaults_to_zero(self):
        chunks = [{"content": "no score field"}]
        result = assess_rag_quality(chunks)
        assert result["top1_score"] == 0.0
        assert result["quality"] == "low"

    def test_none_score_treated_as_zero(self):
        chunks = [{"score": None, "content": "none score"}]
        result = assess_rag_quality(chunks)
        assert result["top1_score"] == 0.0


class TestReturnStructure:
    def test_result_has_all_required_keys(self):
        result = assess_rag_quality([{"score": 0.7}])
        assert set(result.keys()) == {"quality", "top1_score", "avg_score", "result_count"}

    def test_quality_is_one_of_valid_levels(self):
        valid = {"empty", "low", "medium", "high"}
        assert assess_rag_quality([])["quality"] in valid
        assert assess_rag_quality([{"score": 0.2}])["quality"] in valid
        assert assess_rag_quality([{"score": 0.6}])["quality"] in valid
        assert assess_rag_quality([{"score": 0.9}])["quality"] in valid


class TestIntegrationInGraph:
    """Verify rag_quality appears in the graph state after retrieval."""

    def test_graph_state_includes_rag_quality_after_retrieval(self):
        """After rag_retrieval node, state contains rag_quality."""
        import asyncio

        from app.agents.graph import AgentGraphState, AgentOrchestratorGraph
        from app.core.config import Settings
        from app.providers.factory import ProviderFactory
        from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
        from app.retrieval.service import RetrievalService
        from app.services.chunking_service import ChunkingService
        from app.services.embedding_service import EmbeddingService
        from app.services.knowledge_base_service import KnowledgeBaseService

        settings = Settings(
            ai_provider="mock",
            rag_embedding_provider="mock",
            rag_embedding_api_key="",
            database_url="",
            redis_url="",
            _env_file=None,
        )
        provider_factory = ProviderFactory(settings)
        repository = KnowledgeBaseRepository(settings)
        embedding_service = EmbeddingService(settings)
        kb_service = KnowledgeBaseService(repository, embedding_service, ChunkingService(settings))
        retrieval_service = RetrievalService(settings, repository, embedding_service)

        # Create a knowledge base with some content
        kb = kb_service.create_knowledge_base("质量测试KB", "")
        kb_service.import_text_document(kb.id, "测试文档", "长续航电池，适合通勤使用。")

        graph = AgentOrchestratorGraph(
            settings=settings,
            provider_factory=provider_factory,
            retrieval_service=retrieval_service,
        )

        state: AgentGraphState = {
            "user_request": "",
            "product_info": {
                "title": "长续航手机",
                "category": "手机数码",
                "description": "",
                "price": "",
            },
            "target_style": "taobao",
            "knowledge_base_id": kb.id,
            "errors": [],
        }

        # Run only the rag_retrieval node directly
        updated = asyncio.run(graph._run_rag_retrieval(dict(state)))

        assert "rag_quality" in updated
        quality = updated["rag_quality"]
        assert quality["quality"] in ("high", "medium", "low", "empty")
        assert "top1_score" in quality
        assert "avg_score" in quality
        assert quality["result_count"] >= 0

    def test_graph_rag_quality_empty_without_knowledge_base(self):
        """Without a knowledge_base_id, rag_quality is empty."""
        import asyncio

        from app.agents.graph import AgentGraphState, AgentOrchestratorGraph
        from app.core.config import Settings
        from app.providers.factory import ProviderFactory

        settings = Settings(
            ai_provider="mock",
            rag_embedding_provider="mock",
            rag_embedding_api_key="",
            database_url="",
            redis_url="",
            _env_file=None,
        )
        provider_factory = ProviderFactory(settings)

        graph = AgentOrchestratorGraph(
            settings=settings,
            provider_factory=provider_factory,
            retrieval_service=None,
        )

        state: AgentGraphState = {
            "user_request": "",
            "product_info": {"title": "测试", "category": "测试", "description": "", "price": ""},
            "target_style": "taobao",
            "knowledge_base_id": "",
            "errors": [],
        }

        updated = asyncio.run(graph._run_rag_retrieval(dict(state)))
        assert updated["rag_quality"] == {
            "quality": "empty",
            "top1_score": 0.0,
            "avg_score": 0.0,
            "result_count": 0,
        }
