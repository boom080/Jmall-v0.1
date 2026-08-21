from app.llm.cost_tracker import CostTracker


def test_cost_tracker_scope_and_agent_breakdown(settings):
    tracker = CostTracker(settings)
    scope_id, token = tracker.begin_scope()
    try:
        tracker.track("qwen", "qwen-turbo", 1000, 500, "market_research")
        tracker.track("qwen", "qwen-plus", 2000, 600, "style_adaptation")
    finally:
        tracker.end_scope(token)

    scoped = tracker.get_stats(scope_id)
    assert scoped["total_tokens"] == 4100
    assert scoped["total_cost_usd"] > 0
    assert scoped["tokens_by_agent"]["market_research"]["total_tokens"] == 1500
    assert scoped["tokens_by_agent"]["style_adaptation"]["calls"] == 1


def test_qwen_price_estimate_matches_current_beijing_list_price(settings):
    tracker = CostTracker(settings)
    record = tracker.track("qwen", "qwen-max", 1_000_000, 1_000_000, "copy_generation")
    # ¥2.4 input + ¥9.6 output, converted at the documented estimate ¥7.20/USD.
    assert record.cost_usd == round(12.0 / 7.20, 8)
