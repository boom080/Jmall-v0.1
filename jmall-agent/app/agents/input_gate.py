"""Deterministic input sufficiency checks for product orchestration.

The input gate deliberately does not call an LLM.  It decides whether the
merchant has supplied enough grounded product information for the expensive
multi-agent pipeline to be useful.  It accepts either:

* a long-form description that contains grounded product facts and a target
  audience; or
* structured fields for specifications and target audience.  Usage scenarios
  improve the score but are intentionally optional.

The returned dictionary is intentionally API-friendly and stable for both the
preflight endpoint and the graph's ``input_assessment`` state field.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from app.agents.input_questions import build_input_questions


_EMPTY_VALUES = {
    "",
    "-",
    "--",
    "无",
    "暂无",
    "未知",
    "未填写",
    "未提供",
    "待补充",
    "待确认",
    "请补充",
    "n/a",
    "na",
    "none",
    "null",
    "商品",
    "产品",
    "测试",
    "测试商品",
    "测试产品",
    "测试内容",
    "其他商品",
    "随便",
    "不知道",
    "不清楚",
    "参数",
    "规格",
    "卖点",
    "特点",
    "好用",
}

# These rules identify *missing information*, not every negative word.  For
# example, 不锈钢 / 无香精 / 不支持蓝牙 are concrete merchant-supplied attributes.
# Apply them to individual clauses so an unknown colour does not invalidate
# already supplied material and capacity.
_UNAVAILABLE_INFORMATION = re.compile(
    r"不知道|不清楚|不了解|不确定|不明确|不晓得|说不准|未确定|未明确|没(?:有)?(?:确定|明确|想好)|未想好"
    r"|未知|不详|未定|待(?:补充|提供|确认|定|填写|核实)|未(?:填写|提供|确认|知晓)"
    r"|(?:没(?:有)?|缺少|缺乏|暂无|尚无|未有).{0,16}(?:信息|资料|参数|规格|材质|容量|尺寸|重量|型号|人群)"
    r"|(?:是否|是不是|有没有|能否)|[?？]"
    r"|\b(?:unknown|unspecified|not\s+(?:known|sure|provided)|tbd|n/?a)\b",
    re.IGNORECASE,
)

_SUBJECTIVE_WORDS = re.compile(
    r"非常|超级|特别|真的|十分|比较|很|太|好用|好看|漂亮|美观|不错|优秀|优质"
    r"|高端|高档|喜欢|满意|推荐|值得|强大|齐全|丰富|很多|完美|棒|赞|好|的|呢|了",
)

_CLAUSE_SEPARATOR = re.compile(r"[；;，,\n|。！!]+|但是|不过|而且|但")
_AUDIENCE_CLAUSE_START = re.compile(r"(?:适合|面向|针对|卖给|服务于)")

_PLACEHOLDER_PATTERN = re.compile(
    r"^(?:x+|a+|test\d*|demo\d*|asdf\w*|\d+)$",
    re.IGNORECASE,
)

_MEASUREMENT_PATTERN = re.compile(
    r"\d+(?:\.\d+)?\s*(?:ml|毫升|l|升|g|kg|克|千克|斤|mm|cm|m|毫米|厘米|米|w|v|瓦|伏|mah|毫安时|小时|分钟|天|个|件|片|支|包|%|元)",
    re.IGNORECASE,
)

_FACT_MARKERS = re.compile(
    r"材质|规格|型号|容量|重量|尺寸|功率|电压|续航|含量|成分|功能|采用|支持|设计|包含|颜色|口径|数量|配件|参数|口感|产地|保质期|版本|连接|温度|速度|尺码|版型|面料|接口|配方|兼容|内置|附带",
    re.IGNORECASE,
)

# Concise values commonly supplied without labels.  Other attributes remain
# open-ended through explicit labels (e.g. 面料: 莱赛尔) and feature predicates;
# this is not a closed list of permissible product categories.
_CONCRETE_FACT_VALUES = re.compile(
    r"不锈钢|纯棉|全棉|棉质|尼龙|帆布|硅胶|陶瓷|玻璃|实木|真皮|亚麻|羊毛|涤纶"
    r"|(?:黑|白|红|蓝|绿|黄|灰|紫|粉|棕|米白|透明)色"
    r"|原味|无糖|不含糖|无香精|无酒精|无添加|低噪音|静音|防水|防滑"
    r"|可拆洗|可折叠|可调节|一键清洗|自动清洗|自动加热|多功能料理"
    r"|(?:usb[- ]?[ac]?|hdmi|type[- ]?c|蓝牙|wifi|wi-fi)"
    r"|[a-z]+[- ]?\d+[a-z0-9-]*",
    re.IGNORECASE,
)

_NEGATED_AUDIENCE = re.compile(
    r"不(?:是|适合|适用|面向|针对|卖给|服务于)|非(?:目标|面向)|排除|不包括|除外|以外|并非"
)

_AUDIENCE_MARKERS = re.compile(
    r"(?:适合|面向|针对|服务于|为)[^，。；;\n]{0,24}(?:人群|用户|家庭|学生|儿童|宝宝|老人|孕妇|女性|男性|上班族|职场|新手|爱好者|消费者|人士|人使用|送礼)"
    r"|学生|儿童|宝宝|老人|孕妇|上班族|职场人士|新手|爱好者|家庭用户|女性用户|男性用户|消费者|宝妈|宝爸|猫咪|狗狗|宠物",
    re.IGNORECASE,
)

_SCENARIO_MARKERS = re.compile(
    r"使用场景|用于|用来|适用于|日常|通勤|出行|旅行|办公室|办公|居家|厨房|客厅|卧室|户外|露营|运动|健身|学习|工作|聚会|送礼|早餐|午餐|晚餐|烹饪|煎炒|烘焙|清洁|洗护|车载|宿舍|会议",
    re.IGNORECASE,
)


def _text(value: Any) -> str:
    """Normalize scalar/list/dict input into deterministic plain text."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "；".join(item for item in (_text(part) for part in value) if item)
    if isinstance(value, Mapping):
        return "；".join(
            f"{_text(key)}：{_text(part)}"
            for key, part in value.items()
            if _text(part)
        )
    # Remove invisible Unicode formatting characters so zero-width padding
    # cannot inflate an otherwise empty field.
    return re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]", "", str(value)).strip()


