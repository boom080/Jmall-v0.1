"""Deterministic semantic-boundary tests for the zero-LLM input gate.

These cases intentionally exercise the distinction between grounded product
facts and praise, placeholders, or negated/unknown claims.  They call only
``assess_product_input``; no model, HTTP service, or application fixture is
needed.
"""

import pytest

from app.agents.input_gate import assess_product_input


BASE_BRIEF = {
    "title": "保温水杯",
    "category": "家居日用",
    "specifications": "304不锈钢；容量500毫升",
    "target_audience": "上班族",
}


def _brief(**overrides):
    brief = dict(BASE_BRIEF)
    brief.update(overrides)
    return brief


def _assert_needs_input(brief, expected_missing):
    assessment = assess_product_input(brief)

    assert assessment["ready"] is False, assessment
    assert assessment["status"] == "needs_input"
    assert expected_missing in assessment["missing"]
    assert 1 <= len(assessment["questions"]) <= 3


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("specifications", "很棒；喜欢"),
        ("specifications", "超级好用；非常漂亮"),
        ("specifications", "功能强大；设计优秀"),
        ("selling_points", "很棒；喜欢"),
        ("selling_points", "超级好用；非常漂亮"),
        ("selling_points", "功能强大；设计优秀"),
    ],
)
def test_subjective_praise_cannot_supply_product_facts(field, value):
    # Remove the valid structured facts when the selling-points channel is
    # under test as well; praise must not be the sole evidence source.
    overrides = {"specifications": None, field: value}
    _assert_needs_input(
        _brief(**overrides),
        "商品事实或规格",
    )


@pytest.mark.parametrize(
    "specifications",
    [
        "材质不清楚；容量待确认",
        "规格暂未提供；功能还不知道",
        "材质：？；容量：？",
    ],
)
def test_unknown_structured_facts_cannot_unlock_generation(specifications):
    _assert_needs_input(
        _brief(specifications=specifications),
        "商品事实或规格",
    )


def test_negated_description_is_not_grounded_product_evidence():
    _assert_needs_input(
        _brief(
            specifications=None,
            description="没有材质和容量信息，也不知道具体功能，适合学生使用。",
        ),
        "商品事实或规格",
    )


@pytest.mark.parametrize(
    "target_audience",
    [
        "暂时不知道适合谁",
        "不知道是不是适合学生",
        "目标人群还没确定",
        "不适合学生使用",
    ],
)
def test_unknown_or_negative_audience_cannot_unlock_generation(target_audience):
    _assert_needs_input(
        _brief(target_audience=target_audience),
        "目标人群",
    )


def test_one_known_fact_plus_one_unknown_fact_is_still_insufficient():
    _assert_needs_input(
        _brief(specifications="500毫升；材质未知"),
        "商品事实或规格",
    )


@pytest.mark.parametrize(
    "specifications",
    [
        "不锈钢材质；容量500毫升",
        "无香精配方；净含量100毫升",
        "不含糖；净含量500克",
        "不支持蓝牙；续航8小时",
        "304不锈钢；容量500毫升；外观很棒",
        "304不锈钢；容量500毫升；颜色未知",
    ],
)
def test_real_negative_attributes_and_known_facts_are_accepted(specifications):
    assessment = assess_product_input(_brief(specifications=specifications))

    assert assessment["ready"] is True, assessment
    assert assessment["status"] == "ready"
    assert assessment["missing"] == []


@pytest.mark.parametrize("target_audience", ["摄影师", "维修技师"])
def test_non_catalog_professional_audiences_are_accepted(target_audience):
    assessment = assess_product_input(_brief(target_audience=target_audience))

    assert assessment["ready"] is True, assessment
    assert assessment["missing"] == []


def test_factual_selling_points_can_supply_evidence_without_specifications():
    assessment = assess_product_input(
        _brief(
            specifications=None,
            selling_points="采用304不锈钢；容量500毫升",
        )
    )

    assert assessment["ready"] is True, assessment
    assert assessment["missing"] == []


def test_known_facts_and_unknown_adjacent_sentence_are_accepted():
    assessment = assess_product_input(
        _brief(
            specifications=None,
            description=(
                "这款保温水杯采用304不锈钢。容量500毫升。颜色未知。"
                "适合上班族日常通勤使用。"
            ),
        )
    )

    assert assessment["ready"] is True, assessment
    assert assessment["missing"] == []


@pytest.mark.parametrize(
    "specifications",
    [
        ["材质为304不锈钢", "容量为500毫升"],
        {"材质": "304不锈钢", "容量": "500毫升"},
        {"面料": "莱赛尔", "颜色": "靛青"},
    ],
)
def test_list_and_dict_structured_facts_preserve_known_key_value_semantics(specifications):
    assessment = assess_product_input(_brief(specifications=specifications))

    assert assessment["ready"] is True, assessment
    assert assessment["missing"] == []


@pytest.mark.parametrize(
    "specifications",
    [
        ["材质未知", "容量待确认"],
        {"材质": "未知", "容量": "待确认"},
    ],
)
def test_list_and_dict_all_unknown_facts_remain_insufficient(specifications):
    _assert_needs_input(
        _brief(specifications=specifications),
        "商品事实或规格",
    )
