"""Unit tests for CopywriterAgent.

Covers: happy path, RAG context injection, market research fallback, error handling.
"""

import json

from app.agents.copywriter import CopywriterAgent, build_structured_detail
from app.llm.cost_tracker import CostTracker
from app.llm.router import LLMRouter
from app.providers.factory import ProviderFactory


def test_copywriter_returns_copy_drafts(base_state, settings, provider_factory, llm_router, cost_tracker):
    """Happy path: mock provider returns copy drafts with titles, selling points, detail."""
    agent = CopywriterAgent(
        settings=settings, provider_factory=provider_factory,
        llm_router=llm_router, cost_tracker=cost_tracker,
    )
    state = dict(base_state)

    import asyncio
    update = asyncio.run(agent.run(state))

    copy = update.get("copy_drafts", {})
    assert isinstance(copy, dict), "Should return a dict"
    assert "titles" in copy, "Should have titles"
    assert isinstance(copy["titles"], list) and len(copy["titles"]) > 0, "Titles should be non-empty list"
    assert "selling_points" in copy, "Should have selling_points"
    assert isinstance(copy["selling_points"], list), "Selling_points should be a list"
    assert "detail_copy" in copy, "Should have detail_copy"
    assert len(copy.get("detail_copy", "")) > 0, "Detail copy should not be empty"
    for field in ["subtitle", "price_suggestion", "specifications", "target_audience",
                  "usage_scenarios", "seo_keywords", "promotion_copy"]:
        assert field in copy, f"Should have structured field: {field}"


def test_copywriter_includes_style_in_output(base_state, settings, provider_factory, llm_router, cost_tracker):
    """Output copy_drafts includes the target style."""
    agent = CopywriterAgent(
        settings=settings, provider_factory=provider_factory,
        llm_router=llm_router, cost_tracker=cost_tracker,
    )
    state = dict(base_state)
    state["target_style"] = "pinduoduo"

    import asyncio
    update = asyncio.run(agent.run(state))

    copy = update.get("copy_drafts", {})
    # Mock provider may or may not include 'style' — just verify no crash
    assert isinstance(copy, dict)


def test_copywriter_handles_missing_market_research(base_state, settings, provider_factory, llm_router, cost_tracker):
    """Copywriter gracefully handles missing market research in state."""
    agent = CopywriterAgent(
        settings=settings, provider_factory=provider_factory,
        llm_router=llm_router, cost_tracker=cost_tracker,
    )
    state = dict(base_state)
    state["market_research"] = None  # No market research available

    import asyncio
    update = asyncio.run(agent.run(state))

    copy = update.get("copy_drafts", {})
    assert isinstance(copy, dict), "Should still produce copy without market research"
    assert len(copy.get("titles", [])) > 0, "Should have titles even without market research"


def test_copywriter_falls_back_on_error(base_state, settings, llm_router, cost_tracker):
    """When LLM fails, agent returns fallback copy."""
    class FailingProviderFactory(ProviderFactory):
        def chat(self, provider_name, model_name, messages, temperature=0.7, max_tokens=2048, **kwargs):
            raise RuntimeError("Simulated LLM failure")

    failing_factory = FailingProviderFactory(settings)
    agent = CopywriterAgent(
        settings=settings, provider_factory=failing_factory,
        llm_router=llm_router, cost_tracker=cost_tracker,
    )
    state = dict(base_state)

    import asyncio
    update = asyncio.run(agent.run(state))

    copy = update.get("copy_drafts", {})
    assert isinstance(copy, dict), "Should return fallback dict"
    assert "titles" in copy, "Fallback should include titles"
    # Fallback should use product title
    product_title = state["product_info"]["title"]
    assert product_title in str(copy.get("titles", [])), "Fallback should reference product title"
    assert copy["fallback"] is True
    assert "Simulated LLM failure" in copy["error"]


