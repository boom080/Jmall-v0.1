"""Unit tests for StyleAdapterAgent.

Covers: happy path with all 5 styles, error fallback, style profile lookup.
"""

import json

from app.agents.style_adapter import StyleAdapterAgent, STYLE_PROFILES
from app.providers.factory import ProviderFactory


def test_style_adapter_returns_adapted_content(base_state, settings, provider_factory, llm_router, cost_tracker):
    """Happy path: mock provider returns style-adapted copy."""
    agent = StyleAdapterAgent(settings, provider_factory, llm_router, cost_tracker)
    state = dict(base_state)
    state["copy_drafts"] = {
        "titles": ["品质静音破壁机"],
        "selling_points": ["低噪音", "一键清洗"],
        "detail_copy": "高品质静音破壁机，让厨房更安静。",
    }
    state["target_style"] = "taobao"

    import asyncio
    update = asyncio.run(agent.run(state))

    style_previews = update.get("style_previews", {})
    assert isinstance(style_previews, dict), "Should return a dict"
    # Mock provider returns adapted_* fields directly
    has_adapted = any(k for k in style_previews if "adapted" in k or "target_style" in k)
    assert has_adapted or len(style_previews) > 0, "Should have adapted content"


def test_style_adapter_works_for_all_styles(base_state, settings, provider_factory, llm_router, cost_tracker):
    """All 5 platform styles work correctly."""
    styles = ["taobao", "jd", "pinduoduo", "suning", "xiaohongshu"]

    for style in styles:
        agent = StyleAdapterAgent(settings, provider_factory, llm_router, cost_tracker)
        state = dict(base_state)
        state["target_style"] = style
        state["copy_drafts"] = {
            "titles": ["测试商品标题"],
            "selling_points": ["卖点1", "卖点2"],
            "detail_copy": "测试详情文案。",
        }

        import asyncio
        update = asyncio.run(agent.run(state))

        style_previews = update.get("style_previews", {})
        assert isinstance(style_previews, dict), f"Style '{style}' should return dict"


def test_style_adapter_falls_back_on_error(base_state, settings, llm_router, cost_tracker):
    """When LLM fails, agent returns fallback with original copy."""
    class FailingProviderFactory(ProviderFactory):
        def chat(self, provider_name, model_name, messages, temperature=0.7, max_tokens=2048, **kwargs):
            raise RuntimeError("Simulated LLM failure")

    failing_factory = FailingProviderFactory(settings)
    agent = StyleAdapterAgent(settings, failing_factory, llm_router, cost_tracker)
    state = dict(base_state)
    state["copy_drafts"] = {
        "titles": ["原始标题"],
        "selling_points": ["原始卖点"],
        "detail_copy": "原始详情",
    }

    import asyncio
    update = asyncio.run(agent.run(state))

    style_previews = update.get("style_previews", {})
    assert isinstance(style_previews, dict), "Should return fallback dict"
    # Fallback passes through original titles
    adapted_title = style_previews.get("adapted_title", "")
    assert len(adapted_title) > 0 or style_previews.get("target_style") is not None
    assert style_previews["fallback"] is True
    assert "Simulated LLM failure" in style_previews["error"]


def test_get_available_styles_returns_all_profiles(base_state, settings, provider_factory, llm_router, cost_tracker):
    """get_available_styles() returns all 5 platform definitions."""
    styles = StyleAdapterAgent.get_available_styles()
    assert isinstance(styles, dict), "Should return dict"
    expected = {"taobao", "jd", "pinduoduo", "suning", "xiaohongshu"}
    assert set(styles.keys()) == expected, f"Should have all 5 styles, got: {set(styles.keys())}"

    for style_id, info in styles.items():
        assert "name" in info, f"Style '{style_id}' should have name"
        assert "description" in info, f"Style '{style_id}' should have description"


def test_style_profiles_have_required_fields(base_state, settings, provider_factory, llm_router, cost_tracker):
    """Each STYLE_PROFILES entry has name, title_style, color_scheme."""
    required = ["name", "title_style", "color_scheme"]
    for style_id, profile in STYLE_PROFILES.items():
        for field in required:
            assert field in profile, f"Style '{style_id}' missing required field: {field}"


