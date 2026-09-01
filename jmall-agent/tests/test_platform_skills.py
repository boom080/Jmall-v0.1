"""M4 contract tests: one platform, independent rules, grounded output and provenance."""

import asyncio
import json
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.agents.orchestrator import OrchestratorAgent
from app.agents.style_adapter import StyleAdapterAgent
from app.api.dependencies import get_provider_factory
from app.core.config import get_settings
from app.main import app
from app.models.agent_models import CopyOnlyRequest, OrchestrateRequest, StylePreviewRequest
from app.platform_skills.registry import PLATFORM_SKILLS, ProductDraft, get_platform_skill


def provider_for(payload):
    provider = Mock()
    provider.chat.return_value = {
        "success": True, "content": json.dumps(payload, ensure_ascii=False),
        "provider": "mock", "model": "mock", "input_tokens": 1, "output_tokens": 1,
    }
    return provider


@pytest.mark.parametrize("platform", PLATFORM_SKILLS)
def test_one_skill_prompt_one_call_one_draft(platform, settings, llm_router, cost_tracker):
    skill = get_platform_skill(platform)
    provider = provider_for(skill.example["draft"])
    agent = StyleAdapterAgent(settings, provider, llm_router, cost_tracker)
    result = asyncio.run(agent.run({"target_style": platform, "product_info": skill.example["merchant_facts"]}))["style_previews"]
    provider.chat.assert_called_once()
    system_prompt = provider.chat.call_args.kwargs["messages"][0]["content"]
    assert skill.skill_id in system_prompt
    for other in PLATFORM_SKILLS.values():
        if other.platform != platform:
            assert other.skill_id not in system_prompt
    assert agent.system_prompt == agent.SYSTEM_PROMPT  # no shared prompt mutation
    assert set(result["previews"]) == {platform}
    assert result["platform_skill_id"] == f"{platform}_listing_v1"
    assert result["platform_skill_version"] == "1.0.0"
    assert not result["fallback"]
    assert not result["guarded"]
    draft = ProductDraft.model_validate(result["draft"])
    assert len(draft.titles) == 1
    assert len(draft.titles[0]) <= skill.title_max_length
    assert all(heading in draft.detail_copy for heading in skill.detail_sections)
    assert draft.specifications == ["宽35厘米，高30厘米"]
    assert draft.subtitle
    assert 8 <= len(draft.seo_keywords) <= 12


@pytest.mark.parametrize("invalid", ["amazon", "", "  ", None, 9, "../../jd"])
@pytest.mark.parametrize("model", [OrchestrateRequest, CopyOnlyRequest, StylePreviewRequest])
def test_invalid_platform_is_rejected_at_request_boundary(model, invalid):
    with pytest.raises(ValidationError):
        model(product_info={"title": "商品"}, target_style=invalid)


def test_invalid_platform_direct_agent_and_graph_do_not_call_models(settings, llm_router, graph, base_state):
    provider = Mock()
    agent = StyleAdapterAgent(settings, provider, llm_router)
    with pytest.raises(ValueError):
        asyncio.run(agent.run({"target_style": "amazon"}))
    provider.chat.assert_not_called()
    with pytest.raises(ValueError):
        asyncio.run(graph.invoke({**base_state, "target_style": "amazon"}))
    assert graph.cost_tracker.get_stats()["total_calls"] == 0


@pytest.mark.parametrize("payload", [
    {}, [], {"titles": "坏类型", "selling_points": [], "detail_copy": "商品"},
    {"titles": ["一", "二"], "selling_points": [], "detail_copy": "商品"},
    {"titles": ["商品"], "selling_points": [], "detail_copy": "商品", "previews": {"jd": {}}},
    {"titles": ["商品"], "selling_points": [], "detail_copy": "商品", "platform_skill_id": "forged"},
])
def test_bad_schema_falls_back_to_selected_merchant_facts(payload, settings, llm_router):
    skill = get_platform_skill("xiaohongshu")
    provider = provider_for(payload)
    result = asyncio.run(StyleAdapterAgent(settings, provider, llm_router).run({
        "target_style": skill.platform, "product_info": skill.example["merchant_facts"],
        "copy_drafts": {"titles": ["假文案"], "detail_copy": "虚构京东自营"},
    }))["style_previews"]
    assert result["fallback"]
    assert set(result["previews"]) == {skill.platform}
    assert result["platform_skill_id"] == skill.skill_id
    assert "假文案" not in json.dumps(result, ensure_ascii=False)
    assert "穿搭" not in result["adapted_title"]
    assert result["pending_confirmations"]


