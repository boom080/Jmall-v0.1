"""Category-specific, model-free follow-up wording; never evidence or new gates."""

from types import MappingProxyType


# Suggestions are optional examples, not an instruction to fill every field.
CATEGORY_FACT_HINTS = MappingProxyType({
    "食品饮料": "净含量、成分或口味、包装数量、保质期（以实物标签为准）",
    "服饰鞋包": "材质、尺码或尺寸范围、版型或款式、颜色",
    "家居日用": "材质、尺寸或容量、结构、实际功能",
    "数码家电": "型号、关键参数（如功率或容量）、接口、兼容范围",
    "美妆护肤": "净含量、标签成分、产品类型、已确认的适用肤质（不填写未经证实的功效）",
    "运动户外": "材质、尺寸或重量、适用运动、使用环境或承重参数（仅填写已验证值）",
})

CATEGORY_AUDIENCE_HINTS = MappingProxyType({
    "食品饮料": "主要卖给谁食用或饮用？请写明目标人群；特殊人群适用性须有依据。",
    "服饰鞋包": "主要给谁穿、背或使用？请写明目标人群。",
    "家居日用": "这件家居用品主要给谁使用，例如通勤上班族或家庭用户？",
    "数码家电": "主要服务哪类用户，例如居家用户、办公人士或摄影爱好者？",
    "美妆护肤": "主要面向哪类用户？如知道适用肤质请说明，不确定的适用性不要猜测。",
    "运动户外": "主要面向哪类运动或户外用户，例如徒步爱好者或健身新手？",
})

_ALIASES = {
    "食品": "食品饮料", "饮料": "食品饮料", "生鲜水果": "食品饮料",
    "服饰": "服饰鞋包", "鞋包": "服饰鞋包", "服装": "服饰鞋包",
    "家居": "家居日用", "日用百货": "家居日用", "水具": "家居日用", "水具用品": "家居日用",
    "数码": "数码家电", "数码产品": "数码家电", "手机数码": "数码家电", "厨房电器": "数码家电",
    "美妆": "美妆护肤", "护肤": "美妆护肤",
    "运动": "运动户外", "户外": "运动户外",
}


def category_bucket(category: str) -> str:
    """Bounded category for templates/metrics; arbitrary merchant text stays out."""
    category = category.strip()
    if category in CATEGORY_FACT_HINTS:
        return category
    return _ALIASES.get(category, "其他")


def build_input_questions(missing: list[str], category: str, title: str) -> list[str]:
    bucket = category_bucket(category)
    hints = CATEGORY_FACT_HINTS.get(bucket, "材质、规格、容量、功能或具体特点")
    if bucket == "家居日用" and "保温杯" in title:
        hints = "容量、材质、杯盖结构、保温时长（仅填写已验证值）"
    questions = {
        "商品名称": "请在商品名称中写明要卖的具体商品。",
        "商品品类": "请在品类中选择商品所属类别。",
        "商品事实或规格": f"请在规格参数或商品说明中补充至少两项已知事实，例如{hints}。知道多少填多少，不必全部填写，也不要猜测。",
        "目标人群": CATEGORY_AUDIENCE_HINTS.get(bucket, "这件商品主要适合谁使用？请补充目标人群。"),
    }
    return [questions[field] for field in missing[:3]]
