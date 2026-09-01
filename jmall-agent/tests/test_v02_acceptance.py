"""Small, explicit v0.2 input acceptance set; not a production accuracy claim."""

import pytest
from app.agents.input_gate import assess_product_input


CASES = [
    ("原味苏打饼干", "食品饮料", "原味；净含量200克", "办公室上班族"),
    ("白色棉衬衫", "服饰鞋包", "棉材质；白色；尺码M到XL", "通勤上班族"),
    ("轻量保温杯", "家居日用", "304不锈钢；容量500毫升", "上班族和学生"),
    ("USB扩展坞", "数码家电", "USB-C连接；3个USB-A接口", "笔记本办公用户"),
    ("无香精乳液", "美妆护肤", "净含量100毫升；无香精配方", "成年护肤用户"),
    ("徒步背包", "运动户外", "尼龙材质；容量20升", "徒步爱好者"),
]


@pytest.mark.parametrize("title,category,facts,audience", CASES)
@pytest.mark.parametrize("path", ["form", "paragraph"])
def test_valid_six_category_briefs_pass(title, category, facts, audience, path):
    info = {"title": title, "category": category}
    if path == "form":
        info.update(specifications=facts, target_audience=audience)
    else:
        info["description"] = f"我想卖{title}，商品规格是{facts}，主要面向{audience}这类人群。请只使用这些已知信息，不要编造其他卖点。"
    assert assess_product_input(info)["ready"] is True


@pytest.mark.parametrize("title,category,_,__", CASES)
def test_title_category_never_unlocks_full_generation(title, category, _, __):
    assert assess_product_input({"title": title, "category": category})["ready"] is False
