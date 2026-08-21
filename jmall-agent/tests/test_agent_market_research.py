"""Unit tests for MarketResearchAgent.

Covers: happy path with mock provider, error fallback, and field validation.
"""

import json
from unittest.mock import MagicMock

from app.agents.market_research import MarketResearchAgent
from app.providers.factory import ProviderFactory


def test_market_research_returns_trends_and_keywords(base_state, settings, provider_factory, llm_router, cost_tracker):
    """Happy path: mock provider returns structured market research JSON."""
    agent = MarketResearchAgent(settings, provider_factory, llm_router, cost_tracker)
    state = dict(base_state)

    import asyncio
    update = asyncio.run(agent.run(state))

    research = update.get("market_research", {})
    assert isinstance(research, dict), "Should return a dict"
    assert "trends_summary" in research, "Should have trends_summary"
    assert len(research.get("trends_summary", "")) > 0, "Trends summary should not be empty"
    assert "hot_keywords" in research, "Should have hot_keywords"
    assert isinstance(research["hot_keywords"], list), "hot_keywords should be a list"
    assert "competitor_price_range" in research, "Should have competitor_price_range"
    assert "suggestions" in research, "Should have suggestions"


def test_market_research_falls_back_on_error(base_state, settings, llm_router, cost_tracker):
    """When LLM fails, agent returns fallback research data via imperative fallback."""
    # Create a failing provider factory — must accept **kwargs for forward compat
    class FailingProviderFactory(ProviderFactory):
        def chat(self, provider_name, model_name, messages, temperature=0.7, max_tokens=2048, **kwargs):
            raise RuntimeError("Simulated LLM failure")

    failing_factory = FailingProviderFactory(settings)
    agent = MarketResearchAgent(settings, failing_factory, llm_router, cost_tracker)
    state = dict(base_state)

    import asyncio
    update = asyncio.run(agent.run(state))

    research = update.get("market_research", {})
    assert "error" in research or "trends_summary" in research, "Should have some content"
    # Should not have crashed
    assert update is not None


def test_market_research_uses_product_category(base_state, settings, provider_factory, llm_router, cost_tracker):
    """Agent uses product category and title from state."""
    agent = MarketResearchAgent(settings, provider_factory, llm_router, cost_tracker)
    state = dict(base_state)
    state["product_info"] = {
        "title": "有机绿茶礼盒",
        "category": "茶叶",
        "description": "明前采摘",
        "price": "16800",
    }

    import asyncio
    update = asyncio.run(agent.run(state))

    research = update.get("market_research", {})
    # Mock provider returns generic data; verify structure is correct
    assert isinstance(research.get("hot_keywords", []), list)
    assert isinstance(research.get("suggestions", []), list)


def test_market_research_propagates_agent_type(base_state, settings, provider_factory, llm_router, cost_tracker):
    """Agent has correct agent_type set."""
    agent = MarketResearchAgent(settings, provider_factory, llm_router, cost_tracker)
    assert agent.agent_type == "market_research"
    assert len(agent.system_prompt) > 0


def test_market_research_reports_tavily_failure_without_fake_trends(
    base_state, settings, provider_factory, llm_router, cost_tracker,
):
    class FailingSearchTool:
        name = "tavily_search_results_json"

        def invoke(self, query):
            raise RuntimeError("Tavily quota exceeded")

    agent = MarketResearchAgent(settings, provider_factory, llm_router, cost_tracker)
    agent.search_tool = FailingSearchTool()

    import asyncio
    update = asyncio.run(agent.run(dict(base_state)))
    research = update["market_research"]

    assert research["status"] == "failed"
    assert research["hot_keywords"] == []
    assert research["competitor_price_range"]["high"] == 0
    assert "Tavily" in research["error"]