@pytest.mark.parametrize("claim", ["京东自营次日达", "免费安装全国联保", "限时抢购百亿补贴", "亲测回购", "纯棉抗菌防水", "低至9.9元", "规格待确认", "包身挺括", "保障小物件安全"])
def test_unsupported_claims_cannot_leak_through_any_publishable_field(claim, settings, llm_router):
    skill = get_platform_skill("jd")
    text = f"帆布托特包 {claim}"
    provider = provider_for({
        "titles": [text], "selling_points": [text], "detail_copy": text,
        "subtitle": text, "promotion_copy": text, "short_video_script": text,
        "specifications": [text], "target_audience": text, "usage_scenarios": [text], "seo_keywords": [text],
    })
    result = asyncio.run(StyleAdapterAgent(settings, provider, llm_router).run({
        "target_style": "jd", "product_info": skill.example["merchant_facts"],
        "copy_drafts": {"detail_copy": text},  # upstream AI is not proof
    }))["style_previews"]
    publishable = dict(result["draft"])
    publishable.pop("pending_confirmations")
    assert claim not in json.dumps(publishable, ensure_ascii=False)
    assert result["guarded"]
    assert result["pending_confirmations"]


@pytest.mark.parametrize("platform", PLATFORM_SKILLS)
def test_long_title_is_bounded(platform, settings, llm_router):
    skill = get_platform_skill(platform)
    provider = provider_for({"titles": ["帆布托特包" * 25], "selling_points": [], "detail_copy": "帆布托特包"})
    result = asyncio.run(StyleAdapterAgent(settings, provider, llm_router).run({
        "target_style": platform, "product_info": skill.example["merchant_facts"],
    }))["style_previews"]
    assert len(result["adapted_title"]) == skill.title_max_length
    assert any("缩短" in item for item in result["pending_confirmations"])


def test_aggregator_uses_entire_skill_draft_and_provenance(settings, llm_router, provider_factory):
    skill = get_platform_skill("jd")
    result = asyncio.run(StyleAdapterAgent(settings, provider_for(skill.example["draft"]), llm_router).run({
        "target_style": "jd", "product_info": skill.example["merchant_facts"],
    }))["style_previews"]
    final = OrchestratorAgent(settings, provider_factory, llm_router).aggregate_results({
        "target_style": "jd", "style_previews": result, "copy_drafts": {"subtitle": "不应继承的旧稿", "promotion_copy": "虚构优惠"},
    })
    assert final["copy"]["subtitle"] == result["draft"]["subtitle"]
    assert final["copy"]["subtitle"]
    assert final["copy"]["promotion_copy"] == ""
    assert final["copy"]["titles"] == result["draft"]["titles"]
    assert final["generation_metadata"]["platform_skill_id"] == skill.skill_id
    assert final["style_adaptation"]["platform_skill_version"] == skill.version


def test_sourced_market_research_expands_audience_and_seo_without_inventing_attributes(
    settings, llm_router,
):
    skill = get_platform_skill("taobao")
    facts = skill.example["merchant_facts"]
    payload = {
        **skill.example["draft"],
        "subtitle": "米白色包身，内置拉链袋",
        "target_audience": "通勤上班族",
        "seo_keywords": ["帆布托特包"],
    }
    result = asyncio.run(StyleAdapterAgent(settings, provider_for(payload), llm_router).run({
        "target_style": "taobao",
        "product_info": facts,
        "market_research": {
            "status": "ready",
            "hot_keywords": ["帆布托特包 通勤", "大容量帆布托特包", "2026爆款"],
            "audience_segments": ["都市通勤人群", "周末出行用户", "孕妇妈妈"],
            "sources": [{"title": "公开市场资料", "url": "https://example.com/report"}],
        },
    }))["style_previews"]

    draft = result["draft"]
    assert draft["subtitle"] == "米白色包身，内置拉链袋"
    assert draft["target_audience"] == "通勤上班族；都市通勤人群；周末出行用户"
    assert "孕妇妈妈" not in draft["target_audience"]
    assert "帆布托特包 通勤" in draft["seo_keywords"]
    assert "大容量帆布托特包" not in draft["seo_keywords"]
    assert "2026爆款" not in draft["seo_keywords"]
    assert 8 <= len(draft["seo_keywords"]) <= 12
    assert result["marketing_enrichment"] == {
        "source": "market_research",
        "source_urls": ["https://example.com/report"],
        "research_used": True,
        "subtitle_generated": True,
        "audience_expanded": True,
        "seo_expanded": True,
    }


