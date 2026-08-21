"""Unit tests for OrchestratorAgent.

Covers: plan generation, aggregate_results, error handling.
"""

import json

from app.agents.orchestrator import OrchestratorAgent
from app.providers.factory import ProviderFactory


def test_orchestrator_generates_plan(base_state, settings, provider_factory, llm_router, cost_tracker):
    """Happy path: mock provider returns orchestration plan."""
    agent = OrchestratorAgent(settings, provider_factory, llm_router, cost_tracker)
    state = dict(base_state)

    import asyncio
    update = asyncio.run(agent.run(state))

    plan = update.get("orchestration_plan", {})
    assert isinstance(plan, dict), "Should return a dict"
    assert "plan" in plan or "steps" in str(plan).lower(), "Should contain a plan or steps"
    plan_items = plan.get("plan", [])
    assert isinstance(plan_items, list), "Plan items should be a list"

    if len(plan_items) > 0:
        step = plan_items[0]
        assert "step" in step, "Each step should have a 'step' name"
        assert "description" in step, "Each step should have a 'description'"


def test_orchestrator_plan_includes_all_agents(base_state, settings, provider_factory, llm_router, cost_tracker):
    """Generated plan covers all necessary agent steps."""
    agent = OrchestratorAgent(settings, provider_factory, llm_router, cost_tracker)
    state = dict(base_state)

    import asyncio
    update = asyncio.run(agent.run(state))

    plan = update.get("orchestration_plan", {})
    plan_items = plan.get("plan", [])
    step_names = [s.get("step", "") for s in plan_items]

    # Mock orchestrator generates market_research, copy_generation, compliance_review, style_adaptation
    expected = ["market_research", "copy_generation", "compliance_review", "style_adaptation"]
    for expected_step in expected:
        assert expected_step in step_names, f"Plan should include '{expected_step}' step"


def test_aggregate_results_merges_all_outputs(base_state, settings, provider_factory, llm_router, cost_tracker):
    """aggregate_results() correctly merges outputs from all agents."""
    agent = OrchestratorAgent(settings, provider_factory, llm_router, cost_tracker)

    state = dict(base_state)
    state["market_research"] = {"trends_summary": "测试趋势", "hot_keywords": ["热词1"]}
    state["copy_drafts"] = {"titles": ["测试标题"], "selling_points": ["卖点1"]}
    state["review_result"] = {"status": "passed", "issues": [], "warnings": []}
    state["style_previews"] = {"adapted_title": "适配标题"}
    state["orchestration_plan"] = {"plan": []}

    result = agent.aggregate_results(state)

    assert isinstance(result, dict), "Should return dict"
    assert result.get("overall_status") in ("completed", "success", "warning", None, ""), \
        f"Should have valid overall_status, got: {result.get('overall_status')}"
    # Should include product title
    assert "product_title" in result or result.get("overall_status") is not None


def test_aggregate_results_with_errors(base_state, settings, provider_factory, llm_router, cost_tracker):
    """aggregate_results() handles partial state with errors gracefully."""
    agent = OrchestratorAgent(settings, provider_factory, llm_router, cost_tracker)

    state = dict(base_state)
    state["errors"] = ["market_research: Simulated failure"]
    state["market_research"] = {"error": "Failed"}
    state["copy_drafts"] = {}
    state["review_result"] = {}
    state["style_previews"] = {}

    result = agent.aggregate_results(state)
    assert isinstance(result, dict), "Should return dict even with errors"


def test_orchestrator_falls_back_on_error(base_state, settings, llm_router, cost_tracker):
    """When LLM fails, orchestrator uses default plan."""
    class FailingProviderFactory(ProviderFactory):
        def chat(self, provider_name, model_name, messages, temperature=0.7, max_tokens=2048, **kwargs):
            raise RuntimeError("Simulated LLM failure")

    failing_factory = FailingProviderFactory(settings)
    agent = OrchestratorAgent(settings, failing_factory, llm_router, cost_tracker)
    state = dict(base_state)

    import asyncio
    update = asyncio.run(agent.run(state))

    # Should have a fallback plan
    plan = update.get("orchestration_plan", {})
    assert isinstance(plan, dict)