def _pick(product_info: Mapping[str, Any], *names: str) -> str:
    for name in names:
        if name in product_info:
            value = _text(product_info.get(name))
            if value:
                return value
    return ""


def _has_value(value: str) -> bool:
    normalized = re.sub(r"\s+", "", value).strip().lower()
    if not normalized or normalized in _EMPTY_VALUES:
        return False
    if _PLACEHOLDER_PATTERN.fullmatch(normalized):
        return False
    if len(normalized) >= 3 and len(set(normalized)) == 1:
        return False
    # Existing safe templates should not be treated as merchant evidence.
    if re.search(r"请(?:商家|根据|补充|确认|核实)|信息待完善|未确认|待商家确认", value):
        return False
    return True


def _compact_length(value: str) -> int:
    return len(re.findall(r"[0-9a-z\u4e00-\u9fff]", value.lower()))


def _normalized_fact(value: str) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value.lower())


def _has_text_diversity(value: str) -> bool:
    chars = re.findall(r"[0-9a-z\u4e00-\u9fff]", value.lower())
    if not chars:
        return False
    if len(chars) < 20:
        return True
    return len(set(chars)) / len(chars) >= 0.2


def _has_concrete_marker(value: str) -> bool:
    """Require an attribute value, not merely the word 'material' or 'design'."""
    if _MEASUREMENT_PATTERN.search(value) or _CONCRETE_FACT_VALUES.search(value):
        return True
    for marker in _FACT_MARKERS.finditer(value):
        detail = re.sub(r"^[\s:：是为]+", "", value[marker.end():])
        if not _has_value(detail):
            continue
        # '功能强大 / 设计优秀' carry no attribute value after removing praise.
        meaningful = _FACT_MARKERS.sub("", _SUBJECTIVE_WORDS.sub("", detail))
        if _compact_length(meaningful) >= 2 and _has_value(meaningful):
            return True
    return False


def _known_clauses(value: str) -> list[str]:
    return [
        part.strip()
        for part in _CLAUSE_SEPARATOR.split(value)
        if _has_value(part) and not _UNAVAILABLE_INFORMATION.search(part)
        and not _UNAVAILABLE_INFORMATION.search(re.sub(r"\s+", "", part))
    ]


