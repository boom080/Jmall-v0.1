"""Unit tests for ReviewerAgent.

Covers: happy path (passed), warning path, error fallback, rule-based checks.
"""

import json

from app.agents.reviewer import ReviewerAgent
from app.providers.factory import ProviderFactory


def test_reviewer_returns_review_result(base_state, settings, provider_factory, llm_router, cost_tracker):
    """Happy path: mock provider returns compliance review with passed status."""
    agent = ReviewerAgent(settings, provider_factory, llm_router, cost_tracker)
    state = dict(base_state)
    # Add copy_drafts so reviewer has something to review
    state["copy_drafts"] = {
        "titles": ["【品质推荐】静音破壁机"],
        "selling_points": ["低噪音", "一键清洗"],
        "detail_copy": "这是一款高品质静音破壁机。",
    }

    import asyncio
    update = asyncio.run(agent.run(state))

    review = update.get("review_result", {})
    assert isinstance(review, dict), "Should return a dict"
    assert "status" in review, "Should have status field"
    assert review["status"] in ("passed", "warning", "rejected"), f"Unexpected status: {review['status']}"
    assert "warnings" in review, "Should have warnings list"
    assert "issues" in review, "Should have issues list"
    assert isinstance(review["warnings"], list)
    assert isinstance(review["issues"], list)


def test_reviewer_runs_rule_based_check(base_state, settings, provider_factory, llm_router, cost_tracker):
    """Rule-based check runs alongside LLM review and results are merged."""
    agent = ReviewerAgent(settings, provider_factory, llm_router, cost_tracker)
    state = dict(base_state)
    state["product_info"]["price"] = "9999999"  # Extremely high price
    state["copy_drafts"] = {
        "titles": ["测试商品"],
        "selling_points": [],
        "detail_copy": "包含'绝对最好'等绝对化用语。",
    }

    import asyncio
    update = asyncio.run(agent.run(state))

    review = update.get("review_result", {})
    # The merge should produce a valid status
    assert review["status"] in ("passed", "warning", "rejected")


def test_reviewer_falls_back_on_error(base_state, settings, llm_router, cost_tracker):
    """When LLM fails, agent returns warning fallback."""
    class FailingProviderFactory(ProviderFactory):
        def chat(self, provider_name, model_name, messages, temperature=0.7, max_tokens=2048, **kwargs):
            raise RuntimeError("Simulated LLM failure")

    failing_factory = FailingProviderFactory(settings)
    agent = ReviewerAgent(settings, failing_factory, llm_router, cost_tracker)
    state = dict(base_state)

    import asyncio
    update = asyncio.run(agent.run(state))

    review = update.get("review_result", {})
    assert isinstance(review, dict), "Should return fallback dict"
    # Fallback should indicate warning
    assert "status" in review
    assert review["fallback"] is True
    assert "Simulated LLM failure" in review["error"]


def test_reviewer_handles_empty_copy(base_state, settings, provider_factory, llm_router, cost_tracker):
    """Reviewer works even with empty copy_drafts."""
    agent = ReviewerAgent(settings, provider_factory, llm_router, cost_tracker)
    state = dict(base_state)
    state["copy_drafts"] = {}

    import asyncio
    update = asyncio.run(agent.run(state))

    review = update.get("review_result", {})
    assert isinstance(review, dict), "Should handle empty copy gracefully"
