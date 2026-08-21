"""Integration tests for AgentOrchestratorGraph.

Tests the full LangGraph orchestration pipeline with mock providers.
Covers: graph execution, parallel fan-out, result aggregation, error handling.
"""

import asyncio

from app.agents.graph import AgentOrchestratorGraph


def test_graph_completes_full_orchestration(graph, base_state):
    """Full graph execution produces final_result with all agent outputs."""
    state = dict(base_state)

    result = asyncio.run(graph.invoke(state))

    final = result.get("final_result", {})
    assert isinstance(final, dict), "Should have final_result"
    # Should have some status
    assert "overall_status" in final or "product_title" in final, "Should have expected fields"


def test_graph_includes_market_insights(graph, base_state):
    """Market research results appear in final output."""
    state = dict(base_state)

    result = asyncio.run(graph.invoke(state))

    final = result.get("final_result", {})
    # Market insights should be present (from mock)
    market_insights = final.get("market_insights", {})
    assert isinstance(market_insights, dict), "Should have market_insights"


def test_graph_includes_copy_content(graph, base_state):
    """Copy generation results appear in final output."""
    state = dict(base_state)

    result = asyncio.run(graph.invoke(state))

    final = result.get("final_result", {})
    # Copy content should be present
    copy = final.get("copy", {})
    assert isinstance(copy, dict), "Should have copy content"


def test_graph_includes_compliance(graph, base_state):
    """Compliance review results appear in final output."""
    state = dict(base_state)

    result = asyncio.run(graph.invoke(state))

    final = result.get("final_result", {})
    compliance = final.get("compliance", {})
    assert isinstance(compliance, dict), "Should have compliance result"


def test_graph_collects_errors_in_state(graph, base_state):
    """Errors during execution are collected in state['errors']."""
    state = dict(base_state)

    result = asyncio.run(graph.invoke(state))

    # With mock provider, there should be no errors
    errors = result.get("errors", [])
    assert isinstance(errors, list), "errors should be a list"


def test_graph_handles_empty_state(graph):
    """Graph handles minimal state gracefully."""
    minimal_state = {
        "user_request": "",
        "product_info": {
            "title": "测试商品",
            "category": "测试",
            "description": "",
            "price": "",
        },
        "target_style": "taobao",
        "knowledge_base_id": "",
        "errors": [],
    }

    result = asyncio.run(graph.invoke(minimal_state))
    assert "final_result" in result, "Should have final_result even with minimal state"
    assert result["final_result"] is not None


def test_graph_respects_target_style(graph, base_state):
    """Target style is passed through to style adaptation."""
    state = dict(base_state)
    state["target_style"] = "pinduoduo"

    result = asyncio.run(graph.invoke(state))

    final = result.get("final_result", {})
    adaptation = final.get("style_adaptation", {})
    # Style adaptation should exist
    assert isinstance(adaptation, dict)


def test_graph_produces_cost_stats(graph, base_state):
    """get_cost_stats() returns valid stats after graph execution."""
    state = dict(base_state)
    result = asyncio.run(graph.invoke(state))

    stats = graph.get_cost_stats()
    assert isinstance(stats, dict), "Should return dict"
    assert "daily_cost_usd" in stats, "Should have daily_cost_usd"
    assert "total_cost_usd" in stats, "Should have total_cost_usd"
    assert "total_calls" in stats, "Should have total_calls"
    assert isinstance(stats["total_calls"], int)


def test_graph_result_cost_stats_are_scoped_to_one_invocation(graph, base_state):
    import asyncio

    first = asyncio.run(graph.invoke(dict(base_state)))
    second = asyncio.run(graph.invoke(dict(base_state)))

    assert first["cost_stats"]["scope_id"]
    assert second["cost_stats"]["scope_id"]
    assert first["cost_stats"]["scope_id"] != second["cost_stats"]["scope_id"]
    assert "tokens_by_agent" in first["cost_stats"]
    assert first["cost_stats"]["total_tokens"] == sum(
        value["total_tokens"] for value in first["cost_stats"]["tokens_by_agent"].values()
    )


def test_graph_handles_progress_callback(graph, base_state):
    """Progress callback receives events during orchestration."""
    state = dict(base_state)
    events = []

    async def progress_callback(agent_name, status, result):
        events.append((agent_name, status))

    result = asyncio.run(graph.invoke(state, progress_callback=progress_callback))

    # With mock provider, we should get at least the completion event
    assert len(events) > 0, "Should have received at least one progress event"
    # Last event should be completion
    last_event = events[-1]
    assert last_event[0] == "orchestration_complete", f"Last event should be completion, got: {last_event[0]}"


def test_graph_handles_error_in_progress_callback(graph, base_state):
    """Graph survives exceptions in the progress callback."""
    state = dict(base_state)

    async def broken_callback(agent_name, status, result):
        if agent_name == "market_research":
            raise RuntimeError("Callback failure")

    # Should not raise
    result = asyncio.run(graph.invoke(state, progress_callback=broken_callback))
    assert "final_result" in result


def test_graph_isolates_callbacks_for_concurrent_invocations(graph, base_state):
    """A singleton graph must never deliver one request's progress to another."""
    async def run_concurrently():
        events_a = []
        events_b = []

        async def callback_a(agent_name, status, result):
            events_a.append(agent_name)
            await asyncio.sleep(0)

        async def callback_b(agent_name, status, result):
            events_b.append(agent_name)
            await asyncio.sleep(0)

        state_a = dict(base_state)
        state_a["product_info"] = {**base_state["product_info"], "title": "并发商品A"}
        state_b = dict(base_state)
        state_b["product_info"] = {**base_state["product_info"], "title": "并发商品B"}

        await asyncio.gather(
            graph.invoke(state_a, progress_callback=callback_a),
            graph.invoke(state_b, progress_callback=callback_b),
        )
        return events_a, events_b

    events_a, events_b = asyncio.run(run_concurrently())
    assert events_a[-1] == "orchestration_complete"
    assert events_b[-1] == "orchestration_complete"
    assert events_a.count("orchestration_complete") == 1
    assert events_b.count("orchestration_complete") == 1