def _grounded_facts(value: str) -> list[str]:
    facts = {}
    for part in _known_clauses(value):
        # Audience text and praise are not extra specifications.  In particular,
        # '功能很强大适合学生' must not manufacture an attribute value or length.
        evidence = _AUDIENCE_CLAUSE_START.split(part, maxsplit=1)[0]
        evidence = _SUBJECTIVE_WORDS.sub("", evidence)
        if (
            _has_value(evidence)
            and _compact_length(evidence) >= 2
            and _has_text_diversity(evidence)
            and _has_concrete_marker(evidence)
        ):
            facts[_normalized_fact(evidence)] = evidence
    return list(facts.values())


def _has_facts(description: str, specifications: str, selling_points: str) -> bool:
    facts = {
        _normalized_fact(fact): fact
        for value in (specifications, selling_points, description)
        for fact in _grounded_facts(value)
    }
    # Confirmed facts can be spread across fields.  Unknown or subjective
    # padding cannot turn one short fact into two facts or a detailed sentence.
    return len(facts) >= 2 or any(_compact_length(fact) >= 10 for fact in facts.values())


def _has_audience(explicit: str, description: str) -> bool:
    for part in _known_clauses(explicit):
        if not _NEGATED_AUDIENCE.search(re.sub(r"\s+", "", part)) and (
            _AUDIENCE_MARKERS.search(part)
            or (_compact_length(part) >= 3 and _has_text_diversity(part))
        ):
            return True
    return any(
        _AUDIENCE_MARKERS.search(part)
        and not _NEGATED_AUDIENCE.search(re.sub(r"\s+", "", part))
        for part in _known_clauses(description)
    )


def _has_scenario(explicit: str, description: str) -> bool:
    return (
        (_has_value(explicit) and _compact_length(explicit) >= 2)
        or bool(_SCENARIO_MARKERS.search(description))
    )


def assess_product_input(product_info: Mapping[str, Any] | None) -> dict[str, Any]:
    """Assess whether product information is sufficient for full orchestration.

    This function is pure and deterministic: the same product fields always
    produce the same score, missing fields, and questions.  The score is a
    transparent weighted checklist rather than an estimate from a model.
    """
    info = product_info or {}
    title = _pick(info, "title", "product_title", "productTitle")
    category = _pick(info, "category", "product_category", "productCategory")
    description = _pick(info, "description", "detail", "detail_copy", "detailCopy")
    specifications = _pick(info, "specifications", "specs", "specification")
    target_audience = _pick(info, "target_audience", "targetAudience", "audience")
    usage_scenarios = _pick(info, "usage_scenarios", "usageScenarios", "scenarios")
    selling_points = _pick(info, "selling_points", "sellingPoints", "highlights")

    has_title = _has_value(title) and _compact_length(title) >= 2
    has_category = (
        _has_value(category)
        and _compact_length(category) >= 2
        and category.strip() not in {"未分类", "未分类商品"}
    )
    has_facts = _has_facts(description, specifications, selling_points)
    has_audience = _has_audience(target_audience, description)
    has_scenario = _has_scenario(usage_scenarios, description)

    understood: list[str] = []
    if has_title:
        understood.append(f"商品名称：{title}")
    if has_category:
        understood.append(f"商品品类：{category}")
    if has_facts:
        understood.append("商品事实/规格：已提供")
    if has_audience:
        understood.append("目标人群：已提供或可从描述识别")
    if has_scenario:
        understood.append("使用场景：已提供或可从描述识别")

    missing: list[str] = []
    if not has_title:
        missing.append("商品名称")
    if not has_category:
        missing.append("商品品类")
    if not has_facts:
        missing.append("商品事实或规格")
    if not has_audience:
        missing.append("目标人群")
    # A usage scenario improves the generated result and contributes to the
    # score, but is not a hard blocker.  A merchant can still form a complete
    # brief by clearly stating what the product is, its grounded facts, and
    # who it is for.

    questions = build_input_questions(missing, category, title)

    # Transparent checklist weights: title 20, category 15, facts 30,
    # audience 20, scenario 15.  Full orchestration requires the first four;
    # scenario is optional supporting context, so a valid brief may score 85.
    score = (
        (20 if has_title else 0)
        + (15 if has_category else 0)
        + (30 if has_facts else 0)
        + (20 if has_audience else 0)
        + (15 if has_scenario else 0)
    )
    ready = not missing
    return {
        "status": "ready" if ready else "needs_input",
        "ready": ready,
        "score": score,
        "understood": understood,
        "missing": missing,
        "questions": questions[:3],
    }
