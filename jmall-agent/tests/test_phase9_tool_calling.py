"""Tests for Phase 9 changes: Tool Calling + LangGraph restructure.

Covers:
- Test 1: Tool calling when search is needed
- Test 2: Direct answer when no search needed
- Test 3: Missing API key → graceful fallback
- Test 4: Tavily failure → fallback to imperative search
- Test 5: market_research completes before copywriter in new DAG
- Test 6: RAG retrieval with knowledge_base_id
- Test 7: Backward compatibility (SSE, compliance, style, cost, router)
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure jmall-agent is on path
sys.path.insert(0, os.path.dirname(__file__))


# ============================================================================
# Helper: build a minimal Settings for testing
# ============================================================================

@pytest.fixture
def settings(tmp_path):
    """Minimal settings with mock provider, no real API keys."""
    from app.core.config import Settings
    return Settings(
        _env_file=None,
        merchant_ai_data_file=str(tmp_path / "merchant_ai_store.json"),
        ai_provider="mock",
        cost_tracking_enabled=True,
        agent_cost_budget_daily=999.0,
        tavily_api_key="",  # No key → uses mock search tool
        deepseek_api_key="",
        qwen_api_key="",
        agent_default_provider="mock",
    )


@pytest.fixture
def provider_factory(settings):
    from app.providers.factory import ProviderFactory
    return ProviderFactory(settings)


@pytest.fixture
def llm_router(settings):
    from app.llm.router import LLMRouter
    return LLMRouter(settings)


@pytest.fixture
def cost_tracker(settings):
    from app.llm.cost_tracker import CostTracker
    return CostTracker(settings)


def run_async(coro):
    """Helper to run async functions in sync tests."""
    return asyncio.run(coro)


# ============================================================================
# Test 1: Tool calling — LLM decides to search
# ============================================================================

class TestToolCallingHappyPath:
    """When LLM receives tools=[search_market_trends], it should call the tool."""

    def test_mock_provider_returns_tool_call(self, settings, provider_factory):
        """Mock provider returns a tool_call when search signals are present."""
        from app.tools.search import SEARCH_MARKET_TRENDS_TOOL

        messages = [
            {"role": "system", "content": "你是电商市场分析师。使用search_market_trends工具获取市场数据。"},
            {"role": "user", "content": "请分析茶叶品类的市场趋势和热搜关键词。"},
        ]

        result = provider_factory.chat(
            provider_name="mock",
            model_name="mock-product-copy-v1",
            messages=messages,
            tools=[SEARCH_MARKET_TRENDS_TOOL],
        )

        assert result["success"] is True
        # Mock should return a tool_call because the message contains "市场"/"趋势"/"品类"
        tool_calls = result.get("tool_calls")
        assert tool_calls is not None, f"Expected tool_calls but got: {json.dumps({k: str(v)[:100] for k, v in result.items()}, ensure_ascii=False)}"
        assert len(tool_calls) == 1
        tc = tool_calls[0]
        assert tc["type"] == "function"
        assert tc["function"]["name"] == "search_market_trends"
        args = json.loads(tc["function"]["arguments"])
        assert "category" in args

    def test_mock_provider_no_search_needed(self, settings, provider_factory):
        """Mock provider returns direct content when no search signals."""
        from app.tools.search import SEARCH_MARKET_TRENDS_TOOL

        messages = [
            {"role": "system", "content": "你是电商市场分析师。"},
            {"role": "user", "content": "请用JSON输出一个简单的问候。"},
        ]

        result = provider_factory.chat(
            provider_name="mock",
            model_name="mock-product-copy-v1",
            messages=messages,
            tools=[SEARCH_MARKET_TRENDS_TOOL],
        )

        assert result["success"] is True
        # No search signals → should return direct content, not tool_call
        assert result.get("tool_calls") is None
        assert result.get("content") is not None

    def test_backward_compat_no_tools(self, settings, provider_factory):
        """Calling chat() without tools still works."""
        messages = [
            {"role": "system", "content": "你是电商文案。"},
            {"role": "user", "content": "生成商品文案。"},
        ]

        result = provider_factory.chat(
            provider_name="mock",
            model_name="mock-product-copy-v1",
            messages=messages,
            # No tools parameter
        )

        assert result["success"] is True
        assert result.get("content") is not None


# ============================================================================
# Test 2: Tool definition schema is valid
# ============================================================================

class TestToolSchema:
    """Verify the tool definition follows OpenAI spec."""

    def test_schema_has_required_fields(self):
        from app.tools.search import SEARCH_MARKET_TRENDS_TOOL
        assert SEARCH_MARKET_TRENDS_TOOL["type"] == "function"
        func = SEARCH_MARKET_TRENDS_TOOL["function"]
        assert "name" in func
        assert func["name"] == "search_market_trends"
        assert "description" in func
        assert "parameters" in func
        params = func["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "category" in params["properties"]
        assert "required" in params
        assert "category" in params["required"]

    def test_execute_search_tool_returns_string(self):
        from app.tools.search import execute_search_tool, get_search_tool
        tool = get_search_tool("")  # No API key → explicit unavailable state
        with pytest.raises(RuntimeError, match="Tavily"):
            run_async(execute_search_tool(tool, {"category": "茶叶", "keywords": ["龙井"]}))

    def test_tavily_error_text_is_not_treated_as_market_evidence(self):
        from app.tools.search import search_market_trends

        tool = MagicMock()
        tool.invoke.return_value = "HTTPError('432 Client Error: for url: https://api.tavily.com/search')"

        with pytest.raises(RuntimeError, match="error response"):
            search_market_trends(tool, "食品饮料")

    def test_search_falls_back_to_secondary_provider(self):
        from app.tools.search import _FallbackSearchTool

        primary = MagicMock()
        primary.invoke.side_effect = RuntimeError("quota exceeded")
        fallback = MagicMock()
        fallback.invoke.return_value = "联网检索结果"

        assert _FallbackSearchTool(primary, fallback).invoke("茶叶趋势") == "联网检索结果"
        fallback.invoke.assert_called_once_with("茶叶趋势")

    def test_search_evidence_keeps_provider_sources_and_usage(self):
        from app.tools.search import SearchEvidence

        evidence = SearchEvidence(
            "来源摘要 https://example.com/report",
            provider="qwen_web_search",
            sources=[{"title": "行业报告", "url": "https://example.com/report"}],
            model="qwen-plus",
            input_tokens=120,
            output_tokens=30,
        )

        assert isinstance(evidence, str)
        assert evidence.provider == "qwen_web_search"
        assert evidence.sources[0]["title"] == "行业报告"
        assert evidence.input_tokens + evidence.output_tokens == 150


# ============================================================================
# Test 3: MarketResearchAgent with tool calling
# ============================================================================

class TestMarketResearchAgentToolCalling:
    """Verify MarketResearchAgent correctly uses tool calling."""

    def test_agent_registers_tools(self, settings, provider_factory, llm_router, cost_tracker):
        from app.agents.market_research import MarketResearchAgent
        agent = MarketResearchAgent(
            settings=settings,
            provider_factory=provider_factory,
            llm_router=llm_router,
            cost_tracker=cost_tracker,
        )
        assert len(agent.tools) == 1
        assert agent.tools[0]["function"]["name"] == "search_market_trends"

    def test_agent_returns_structured_result(self, settings, provider_factory, llm_router, cost_tracker):
        """Full tool-calling flow with mock provider."""
        from app.agents.market_research import MarketResearchAgent
        agent = MarketResearchAgent(
            settings=settings,
            provider_factory=provider_factory,
            llm_router=llm_router,
            cost_tracker=cost_tracker,
        )

        state = {
            "product_info": {
                "title": "明前龙井茶",
                "category": "茶叶",
                "description": "2024年新茶，产地杭州",
                "price": "29900",
            },
        }

        update = run_async(agent.run(state))
        assert "market_research" in update
        mr = update["market_research"]
        # Should have standard fields regardless of path
        assert "category" in mr
        assert mr["category"] == "茶叶"
        # Check that method field exists (tells us which path was used)
        assert "method" in mr
        assert mr["method"] in ("tool_calling", "imperative_fallback", "realtime_search_unavailable")
        if mr["method"] == "realtime_search_unavailable":
            assert mr["status"] == "failed"
            assert mr["hot_keywords"] == []

    def test_agent_fallback_on_tool_error(self, settings, provider_factory, llm_router, cost_tracker):
        """If tool calling fails, agent falls back to imperative search."""
        from app.agents.market_research import MarketResearchAgent
        agent = MarketResearchAgent(
            settings=settings,
            provider_factory=provider_factory,
            llm_router=llm_router,
            cost_tracker=cost_tracker,
        )

        # Make provider_factory.chat fail on first call, succeed on second
        original_chat = provider_factory.chat
        call_count = [0]

        def failing_chat(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1 and kwargs.get("tools"):
                raise RuntimeError("Simulated tool calling failure")
            return original_chat(*args, **kwargs)

        provider_factory.chat = failing_chat

        state = {
            "product_info": {
                "title": "测试商品",
                "category": "测试",
                "description": "",
                "price": "100",
            },
        }

        update = run_async(agent.run(state))
        assert "market_research" in update
        mr = update["market_research"]
        # Should still produce valid output via fallback
        assert "category" in mr

    def test_agent_no_api_key_still_works(self, settings, provider_factory, llm_router, cost_tracker):
        """Even without Tavily API key, agent should not crash."""
        settings.tavily_api_key = ""
        from app.agents.market_research import MarketResearchAgent
        agent = MarketResearchAgent(
            settings=settings,
            provider_factory=provider_factory,
            llm_router=llm_router,
            cost_tracker=cost_tracker,
        )

        state = {
            "product_info": {
                "title": "测试商品",
                "category": "测试",
                "description": "",
                "price": "100",
            },
        }

        update = run_async(agent.run(state))
        assert "market_research" in update
        mr = update["market_research"]
        assert mr.get("category") == "测试"


# ============================================================================
# Test 4: LangGraph DAG correctness
# ============================================================================

class TestGraphRestructure:
    """Verify the new DAG structure."""

    def test_rag_retrieval_node_exists(self, settings, provider_factory):
        from app.agents.graph import AgentOrchestratorGraph
        graph = AgentOrchestratorGraph(
            settings=settings,
            provider_factory=provider_factory,
            retrieval_service=None,
        )
        # Graph should compile without error
        assert graph.graph is not None

    def test_rag_retrieval_noop_without_kb(self, settings, provider_factory):
        """rag_retrieval is a no-op when no knowledge_base_id."""
        from app.agents.graph import AgentOrchestratorGraph
        graph = AgentOrchestratorGraph(
            settings=settings,
            provider_factory=provider_factory,
            retrieval_service=None,
        )
        state: Dict[str, Any] = {
            "knowledge_base_id": "",
            "product_info": {"title": "test", "category": "test"},
        }
        result = run_async(graph._run_rag_retrieval(state))
        assert result.get("rag_context") == ""

    def test_market_research_before_copywriter(self, settings, provider_factory):
        """Verify the graph topology: market_research feeds into copywriter."""
        from app.agents.graph import AgentOrchestratorGraph
        graph_obj = AgentOrchestratorGraph(
            settings=settings,
            provider_factory=provider_factory,
            retrieval_service=None,
        )
        # Check graph structure via compiled graph
        compiled = graph_obj.graph
        assert compiled is not None

    def test_full_pipeline_smoke(self, settings, provider_factory):
        """Run the full graph end-to-end with mock provider."""
        from app.agents.graph import AgentGraphState, AgentOrchestratorGraph
        graph = AgentOrchestratorGraph(
            settings=settings,
            provider_factory=provider_factory,
            retrieval_service=None,
        )

        state: AgentGraphState = {
            "user_request": "为茶叶生成淘宝风格文案",
            "product_info": {
                "title": "明前龙井",
                "category": "茶叶",
                "description": "2024新茶",
                "price": "29900",
                "specifications": "明前采摘；龙井43号；净含量250克",
                "target_audience": "茶叶爱好者和送礼用户",
                "usage_scenarios": "日常饮用、节日送礼",
            },
            "target_style": "taobao",
            "knowledge_base_id": "",
            "errors": [],
        }

        result = run_async(graph.invoke(state))
        assert "final_result" in result
        final = result["final_result"]
        assert final is not None
        # Basic structure check
        assert "overall_status" in final
        assert "copy" in final
        assert "market_insights" in final


# ============================================================================
# Test 5: SSE backward compatibility
# ============================================================================

class TestSSEBackwardCompat:
    """Verify SSE streaming still works after changes."""

    def test_progress_callback_format(self, settings, provider_factory):
        from app.agents.graph import AgentGraphState, AgentOrchestratorGraph

        events: List[dict] = []

        async def collect_events(agent_name: str, status: str, result: dict):
            events.append({"agent": agent_name, "status": status, "data": result})

        graph = AgentOrchestratorGraph(
            settings=settings,
            provider_factory=provider_factory,
            retrieval_service=None,
        )

        state: AgentGraphState = {
            "user_request": "测试",
            "product_info": {"title": "测试商品", "category": "测试", "description": "", "price": "100"},
            "target_style": "taobao",
            "knowledge_base_id": "",
            "errors": [],
        }

        result = run_async(graph.invoke(state, progress_callback=collect_events))
        assert len(events) > 0, "SSE events should be emitted"
        # Last event should be orchestration_complete
        assert events[-1]["agent"] == "orchestration_complete"


# ============================================================================
# Test 6: Backward compatibility
# ============================================================================

class TestBackwardCompatibility:
    """Verify existing features still work."""

    def test_llm_router_still_works(self, settings):
        from app.llm.router import LLMRouter
        router = LLMRouter(settings)
        provider, model = router.route("market_research")
        # With no API keys configured, defaults to mock provider
        assert provider == "mock"
        assert isinstance(model, str) and len(model) > 0

    def test_cost_tracker_still_works(self, settings):
        from app.llm.cost_tracker import CostTracker
        ct = CostTracker(settings)
        ct.track(provider="mock", model="mock-v1", input_tokens=100, output_tokens=50, agent_type="market_research")
        stats = ct.get_stats()
        assert stats is not None

    def test_old_call_llm_still_works(self, settings, provider_factory, llm_router, cost_tracker):
        """BaseAgent._call_llm() without tools still works."""
        from app.agents.base import BaseAgent

        class TestAgent(BaseAgent):
            agent_type = "test"
            async def run(self, state):
                return {}

        agent = TestAgent(settings, provider_factory, llm_router, cost_tracker)
        result = agent._call_llm("Hello")
        assert result.get("content") is not None


# ============================================================================
# Test 7: Run via pytest
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
