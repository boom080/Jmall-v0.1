"""Coverage for the deterministic input gate and free preflight paths."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.agents.input_gate import assess_product_input
from app.api.agent import orchestrate, product_copy_only
from app.main import app
from app.models.agent_models import CopyOnlyRequest, OrchestrateRequest


def _long_description() -> str:
    return (
        "这是一款采用食品级不锈钢材质的保温杯，容量500毫升，支持长效保温，"
        "适合上班族和学生，主要用于办公室、通勤和旅行携带。"
    )


def test_title_and_category_only_needs_input():
    assessment = assess_product_input({"title": "智能破壁机", "category": "厨房电器"})

    assert assessment["status"] == "needs_input"
    assert assessment["ready"] is False
    assert assessment["score"] == 35
    assert "商品事实或规格" in assessment["missing"]
    assert "目标人群" in assessment["missing"]
    assert len(assessment["questions"]) <= 3


def test_trivial_structured_tokens_cannot_bypass_gate():
    assessment = assess_product_input(
        {
            "title": "杯子",
            "category": "水具",
            "specifications": "x",
            "target_audience": "人",
        }
    )

    assert assessment["status"] == "needs_input"
    assert assessment["ready"] is False
    assert "商品事实或规格" in assessment["missing"]
    assert "目标人群" in assessment["missing"]


@pytest.mark.parametrize(
    ("product_info", "expected_missing"),
    [
        (
            {
                "title": "测试商品",
                "category": "日用百货",
                "description": "这个商品很好用" * 10 + "，适合学生",
            },
            {"商品名称", "商品事实或规格"},
        ),
        (
            {
                "title": "保温水杯",
                "category": "水具用品",
                "specifications": "好用；好用",
                "target_audience": "学生",
            },
            {"商品事实或规格"},
        ),
        (
            {
                "title": "保温水杯",
                "category": "水具用品",
                "specifications": "304不锈钢；500ml",
                "target_audience": "哈哈",
            },
            {"目标人群"},
        ),
        (
            {
                "title": "测试商品",
                "category": "其他商品",
                "specifications": "参数；规格",
                "target_audience": "用户",
            },
            {"商品名称", "商品品类", "商品事实或规格", "目标人群"},
        ),
        (
            {
                "title": "\u200b\u200b",
                "category": "。。",
                "specifications": "；；",
                "target_audience": "🙂🙂🙂",
            },
            {"商品名称", "商品品类", "商品事实或规格", "目标人群"},
        ),
    ],
)
def test_adversarial_placeholders_cannot_unlock_generation(product_info, expected_missing):
    assessment = assess_product_input(product_info)

    assert assessment["status"] == "needs_input"
    assert assessment["ready"] is False
    assert expected_missing.issubset(set(assessment["missing"]))


def test_long_description_path_is_ready():
    assessment = assess_product_input(
        {"title": "轻量保温杯", "category": "水具", "description": _long_description()}
    )

    assert assessment["status"] == "ready"
    assert assessment["ready"] is True
    assert assessment["score"] == 100
    assert assessment["missing"] == []


def test_long_product_and_audience_brief_is_ready_without_scenario():
    assessment = assess_product_input(
        {
            "title": "轻量保温杯",
            "category": "水具",
            "description": (
                "我想卖一款采用食品级304不锈钢的保温杯，容量500毫升，"
                "杯盖可拆洗且支持12小时保温，主要卖给上班族和学生。"
            ),
        }
    )

    assert assessment["status"] == "ready"
    assert assessment["ready"] is True
    assert assessment["score"] == 85


def test_structured_fields_path_is_ready():
    assessment = assess_product_input(
        {
            "title": "轻量保温杯",
            "category": "水具",
            "specifications": "食品级不锈钢；容量500ml；保温12小时",
            "target_audience": "上班族和学生",
            "usage_scenarios": "办公室、通勤、旅行",
        }
    )

    assert assessment["status"] == "ready"
    assert assessment["ready"] is True
    assert assessment["missing"] == []


def test_audience_is_required_but_scenario_is_optional():
    missing_audience = assess_product_input(
        {
            "title": "轻量保温杯",
            "category": "水具",
            "specifications": "食品级不锈钢；容量500ml",
            "usage_scenarios": "办公室、通勤",
        }
    )
    missing_scenario = assess_product_input(
        {
            "title": "轻量保温杯",
            "category": "水具",
            "specifications": "食品级不锈钢；容量500ml",
            "target_audience": "上班族和学生",
        }
    )

    assert missing_audience["status"] == "needs_input"
    assert "目标人群" in missing_audience["missing"]
    assert missing_scenario["status"] == "ready"
    assert missing_scenario["score"] == 85
    assert "使用场景" not in missing_scenario["missing"]


def test_graph_hard_gate_does_not_initialize_downstream_agents(graph):
    events = []

    async def callback(agent_name, status, result):
        events.append((agent_name, status, result))

    result = asyncio.run(
        graph.invoke(
            {
                "product_info": {"title": "测试商品", "category": "厨房电器"},
                "target_style": "taobao",
                "errors": [],
            },
            progress_callback=callback,
        )
    )

    final = result["final_result"]
    assert final["overall_status"] == "needs_input"
    assert final["input_assessment"]["status"] == "needs_input"
    assert graph.get_agent_status() == {
        "orchestrator": False,
        "market_research": False,
        "copywriter": False,
        "reviewer": False,
        "style_adapter": False,
    }
    assert [event[0] for event in events] == [
        "input_assessment",
        "orchestration_complete",
    ]


def test_graph_ready_path_preserves_input_assessment(graph):
    result = asyncio.run(
        graph.invoke(
            {
                "product_info": {
                    "title": "轻量保温杯",
                    "category": "水具",
                    "description": _long_description(),
                },
                "target_style": "taobao",
                "errors": [],
            }
        )
    )

    assessment = result["final_result"]["input_assessment"]
    assert assessment["status"] == "ready"
    assert assessment["ready"] is True
    assert result["final_result"]["overall_status"] != "needs_input"


def test_orchestrate_response_exposes_ready_assessment(graph):
    request = OrchestrateRequest(
        product_info={
            "title": "轻量保温杯",
            "category": "水具",
            "description": _long_description(),
        },
        target_style="taobao",
    )

    response = asyncio.run(orchestrate(request, graph))

    assert response.input_assessment.status == "ready"
    assert response.input_assessment.ready is True
    assert response.overall_status != "needs_input"


def test_free_input_assessment_endpoint_is_nested_and_model_free():
    client = TestClient(app)
    response = client.post(
        "/api/agent/input-assessment",
        json={
            "product_info": {"title": "测试商品", "category": "厨房电器"},
            "target_style": "taobao",
        },
    )

    assert response.status_code == 200
    assessment = response.json()["input_assessment"]
    assert assessment["status"] == "needs_input"
    assert 0 <= assessment["score"] <= 100
    assert len(assessment["questions"]) <= 3


def test_free_input_assessment_accepts_empty_title_and_returns_guidance():
    client = TestClient(app)
    response = client.post(
        "/api/agent/input-assessment",
        json={
            "product_info": {"title": "", "category": "", "description": ""},
            "target_style": "taobao",
        },
    )

    assert response.status_code == 200
    assessment = response.json()["input_assessment"]
    assert assessment["status"] == "needs_input"
    assert assessment["ready"] is False
    assert "商品名称" in assessment["missing"]
    assert assessment["questions"]


def test_copy_only_path_reuses_gate_without_initializing_agent(
    settings, provider_factory
):
    request = CopyOnlyRequest(
        product_info={"title": "测试商品", "category": "厨房电器"},
        target_style="taobao",
    )

    response = asyncio.run(product_copy_only(request, settings, provider_factory, None))

    assert response.success is False
    assert response.input_assessment.status == "needs_input"
    assert response.titles == []