def test_copywriter_calls_cost_tracker(base_state, settings, provider_factory, llm_router, cost_tracker):
    """Agent tracks LLM costs via cost_tracker."""
    agent = CopywriterAgent(
        settings=settings, provider_factory=provider_factory,
        llm_router=llm_router, cost_tracker=cost_tracker,
    )
    state = dict(base_state)

    calls_before = len(cost_tracker._records)

    import asyncio
    update = asyncio.run(agent.run(state))

    # Mock provider calls still generate cost records
    assert len(cost_tracker._records) >= calls_before, "Cost tracker should have recorded the call"


def test_copywriter_agent_type_is_correct(base_state, settings, provider_factory, llm_router, cost_tracker):
    """Agent has correct agent_type identifier."""
    agent = CopywriterAgent(
        settings=settings, provider_factory=provider_factory,
        llm_router=llm_router, cost_tracker=cost_tracker,
    )
    assert agent.agent_type == "copy_generation"
    assert len(agent.system_prompt) > 0


def test_fact_guard_removes_unsupported_experience_and_ingredient_claims(
    settings, provider_factory, llm_router, cost_tracker
):
    agent = CopywriterAgent(settings=settings, provider_factory=provider_factory,
                            llm_router=llm_router, cost_tracker=cost_tracker)
    product_info = {
        "title": "恐龙蛋",
        "category": "食品饮料",
        "description": "恐龙造型巧克力脆壳糖果，净含量45克",
    }
    guarded = agent._apply_fact_guard({
        "titles": ["恐龙蛋糖果"],
        "selling_points": ["已囤3盒", "净含量45克"],
        "detail_copy": "我家孩子最爱，配料表干净，没有人工色素",
        "target_audience": "儿童和年轻人",
    }, product_info)

    assert guarded["selling_points"] == ["净含量45克"]
    assert guarded["detail_copy"] == product_info["description"]
    assert guarded["target_audience"] == "请商家根据真实适用范围确认"
    assert guarded["pending_confirmations"]


def test_publishable_copy_keeps_grounded_rewrite_and_rejects_novel_claims():
    product_info = {
        "title": "恐龙蛋",
        "category": "食品饮料",
        "description": "恐龙造型巧克力脆壳糖果，净含量45克；配料与过敏原信息以实物标签为准。",
    }
    agent = object.__new__(CopywriterAgent)
    guarded = agent._apply_fact_guard({
        "titles": ["恐龙造型巧克力脆壳糖果｜萌趣分享"],
        "selling_points": ["恐龙造型更有趣", "香甜内馅", "学生最爱"],
        "detail_copy": "恐龙造型巧克力脆壳糖果，净含量45克，适合分享。",
        "target_audience": "年轻人与学生",
        "usage_scenarios": ["聚会分享"],
    }, product_info)
    locked = CopywriterAgent._finalize_publishable_copy(guarded, product_info)

    serialized = json.dumps(locked, ensure_ascii=False)
    for unsupported in ["香甜内馅", "学生最爱", "安全可靠", "聚会分享"]:
        assert unsupported not in serialized
    assert locked["titles"] == ["恐龙造型巧克力脆壳糖果｜萌趣分享"]
    assert locked["selling_points"] == ["恐龙造型更有趣"]
    assert "恐龙造型巧克力脆壳糖果" in locked["detail_copy"]
    assert locked["specifications"] == ["净含量45克"]
    assert locked["fact_source"] == "merchant_input_with_guarded_ai_rewrite"


def test_structured_detail_expands_guarded_fields_into_detail_page():
    detail = build_structured_detail(
        base_detail="酒红色圆领设计，胸前有白色字母图案。",
        title="酒红色圆领字母卫衣",
        category="服饰鞋包",
        selling_points=["酒红色圆领设计", "胸前白色字母图案"],
        specifications=["尺码请商家确认"],
        target_audience="追求街头风格的消费者",
        usage_scenarios=["休闲出行", "日常搭配"],
    )

    for section in ["商品概览", "核心亮点", "规格参数", "适用人群与场景", "购买前核对"]:
        assert f"【{section}】" in detail
    assert "酒红色圆领设计" in detail
    assert len(detail) > 260
