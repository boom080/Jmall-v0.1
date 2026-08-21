"""Style adaptation agent for e-commerce platform-specific copy adaptation."""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.agents.copywriter import build_structured_detail

logger = logging.getLogger(__name__)

# Platform style profiles
STYLE_PROFILES = {
    "pinduoduo": {
        "name": "拼多多",
        "characteristics": [
            "价格导向突出，强调性价比",
            "制造紧迫感，使用限时/限量/抢购等用语",
            "口语化表达，接地气",
            "突出拼团优惠和社交裂变",
            "多用感叹号和emoji增强感染力",
        ],
        "title_style": "简短有力，突出价格和数量优势",
        "selling_point_style": "直击痛点，数字量化，紧迫感强",
        "detail_style": "图多文少，重点突出，价格和优惠信息前置",
        "color_scheme": "warm-red",
        "layout": "promotion-driven",
        "font_style": "bold-emphasis",
    },
    "taobao": {
        "name": "淘宝",
        "characteristics": [
            "丰富多元，覆盖多种风格",
            "突出商品卖点和差异化",
            "SEO友好，关键词密度适中",
            "注重用户评价和信任感建设",
            "风格灵活，可根据品类调整",
        ],
        "title_style": "信息完整，包含品牌+品类+核心卖点+场景",
        "selling_point_style": "突出差异化，对比竞品优势",
        "detail_style": "结构清晰，图文并茂，分层展示卖点",
        "color_scheme": "orange-warm",
        "layout": "content-rich",
        "font_style": "clean-modern",
    },
    "jd": {
        "name": "京东",
        "characteristics": [
            "品质导向，强调正品保障和京东自营",
            "参数详细，规格清晰",
            "专业规范，用词严谨",
            "强调物流速度和售后服务",
            "突出品牌授权和资质认证",
        ],
        "title_style": "规范完整，品牌+型号+规格参数+核心卖点",
        "selling_point_style": "参数化表达，数据支撑，权威感强",
        "detail_style": "规格参数表+图文详情，信息密度高",
        "color_scheme": "red-professional",
        "layout": "spec-driven",
        "font_style": "clean-standard",
    },
    "suning": {
        "name": "苏宁",
        "characteristics": [
            "家电3C风格突出",
            "强调售后服务和完善保障",
            "品牌信任感和正品保障",
            "注重以旧换新、延保等服务",
            "线上线下融合体验",
        ],
        "title_style": "品牌+型号+规格+服务亮点",
        "selling_point_style": "服务保障+产品优势并重",
        "detail_style": "规格+场景+服务保障三段式",
        "color_scheme": "blue-trust",
        "layout": "service-emphasis",
        "font_style": "professional-clean",
    },
    "xiaohongshu": {
        "name": "小红书",
        "characteristics": [
            "种草风格，生活方式化表达",
            "基于商品事实的场景化推荐，不伪造第一人称体验",
            "年轻化语言，网络热词适度使用",
            "突出使用场景和情感共鸣",
            "视觉驱动，搭配风格化描述",
        ],
        "title_style": "吸引眼球，带有情感和场景感",
        "selling_point_style": "体验式描述，而非参数罗列",
        "detail_style": "故事化叙述，从使用场景切入",
        "color_scheme": "pink-warm",
        "layout": "lifestyle-driven",
        "font_style": "casual-elegant",
    },
}


