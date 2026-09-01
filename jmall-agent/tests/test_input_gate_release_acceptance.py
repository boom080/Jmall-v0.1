"""Release acceptance counterexamples found by the 2026-08-31 audit.

These are ordinary regression tests, not xfail: a release must not regard
subjective praise or explicitly unknown information as a complete brief.
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api import agent as agent_api
from app.agents.input_gate import assess_product_input
from app.main import app
from app.models.agent_models import CopyOnlyRequest, StylePreviewRequest
from app.models.image_models import ImageCandidatesRequest
from app.services.image_scout_service import ImageScoutService


INCOMPLETE_BRIEFS = [
        pytest.param(
            {"specifications": "很棒；喜欢", "target_audience": "学生"},
            "商品事实或规格", id="subjective-praise-is-not-product-evidence",
        ),
        pytest.param(
            {"specifications": "材质未知；容量未知", "target_audience": "学生"},
            "商品事实或规格", id="unknown-specifications-are-not-facts",
        ),
        pytest.param(
            {"specifications": "304不锈钢；500毫升", "target_audience": "不知道呢"},
            "目标人群", id="unknown-audience-is-not-a-real-audience",
        ),
        pytest.param(
            {"description": "不知道材质型号，也没有尺寸重量等信息，具体商品功能暂时不了解，只知道适合学生使用。"},
            "商品事实或规格", id="negated-fact-markers-are-not-evidence",
        ),
]


def product_info(fields):
    return {"title": "保温水杯", "category": "家居日用", **fields}


def assert_needs_input(assessment, expected_missing):
    assert assessment["ready"] is False, f"Incomplete merchant information was accepted: {assessment}"
    assert assessment["status"] == "needs_input"
    assert expected_missing in assessment["missing"]
    assert 1 <= len(assessment["questions"]) <= 3


@pytest.mark.parametrize("fields,expected_missing", INCOMPLETE_BRIEFS)
def test_incomplete_semantic_information_must_not_unlock_generation(fields, expected_missing):
    assert_needs_input(assess_product_input(product_info(fields)), expected_missing)


@pytest.mark.parametrize("fields,expected_missing", INCOMPLETE_BRIEFS)
def test_semantic_rejection_reaches_free_http_preflight(fields, expected_missing, monkeypatch):
    factory = Mock(side_effect=AssertionError("Free preflight must not construct model providers"))
    monkeypatch.setattr("app.providers.factory.ProviderFactory.__init__", factory)
    response = TestClient(app).post("/api/agent/input-assessment", json={
        "product_info": product_info(fields), "target_style": "taobao",
    })
    assert response.status_code == 200
    assert_needs_input(response.json()["input_assessment"], expected_missing)
    factory.assert_not_called()


@pytest.mark.parametrize("fields,expected_missing", INCOMPLETE_BRIEFS)
def test_semantic_rejection_stops_graph_before_agents_and_tokens(fields, expected_missing, graph):
    events = []

    async def callback(agent_name, status, result):
        events.append(agent_name)

    result = asyncio.run(graph.invoke({
        "product_info": product_info(fields), "target_style": "taobao", "errors": [],
    }, progress_callback=callback))
    final = result["final_result"]
    assert final["overall_status"] == "needs_input"
    assert_needs_input(final["input_assessment"], expected_missing)
    assert not any(graph.get_agent_status().values())
    assert graph.cost_tracker.get_stats()["total_calls"] == 0
    assert events == ["input_assessment", "orchestration_complete"]


@pytest.mark.parametrize("fields,expected_missing", INCOMPLETE_BRIEFS)
def test_semantic_rejection_cannot_bypass_via_copy(fields, expected_missing, settings, monkeypatch):
    constructor = Mock(side_effect=AssertionError("Incomplete input must not construct a copywriter"))
    monkeypatch.setattr(agent_api, "CopywriterAgent", constructor)
    response = asyncio.run(agent_api.product_copy_only(
        CopyOnlyRequest(product_info=product_info(fields), target_style="taobao"),
        settings, None, None,
    ))
    assert response.success is False
    assert response.titles == []
    assert_needs_input(response.input_assessment.model_dump(), expected_missing)
    constructor.assert_not_called()


@pytest.mark.parametrize("fields,expected_missing", INCOMPLETE_BRIEFS)
def test_semantic_rejection_cannot_bypass_via_style_preview(fields, expected_missing, settings, monkeypatch):
    constructor = Mock(side_effect=AssertionError("Incomplete input must not construct a style adapter"))
    monkeypatch.setattr(agent_api, "StyleAdapterAgent", constructor)
    with pytest.raises(HTTPException) as error:
        asyncio.run(agent_api.preview_style(
            StylePreviewRequest(product_info=product_info(fields), target_style="taobao"),
            settings, None,
        ))
    assert error.value.status_code == 422
    assert_needs_input(error.value.detail["input_assessment"], expected_missing)
    constructor.assert_not_called()


@pytest.mark.parametrize("fields,expected_missing", INCOMPLETE_BRIEFS)
def test_semantic_rejection_stops_image_search(fields, expected_missing):
    provider = Mock()
    provider.name = "release-test"
    provider.search = AsyncMock(side_effect=AssertionError("Incomplete input must not search images"))
    response = asyncio.run(ImageScoutService(provider, resolve_dns=False).find_candidates(
        ImageCandidatesRequest(product_info=product_info(fields)),
    ))
    assert response.status == "needs_input"
    assert response.candidates == []
    assert_needs_input(response.input_assessment.model_dump(), expected_missing)
    provider.search.assert_not_awaited()


@pytest.mark.parametrize("fields,expected_missing", [
    ({"description": "这个商品功能非常强大非常适合学生使用。"}, "商品事实或规格"),
    ({"specifications": "容量500毫升真的特别棒超级喜欢", "target_audience": "学生"}, "商品事实或规格"),
    ({"specifications": "500毫升很棒；500毫升不错", "target_audience": "学生"}, "商品事实或规格"),
    ({"specifications": "500毫升", "description": "500毫升", "target_audience": "学生"}, "商品事实或规格"),
    ({"specifications": "material: unknown; capacity: not known", "target_audience": "学生"}, "商品事实或规格"),
    ({"specifications": "304不锈钢；500毫升", "target_audience": "人群还没明确"}, "目标人群"),
    ({"specifications": "304不锈钢；500毫升", "description": "不知道适合学生还是老人。"}, "目标人群"),
    ({"specifications": "304不锈钢；500毫升", "description": "不适合学生使用。"}, "目标人群"),
    ({"specifications": "材质 未 知；容量 待 确 认", "target_audience": "学生"}, "商品事实或规格"),
    ({"specifications": "304不锈钢；500毫升", "target_audience": "不 知 道 呢"}, "目标人群"),
    ({"specifications": "304不锈钢；500毫升", "target_audience": "不 适 合 学生"}, "目标人群"),
    ({"specifications": "304不锈钢；500毫升", "target_audience": "不\u200b知道呢"}, "目标人群"),
])
def test_padding_and_description_cannot_reintroduce_semantic_bypasses(fields, expected_missing):
    assert_needs_input(assess_product_input(product_info(fields)), expected_missing)


@pytest.mark.parametrize("fields", [
    {"specifications": "304不锈钢", "description": "容量500毫升", "target_audience": "学生"},
    {"specifications": "304不锈钢；500毫升", "description": "不适合儿童，但适合上班族。"},
    {"specifications": "304不锈钢；500毫升", "target_audience": "摄影师；其他人群待确认"},
])
def test_evidence_can_span_fields_without_unknown_details_invalidating_it(fields):
    result = assess_product_input(product_info(fields))
    assert result["ready"] is True, result
    assert result["missing"] == []
    assert result["questions"] == []