def test_style_adapter_rejects_experience_claims_and_returns_five_previews(
    base_state, settings, llm_router, cost_tracker
):
    class UnsafeProviderFactory(ProviderFactory):
        def chat(self, provider_name, model_name, messages, temperature=0.7, max_tokens=2048, **kwargs):
            return {
                "success": True,
                "content": json.dumps({
                    "adapted_title": "我上周囤了3盒",
                    "adapted_selling_points": ["没有人工色素"],
                    "adapted_detail": "我家孩子最爱",
                    "visual_params": {},
                    "style_notes": "小红书风",
                }, ensure_ascii=False),
                "input_tokens": 1,
                "output_tokens": 1,
                "provider": "mock",
                "model": "mock-product-copy-v1",
            }

    original = {
        "titles": ["恐龙蛋巧克力糖果"],
        "selling_points": ["净含量45克"],
        "detail_copy": "恐龙造型巧克力脆壳糖果，净含量45克",
    }
    state = dict(base_state)
    state["product_info"] = {
        "title": "恐龙蛋",
        "category": "食品饮料",
        "description": original["detail_copy"],
    }
    state["copy_drafts"] = original
    agent = StyleAdapterAgent(settings, UnsafeProviderFactory(settings), llm_router, cost_tracker)

    import asyncio
    result = asyncio.run(agent.run(state))["style_previews"]
    assert set(result["previews"]) == set(STYLE_PROFILES)
    serialized = json.dumps(result, ensure_ascii=False)
    for unsafe in ["我上周囤了3盒", "没有人工色素", "我家孩子最爱"]:
        assert unsafe not in serialized
    assert original["detail_copy"] in result["adapted_detail"]


def test_style_adapter_blocks_fabricated_social_proof_title(
    base_state, settings, llm_router, cost_tracker
):
    class SocialProofProviderFactory(ProviderFactory):
        def chat(self, provider_name, model_name, messages, temperature=0.7, max_tokens=2048, **kwargs):
            return {
                "success": True,
                "content": json.dumps({
                    "adapted_title": "这件卫衣让我被朋友追着问链接",
                    "adapted_selling_points": ["酒红色不挑肤色"],
                    "adapted_detail": "酒红色圆领设计，胸前有白色字母图案。",
                    "visual_params": {},
                    "style_notes": "小红书风",
                }, ensure_ascii=False),
                "input_tokens": 1,
                "output_tokens": 1,
                "provider": "mock",
                "model": "mock-product-copy-v1",
            }

    state = dict(base_state)
    state["product_info"] = {
        "title": "酒红色圆领字母卫衣",
        "category": "服饰鞋包",
        "description": "酒红色圆领设计，胸前有白色字母图案。",
    }
    state["copy_drafts"] = {
        "titles": ["酒红色圆领字母卫衣"],
        "selling_points": ["酒红色圆领设计", "胸前白色字母图案"],
        "detail_copy": "酒红色圆领设计，胸前有白色字母图案。",
    }
    state["target_style"] = "xiaohongshu"

    import asyncio
    result = asyncio.run(
        StyleAdapterAgent(
            settings, SocialProofProviderFactory(settings), llm_router, cost_tracker
        ).run(state)
    )["style_previews"]

    serialized = json.dumps(result, ensure_ascii=False)
    assert "朋友追着问链接" not in serialized
    assert "不挑肤色" not in serialized
    assert result["adapted_title"].startswith("今日穿搭灵感｜")


def test_style_adapter_blocks_research_claims_and_personal_story(
    base_state, settings, llm_router, cost_tracker
):
    class StoryProviderFactory(ProviderFactory):
        def chat(self, provider_name, model_name, messages, temperature=0.7, max_tokens=2048, **kwargs):
            return {
                "success": True,
                "content": json.dumps({
                    "adapted_title": "马年本命红卫衣",
                    "adapted_selling_points": [
                        "洗过两次也不起球",
                        "圆领刚刚好，不勒脖也不滑落",
                    ],
                    "adapted_detail": "上周穿去咖啡店，陌生人要了三次链接。秋冬必备，穿着舒适。",
                    "visual_params": {},
                    "style_notes": "小红书风",
                }, ensure_ascii=False),
                "input_tokens": 1,
                "output_tokens": 1,
                "provider": "mock",
                "model": "mock-product-copy-v1",
            }

    state = dict(base_state)
    state["product_info"] = {
        "title": "酒红色圆领字母卫衣",
        "category": "服饰鞋包",
        "description": "酒红色圆领设计，胸前有白色字母图案。",
    }
    state["copy_drafts"] = {
        "titles": ["酒红色圆领字母卫衣"],
        "selling_points": ["酒红色圆领设计", "胸前白色字母图案"],
        "detail_copy": "酒红色圆领设计，胸前有白色字母图案。",
    }
    state["target_style"] = "xiaohongshu"
    state["market_research"] = {"hot_keywords": ["本命年幸运色", "马年穿搭"]}

    import asyncio
    result = asyncio.run(
        StyleAdapterAgent(
            settings, StoryProviderFactory(settings), llm_router, cost_tracker
        ).run(state)
    )["style_previews"]

    serialized = json.dumps(result, ensure_ascii=False)
    for unsafe in [
        "马年本命红", "洗过两次也不起球", "不勒脖也不滑落",
        "上周穿去咖啡店", "陌生人要了三次链接", "秋冬必备", "穿着舒适",
    ]:
        assert unsafe not in serialized
    assert result["adapted_title"].startswith("今日穿搭灵感｜")
    assert "【商品概览】" in result["adapted_detail"]
    assert "【购买前核对】" in result["adapted_detail"]