def test_long_paragraph_can_supply_structured_facts_without_filling_every_box(settings, llm_router):
    facts = {"title": "帆布托特包", "category": "服饰鞋包", "description":
             "米白色帆布托特包，宽35厘米，高30厘米，内置拉链袋，面向通勤上班族，用于日常通勤。"}
    provider = provider_for({"titles": ["米白色帆布托特包"], "selling_points": ["内置拉链袋"],
        "detail_copy": facts["description"], "specifications": ["宽35厘米，高30厘米"],
        "target_audience": "通勤上班族", "usage_scenarios": ["日常通勤"], "seo_keywords": ["帆布托特包"]})
    result = asyncio.run(StyleAdapterAgent(settings, provider, llm_router).run({
        "target_style": "taobao", "product_info": facts,
    }))["style_previews"]
    assert result["draft"]["specifications"] == ["宽35厘米，高30厘米"]
    assert result["draft"]["target_audience"] == "通勤上班族"
    assert result["draft"]["usage_scenarios"] == ["日常通勤"]
    assert not result["pending_confirmations"]


@pytest.mark.parametrize("platform", PLATFORM_SKILLS)
def test_graph_keeps_one_platform_and_skill_metadata(platform, graph, base_state):
    final = asyncio.run(graph.invoke({**base_state, "target_style": platform}))["final_result"]
    assert set(final["style_adaptation"]["previews"]) == {platform}
    assert final["generation_metadata"]["platform_skill_id"] == f"{platform}_listing_v1"
    assert len(final["copy"]["titles"]) == 1


def test_compliance_reviews_final_platform_copy_without_extra_model_call(graph, base_state, monkeypatch):
    from unittest.mock import AsyncMock
    reviewer = graph._get_reviewer()
    review = AsyncMock(return_value={"review_result": {"status": "passed"}})
    monkeypatch.setattr(reviewer, "run", review)
    result = asyncio.run(graph.invoke({**base_state, "target_style": "jd"}))
    review.assert_awaited_once()
    reviewed_draft = review.call_args.args[0]["copy_drafts"]
    assert reviewed_draft == result["style_previews"]["draft"]
    assert reviewed_draft["titles"] == result["final_result"]["copy"]["titles"]


def test_final_review_includes_full_detail_and_original_structured_facts(settings, llm_router):
    from app.agents.reviewer import ReviewerAgent
    provider = provider_for({"status": "passed", "issues": [], "warnings": []})
    detail = "商品说明" * 100 + "末尾必须核对的内容"
    asyncio.run(ReviewerAgent(settings, provider, llm_router).run({
        "product_info": {"title": "帆布包", "category": "服饰鞋包", "description": "米白色", "target_audience": "通勤上班族", "specifications": "宽35厘米"},
        "copy_drafts": {"titles": ["帆布包"], "detail_copy": detail, "subtitle": "同样需要审查的副标题"},
    }))
    prompt = provider.chat.call_args.kwargs["messages"][-1]["content"]
    assert "末尾必须核对的内容" in prompt
    assert "通勤上班族" in prompt
    assert "宽35厘米" in prompt
    assert "同样需要审查的副标题" in prompt


def test_preview_gate_and_platform_preflight_are_model_free(settings):
    provider = Mock()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_provider_factory] = lambda: provider
    try:
        with TestClient(app) as client:
            response = client.post("/api/styles/preview", json={"product_info": {"title": "杯子"}, "target_style": "jd"})
            assert response.status_code == 422
            assert not response.json()["detail"]["input_assessment"]["ready"]
            response = client.post("/api/agent/input-assessment", json={"product_info": {"title": "杯子"}, "target_style": "amazon"})
            assert response.status_code == 422
        provider.chat.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_standalone_preview_returns_skill_contract(settings, llm_router):
    skill = get_platform_skill("jd")
    provider = provider_for(skill.example["draft"])
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_provider_factory] = lambda: provider
    try:
        with TestClient(app) as client:
            response = client.post("/api/styles/preview", json={"product_info": skill.example["merchant_facts"], "target_style": " JD "})
            assert response.status_code == 200
            data = response.json()
            assert data["platform_skill_id"] == skill.skill_id
            assert data["draft"]["titles"] == skill.example["draft"]["titles"]
            styles = client.get("/api/styles").json()["styles"]
            assert len(styles) == 5
            assert all(style["platform_skill_version"] for style in styles)
    finally:
        app.dependency_overrides.clear()


def test_copy_endpoint_also_delivers_one_versioned_platform_draft(settings, provider_factory):
    from app.api.agent import product_copy_only
    skill = get_platform_skill("jd")
    response = asyncio.run(product_copy_only(
        CopyOnlyRequest(product_info=skill.example["merchant_facts"], target_style="jd"),
        settings, provider_factory, None,
    ))
    assert response.platform_skill_id == skill.skill_id
    assert response.platform_skill_version == skill.version
    assert response.titles == response.draft.titles
    assert len(response.titles) == 1
