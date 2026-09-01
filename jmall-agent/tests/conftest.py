"""Shared pytest fixtures for agent tests.

Uses the existing hand-rolled mock patterns established in the codebase:
- Real Settings with _env_file=None (no .env loading)
- Real ProviderFactory (mock mode by default — returns canned responses)
- Real CostTracker (enabled tracking)
- File-based repositories in tmp_path

No pytest-asyncio needed — agent.run() is async but _call_llm() is sync under
the hood, so asyncio.run() works in plain test functions.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from app.agents.graph import AgentGraphState, AgentOrchestratorGraph
from app.core.config import Settings
from app.llm.cost_tracker import CostTracker
from app.llm.router import LLMRouter
from app.providers.factory import ProviderFactory
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.retrieval.service import RetrievalService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Isolated Settings with no env files and temp storage.

    All providers default to 'mock' mode since no API keys are configured.
    Explicitly sets embedding to mock so no real API calls leak from Docker env.
    """
    return Settings(
        _env_file=None,
        merchant_ai_data_file=str(tmp_path / "merchant_ai_store.json"),
        cost_tracking_enabled=True,
        agent_cost_budget_daily=999.0,  # High budget so tests never hit limit
        ai_provider="mock",
        ai_fallback_provider="mock",
        agent_default_provider="mock",
        agent_strong_provider="mock",
        agent_medium_provider="mock",
        agent_cheap_provider="mock",
        tavily_api_key="",
        qwen_api_key="",
        image_search_provider="disabled",
        serpapi_api_key="",
        rag_embedding_provider="mock",
        rag_embedding_api_key="",
    )


@pytest.fixture
def provider_factory(settings: Settings) -> ProviderFactory:
    """ProviderFactory in mock mode — returns canned JSON for all agent types."""
    return ProviderFactory(settings)


@pytest.fixture
def llm_router(settings: Settings) -> LLMRouter:
    """LLMRouter that routes everything to 'mock' provider."""
    return LLMRouter(settings)


@pytest.fixture
def cost_tracker(settings: Settings) -> CostTracker:
    """CostTracker with tracking enabled and high budget."""
    return CostTracker(settings)


@pytest.fixture
def repository(settings: Settings) -> KnowledgeBaseRepository:
    """File-based KnowledgeBaseRepository with temp storage."""
    return KnowledgeBaseRepository(settings)


@pytest.fixture
def embedding_service(settings: Settings) -> EmbeddingService:
    """EmbeddingService in mock mode (returns zero vectors)."""
    return EmbeddingService(settings)


@pytest.fixture
def chunking_service(settings: Settings) -> ChunkingService:
    """ChunkingService with default settings."""
    return ChunkingService(settings)


@pytest.fixture
def retrieval_service(
    settings: Settings,
    repository: KnowledgeBaseRepository,
    embedding_service: EmbeddingService,
) -> RetrievalService:
    """RetrievalService backed by temp file storage."""
    return RetrievalService(settings, repository, embedding_service)


@pytest.fixture
def base_state() -> AgentGraphState:
    """Standard AgentGraphState for a typical product listing task."""
    return {
        "user_request": "为我的新产品生成电商文案",
        "product_info": {
            "title": "静音破壁机",
            "category": "厨房电器",
            "description": "低噪音设计，一键清洗，多功能料理",
            "price": "29900",  # cents: ¥299.00
            "target_audience": "家庭用户和上班族",
            "usage_scenarios": "家庭厨房、日常料理",
        },
        "target_style": "taobao",
        "knowledge_base_id": "",
        "orchestration_plan": None,
        "market_research": None,
        "copy_drafts": None,
        "review_result": None,
        "style_previews": None,
        "final_result": None,
        "errors": [],
    }


@pytest.fixture
def graph(
    settings: Settings,
    provider_factory: ProviderFactory,
    retrieval_service: RetrievalService,
) -> AgentOrchestratorGraph:
    """AgentOrchestratorGraph with mock providers."""
    return AgentOrchestratorGraph(
        settings=settings,
        provider_factory=provider_factory,
        retrieval_service=retrieval_service,
    )


def run_async(coro):
    """Helper to run an async agent.run() in a plain test function.

    All agents are async def run() but _call_llm() is sync, so
    asyncio.run() works without pytest-asyncio.
    """
    return asyncio.run(coro)
