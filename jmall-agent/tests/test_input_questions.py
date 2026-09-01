"""M5 category golden cases: questions change, sufficiency rules do not."""

import pytest
from fastapi.testclient import TestClient

from app.agents.input_gate import assess_product_input
from app.agents.input_questions import CATEGORY_FACT_HINTS, category_bucket
from app.main import app


@pytest.mark.parametrize("category,marker", [
    ("食品饮料", "净含量"), ("服饰鞋包", "尺码"), ("家居日用", "容量"),
    ("数码家电", "兼容范围"), ("美妆护肤", "肤质"), ("运动户外", "承重"),
])
def test_six_categories_ask_concrete_questions_without_starting_generation(category, marker):
    result = assess_product_input({"title": "具体商品", "category": category})
    assert result["status"] == "needs_input"
    assert result["missing"] == ["商品事实或规格", "目标人群"]
    assert len(result["questions"]) == 2
    assert marker in result["questions"][0]
    assert "不必全部填写" in result["questions"][0]


@pytest.mark.parametrize("category", list(CATEGORY_FACT_HINTS))
@pytest.mark.parametrize("brief", [
    {"specifications": "米白色；内置拉链袋", "target_audience": "通勤上班族"},
    {"description": "我想卖米白色帆布包，内置一个拉链袋，包口为敞口设计，宽35厘米、高30厘米，主要面向通勤上班族。"},
])
def test_templates_never_require_all_suggested_attributes(category, brief):
    result = assess_product_input({"title": "帆布托特包", "category": category, **brief})
    assert result["ready"] is True
    assert result["questions"] == []


def test_only_missing_fields_are_asked_and_at_most_three():
    assert len(assess_product_input({})["questions"]) == 3
    result = assess_product_input({"title": "零食饼干", "category": "食品饮料", "specifications": "原味；净含量200克"})
    assert result["missing"] == ["目标人群"]
    assert len(result["questions"]) == 1
    assert "食用" in result["questions"][0]


def test_aliases_generic_fallback_and_cup_specific_hint():
    assert category_bucket("数码产品") == "数码家电"
    assert category_bucket("任意秘密品类") == "其他"
    cup = assess_product_input({"title": "保温杯", "category": "水具"})
    assert "保温时长" in cup["questions"][0]
    unknown = assess_product_input({"title": "文创摆件", "category": "图书文娱"})
    assert "具体特点" in unknown["questions"][0]


def test_free_endpoint_exposes_category_questions_and_supports_recheck():
    with TestClient(app) as client:
        request = {"product_info": {"title": "苏打饼干", "category": "食品饮料"}, "target_style": "taobao"}
        rejected = client.post("/api/agent/input-assessment", json=request)
        assert rejected.status_code == 200
        assert "净含量" in rejected.json()["input_assessment"]["questions"][0]
        request["product_info"].update(specifications="原味；净含量200克", target_audience="办公室上班族")
        accepted = client.post("/api/agent/input-assessment", json=request)
        assert accepted.json()["input_assessment"]["ready"] is True