class StyleAdapterAgent(BaseAgent):
    """Style adaptation agent for e-commerce platform-specific copy.

    Adapts generated copy to match the tone and style of different platforms:
    - Pinduoduo: Price-focused, urgency-driven
    - Taobao: SEO-friendly, comprehensive
    - JD: Quality-focused, specification-heavy
    - Suning: Service-oriented, trust-building
    - Xiaohongshu: Lifestyle-driven, authentic

    Uses the medium model tier.
    """

    agent_type = "style_adaptation"
    model_preference = "medium"

    SYSTEM_PROMPT = (
        "你是电商视觉和文案风格专家。根据指定目标平台，生成一份差异化文案预览。\n\n"
        "你了解以下平台的文案风格特点：\n"
        "- 拼多多：价格导向、紧迫感强、口语化、强调拼团\n"
        "- 淘宝：信息丰富、SEO优化、突出卖点、风格灵活\n"
        "- 京东：品质导向、参数详细、专业规范、强调服务\n"
        "- 苏宁：家电风格、售后服务、品牌信任、正品保障\n"
        "- 小红书：种草风格、生活方式化、场景化推荐、年轻化\n\n"
        "你的职责：\n"
        "1. 按指定目标平台重写标题、3到5条卖点和350至900字的完整分段详情文案\n"
        "2. 给出视觉参数建议（配色、布局、字体风格）\n"
        "事实约束：\n"
        "- 只能改写原文已有事实，不得新增配料、功效、适用人群、销量、优惠、认证或体验\n"
        "- 不得伪造第一人称亲身体验、亲友评价、购买或囤货经历\n"
        "- 信息不足时保留原文，或写明请商家确认\n\n"
        "输出要求：\n"
        "请只输出 JSON，不要输出 Markdown。JSON 格式：\n"
        '{"adapted_title": "...", "adapted_selling_points": ["..."], '
        '"adapted_detail": "...", "visual_params": {}, "style_notes": "..."}'
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.system_prompt = self.SYSTEM_PROMPT

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt copy to the target platform style.

        Args:
            state: Orchestration state with copy_drafts, target_style

        Returns:
            State update with style_previews
        """
        copy_drafts = state.get("copy_drafts", {})
        target_style = state.get("target_style", "taobao")
        product_info = state.get("product_info", {})
        product_info = {
            **product_info,
            "market_research": state.get("market_research") or {},
        }

        title = product_info.get("title", "")
        category = product_info.get("category", "未分类")

        profile = STYLE_PROFILES.get(target_style, STYLE_PROFILES["taobao"])
        logger.info(
            "StyleAdapterAgent: adapting copy to '%s' (%s) style",
            target_style, profile["name"],
        )

        # Build prompt with current copy and target style profile
        prompt = self._build_prompt(
            copy_drafts=copy_drafts,
            target_style=target_style,
            profile=profile,
            title=title,
            category=category,
        )

        fallback_error = ""
        try:
            # Generate the merchant-selected style with the model.  Asking a
            # single response to contain five full detail pages regularly hit
            # provider read timeouts.  The remaining four previews are built
            # deterministically below from the same guarded copy.
            llm_result = self._call_llm(prompt, temperature=0.7, max_tokens=1536)
            parsed = self._parse_json_response(llm_result)
        except Exception as exc:
            logger.warning("StyleAdapterAgent LLM call failed, using original copy: %s", exc)
            fallback_error = str(exc)
            parsed = {}

        parsed_previews = parsed.get("previews", {}) if isinstance(parsed, dict) else {}
        # Backward compatibility with providers that still emit the original
        # single-style response shape.
        if not isinstance(parsed_previews, dict):
            parsed_previews = {}
        if isinstance(parsed, dict) and (
            parsed.get("adapted_title")
            or parsed.get("adapted_selling_points")
            or parsed.get("adapted_detail")
        ):
            parsed_previews[target_style] = parsed

        previews: Dict[str, Dict[str, Any]] = {}
        for style_id, style_profile in STYLE_PROFILES.items():
            candidate = parsed_previews.get(style_id, {})
            if not isinstance(candidate, dict) or not candidate:
                candidate = self._build_safe_style_preview(style_id, copy_drafts, title)
            previews[style_id] = self._guard_style_preview(
                candidate=candidate,
                copy_drafts=copy_drafts,
                product_info=product_info,
                style_id=style_id,
                profile=style_profile,
            )

        selected = previews[target_style]

        style_result = {
            "target_style": target_style,
            "style_name": profile["name"],
            "adapted_title": selected["adapted_title"],
            "adapted_selling_points": selected["adapted_selling_points"],
            "adapted_detail": selected["adapted_detail"],
            "visual_params": selected["visual_params"],
            "style_notes": selected["style_notes"],
            "previews": previews,
            "style_characteristics": profile.get("characteristics", []),
            "fallback": bool(fallback_error),
            "error": fallback_error,
        }

        logger.info("StyleAdapterAgent: adaptation complete for %s", profile["name"])

        return self._make_state_update("style_previews", style_result)

    @staticmethod
    def _build_safe_style_preview(
        style_id: str,
        copy_drafts: Dict[str, Any],
        title: str,
    ) -> Dict[str, Any]:
        """Produce a visibly distinct, fact-preserving preview if a model omits one."""
        base_title = (copy_drafts.get("titles") or [title or "商品"])[0]
        points = list(copy_drafts.get("selling_points") or [])
        detail = str(copy_drafts.get("detail_copy") or "")
        templates = {
            "pinduoduo": (f"好物直达｜{base_title}", [f"好懂：{p}" for p in points], "重点先看："),
            "taobao": (f"{base_title}｜信息清晰 好搜好选", [f"商品亮点：{p}" for p in points], "商品详情\n"),
            "jd": (f"{base_title}｜规格信息以详情为准", [f"信息要点：{p}" for p in points], "商品信息\n"),
            "suning": (f"{base_title}｜商品与服务信息详见页面", [f"选购要点：{p}" for p in points], "选购说明\n"),
            "xiaohongshu": (f"今日穿搭灵感｜{base_title}", [f"✨ {p}" for p in points], "风格灵感\n"),
        }
        adapted_title, adapted_points, detail_prefix = templates.get(style_id, templates["taobao"])
        return {
            "adapted_title": adapted_title,
            "adapted_selling_points": adapted_points or points,
            "adapted_detail": f"{detail_prefix}{detail}".strip(),
            "visual_params": {},
            "style_notes": "模型未返回该平台版本，已生成事实安全的差异化预览。",
        }

    @staticmethod
    def _guard_style_preview(
        candidate: Dict[str, Any],
        copy_drafts: Dict[str, Any],
        product_info: Dict[str, Any],
        style_id: str,
        profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Reject unsupported factual claims while preserving stylistic wording."""
        base_title = (copy_drafts.get("titles") or [product_info.get("title", "商品")])[0]
        base_points = list(copy_drafts.get("selling_points") or [])
        base_detail = str(copy_drafts.get("detail_copy") or product_info.get("description", ""))
        evidence = " ".join([
            str(product_info.get("title", "")),
            str(product_info.get("category", "")),
            str(product_info.get("description", "")),
            str(product_info.get("specifications", "")),
            str(product_info.get("target_audience", "")),
            str(product_info.get("usage_scenarios", "")),
            base_title,
            " ".join(base_points),
            base_detail,
        ])
        unsupported = re.compile(
            r"(?:第一|最好|顶级|唯一|100%|永不|销量|冠军|官方授权|正品保证|"
            r"无添加|人工色素|反式脂肪|儿童|宝宝|孕妇|亲测|已囤|我家|闺蜜|"
            r"朋友|上周|昨天|今天穿|我穿|让我|穿上它|洗过|陌生人|问链接|追着问|要了?链接|不起球|不褪色|"
            r"洗后|柔软|软糯|纯棉|厚度|锁骨|显白|不挑肤色|舒适|不勒|不卡|不滑落|秋冬必备|"
            r"完美适应|完美适配|脱颖而出|衣橱.{0,8}新宠|京东自营|次日达|七天无理由|保修\d+年)",
            flags=re.IGNORECASE,
        )
        evidence_compact = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", evidence.lower())

        def has_grounding(value: str) -> bool:
            if re.search(r"请.*(?:确认|补充)|待确认|以.*为准", value):
                return True
            compact = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value.lower())
            latin_tokens = re.findall(r"[a-z0-9]{2,}", compact)
            if any(token in evidence_compact for token in latin_tokens):
                return True
            cjk = "".join(re.findall(r"[\u4e00-\u9fff]", compact))
            return any(cjk[i:i + 2] in evidence_compact for i in range(max(0, len(cjk) - 1)))

        def safe(text: Any, fallback: str) -> str:
            value = str(text or "").strip()
            if not value:
                return fallback
            if not has_grounding(value):
                return fallback
            for match in unsupported.finditer(value):
                if match.group(0).lower() not in evidence.lower():
                    return fallback
            # New numeric claims are particularly risky; allow only numbers
            # already present in merchant/reviewed copy.
            evidence_numbers = set(re.findall(r"\d+(?:\.\d+)?", evidence))
            if any(number not in evidence_numbers for number in re.findall(r"\d+(?:\.\d+)?", value)):
                return fallback
            return value

        # Research conclusions are useful evidence in the market panel, but
        # they are not facts about this merchant SKU and must not enter a
        # publishable style preview unless the merchant supplied them.
        market_research = product_info.get("market_research") or {}
        research_only_phrases = {
            str(keyword).strip().lower()
            for keyword in (market_research.get("hot_keywords", []) or [])
            if len(str(keyword).strip()) >= 2
            and str(keyword).strip().lower() not in evidence.lower()
        }
        research_marker = re.compile(
            r"(?:20\d{2}年|今年|马年|本命年|爆款|热销|热度|时尚宠儿|销售旺季)",
            flags=re.IGNORECASE,
        )

        def contains_research_only(value: str) -> bool:
            return bool(research_marker.search(value)) or any(
                phrase in value.lower() for phrase in research_only_phrases
            )

        fallback = StyleAdapterAgent._build_safe_style_preview(style_id, copy_drafts, base_title)
        raw_title = str(candidate.get("adapted_title") or "")
        title = fallback["adapted_title"] if contains_research_only(raw_title) else safe(raw_title, fallback["adapted_title"])
        raw_points = candidate.get("adapted_selling_points", [])
        points: List[str] = []
        if isinstance(raw_points, list):
            for index, item in enumerate(raw_points[:5]):
                point_fallbacks = fallback.get("adapted_selling_points") or base_points
                point_fallback = point_fallbacks[min(index, len(point_fallbacks) - 1)] if point_fallbacks else "商品信息以详情为准"
                raw_item = str(item or "")
                value = point_fallback if contains_research_only(raw_item) else safe(raw_item, point_fallback)
                if value and value not in points:
                    points.append(value)
        if not points:
            points = fallback.get("adapted_selling_points") or base_points
        raw_detail = str(candidate.get("adapted_detail") or "")
        detail = fallback["adapted_detail"] if contains_research_only(raw_detail) else safe(raw_detail, fallback["adapted_detail"])
        detail = build_structured_detail(
            base_detail=detail,
            title=title,
            category=str(product_info.get("category", "商品")),
            selling_points=points,
            specifications=list(copy_drafts.get("specifications") or []),
            target_audience=str(copy_drafts.get("target_audience") or ""),
            usage_scenarios=list(copy_drafts.get("usage_scenarios") or []),
            pending_confirmations=list(copy_drafts.get("pending_confirmations") or []),
        )
        visual_params = candidate.get("visual_params", {})
        if not isinstance(visual_params, dict):
            visual_params = {}
        visual_params.setdefault("color_scheme", profile.get("color_scheme", "default"))
        visual_params.setdefault("layout", profile.get("layout", "standard"))
        visual_params.setdefault("font_style", profile.get("font_style", "standard"))
        visual_params.setdefault("image_style", "产品实拍+场景图+细节图")
        return {
            "target_style": style_id,
            "style_name": profile["name"],
            "adapted_title": title,
            "adapted_selling_points": points,
            "adapted_detail": detail,
            "visual_params": visual_params,
            "style_notes": str(candidate.get("style_notes") or f"已适配{profile['name']}平台风格"),
        }

    def _build_prompt(
        self,
        copy_drafts: dict,
        target_style: str,
        profile: dict,
        title: str,
        category: str,
    ) -> str:
        """Build the style adaptation prompt."""
        parts = [
            "【目标平台风格适配任务】",
            f"目标风格：{profile['name']}（{target_style}）",
            f"标题要求：{profile.get('title_style', '')}",
            f"卖点要求：{profile.get('selling_point_style', '')}",
            f"详情要求：{profile.get('detail_style', '')}",
        ]

        parts.append(f"\n原始商品：{title}（{category}）")

        if copy_drafts:
            parts.append(f"\n原标题：{' | '.join(copy_drafts.get('titles', []))}")
            parts.append(f"原卖点：{'；'.join(copy_drafts.get('selling_points', []))}")
            detail = copy_drafts.get("detail_copy", "")
            if detail:
                parts.append(f"原详情文案：\n{detail[:1800]}")

        parts.append("\n请仅生成目标平台版本，并按指定 JSON 输出；完整保留原详情中的所有事实区块。")
        return "\n".join(parts)

    @staticmethod
    def get_available_styles() -> Dict[str, Dict[str, Any]]:
        """Return all available style profiles with descriptions."""
        return {
            key: {
                "name": profile["name"],
                "description": profile.get("characteristics", [""])[0] if profile.get("characteristics") else "",
                "title_style": profile.get("title_style", ""),
                "color_scheme": profile.get("color_scheme", ""),
            }
            for key, profile in STYLE_PROFILES.items()
        }
