"""Execute exactly one versioned listing skill against merchant-supplied facts."""

import json
import logging
import re
from typing import Any, Dict, Iterable

from app.agents.base import BaseAgent
from app.platform_skills.registry import PLATFORM_SKILLS, ProductDraft, get_platform_skill

logger = logging.getLogger(__name__)
STYLE_PROFILES = {key: skill.model_dump() for key, skill in PLATFORM_SKILLS.items()}
_UNKNOWN = re.compile(r"待确认|待补充|请.*(?:确认|补充|核实)|未提供|未填写|以.*为准")
_ALWAYS_BLOCK = re.compile(
    r"全网最低|最好|顶级|唯一|冠军|第一|100%|永不|亲测|已囤|我家|闺蜜|"
    r"我穿|让我|洗过|追着问|问链接|要了?链接|陌生人|上周|昨天|今天穿|"
    r"加微信|私信下单|站外交易|完美适配|完美适应"
)
_CLAIMS = re.compile(
    r"销量|官方授权|正品保[证障]|京东自营|次日达|七天无理由|保修|联保|延保|"
    r"免费安装|送装一体|以旧换新|百亿补贴|限时|限量|抢购|拼团|折扣|赠品|"
    r"无添加|人工色素|反式脂肪|儿童|宝宝|孕妇|不起球|不褪色|柔软|软糯|"
    r"纯棉|真皮|不锈钢|抗菌|防水|减肥|美白|治疗|舒适|不勒|不卡|不滑落|"
    r"显白|不挑肤色|锁骨|厚度|秋冬必备|衣橱.{0,8}新宠|脱颖而出|"
    r"挺括|耐磨|抗皱|透气|防盗|承重|防刮|耐用|保温|防漏|保障.{0,8}安全|"
    r"20\d{2}年|今年|马年|本命年|爆款|热销|热度|时尚宠儿|销售旺季"
)
_SENSITIVE_AUDIENCE = re.compile(
    r"儿童|孩子|小朋友|宝宝|婴幼儿|未成年人|孕妇|产妇|哺乳|老人|老年|患者|病人|"
    r"糖尿病|高血压|癌症|抑郁|焦虑|残障|残疾|\d+岁"
)
_SEARCH_INTENT_ONLY = re.compile(r"(?:推荐|选购|怎么选|价格|多少钱|对比|指南|适用|使用|场景|人群|日常)*")


def _fragments(value: Any) -> list[str]:
    if not isinstance(value, str):
        return []
    return [part.strip() for part in re.split(r"[\n；;。]+", value) if part.strip()]


def _unique_text(values: Iterable[Any], *, limit: int) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = re.sub(r"\s+", " ", str(value or "")).strip(" ,，;；。|｜")
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            result.append(text)
        if len(result) >= limit:
            break
    return result


class StyleAdapterAgent(BaseAgent):
    agent_type = "style_adaptation"
    model_preference = "medium"
    SYSTEM_PROMPT = "仅执行已注册的平台商品 Skill，不能生成其他平台内容。"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.system_prompt = self.SYSTEM_PROMPT

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Resolve before any provider call, even for direct/internal invocations.
        skill = get_platform_skill(state.get("target_style", "taobao"))
        product = state.get("product_info") or {}
        fallback = self._merchant_draft(product, skill)
        market_research = state.get("market_research") or {}
        research_sources = self._research_sources(market_research)
        verified_research = bool(research_sources) and market_research.get("status") != "failed"
        pending = list(fallback.pending_confirmations)
        for item in (state.get("copy_drafts") or {}).get("pending_confirmations", []):
            if isinstance(item, str) and item not in pending:
                pending.append(item)

        error = ""
        try:
            reference = state.get("copy_drafts") or {}
            marketing_research = {
                "hot_keywords": (market_research.get("hot_keywords") or [])[:12],
                "audience_segments": (market_research.get("audience_segments") or [])[:5],
                "sources": research_sources,
            } if verified_research else {}
            result = self._call_llm(
                json.dumps({
                    "merchant_facts": product,
                    "writing_preference": state.get("user_request") or "",
                    # Upstream extraction helps organization, but is explicitly
                    # not factual evidence and is never trusted by the guard.
                    "reference_outline": {key: reference.get(key) for key in (
                        "selling_points", "specifications", "target_audience", "usage_scenarios",
                        "subtitle", "seo_keywords",
                    )},
                    "marketing_research": marketing_research,
                }, ensure_ascii=False),
                temperature=0.4, max_tokens=2500,
                system_prompt=skill.system_prompt(),
            )
            candidate = self._parse_json_response(result)
            # Migration boundary for existing single-preview provider responses.
            if isinstance(candidate, dict) and "adapted_title" in candidate:
                candidate = {
                    "titles": [candidate.get("adapted_title")],
                    "selling_points": candidate.get("adapted_selling_points"),
                    "detail_copy": candidate.get("adapted_detail"),
                }
            draft = ProductDraft.model_validate(candidate)
        except Exception:
            logger.warning("Platform skill %s provider/schema failure", skill.skill_id, exc_info=True)
            # Raw provider errors may contain secrets or URLs.
            error = "平台模型输出不可用，已按商家事实生成保守草稿，请人工检查。"
            draft = fallback.model_copy(deep=True)
            pending.append(error)

        evidence = " ".join(str(product.get(field) or "") for field in (
            "title", "category", "description", "price", "specifications", "target_audience", "usage_scenarios"
        ))
        research_only = [str(word) for word in market_research.get("hot_keywords", [])
                         if str(word) not in evidence]
        guarded = False
        generated_candidates = {
            "target_audience": draft.target_audience,
            "seo_keywords": list(draft.seo_keywords),
        }

        def safe(value: str, default: str, field: str) -> str:
            nonlocal guarded
            compact = re.sub(r"\W", "", value.lower())
            known = re.sub(r"\W", "", evidence.lower())
            grounded = any(compact[i:i + 2] in known for i in range(len(compact) - 1))
            numbers_known = set(re.findall(r"\d+(?:\.\d+)?", evidence))
            invalid = (not value.strip() or not grounded or _UNKNOWN.search(value)
                       or _ALWAYS_BLOCK.search(value)
                       or any(match.group() not in evidence for match in _CLAIMS.finditer(value))
                       or any(number not in numbers_known for number in re.findall(r"\d+(?:\.\d+)?", value))
                       or any(word and word in value for word in research_only))
            if invalid:
                guarded = True
                pending.append(f"{field}中有缺失或未经确认的表达，已替换为商家事实，请核对。")
                return default
            return value.strip()

        raw_title = safe(draft.titles[0], fallback.titles[0], "标题")
        if len(raw_title) > skill.title_max_length:
            pending.append("标题已按平台编辑预算缩短，请核对完整性。")
        draft.titles = [raw_title[:skill.title_max_length]]
        draft.selling_points = list(dict.fromkeys(
            safe(point, fallback.selling_points[min(i, len(fallback.selling_points) - 1)], "卖点")
            for i, point in enumerate(draft.selling_points)
        )) if draft.selling_points and fallback.selling_points else fallback.selling_points
        draft.detail_copy = safe(draft.detail_copy, fallback.detail_copy, "详情")
        # Preserve filled form fields; extraction from a long description is
        # also allowed when the model quotes actual merchant text verbatim.
        def extracted(values, report=True):
            accepted = [value for value in values if value.strip() and value in evidence
                        and not _UNKNOWN.search(value) and not _ALWAYS_BLOCK.search(value)]
            if report and len(accepted) != len(values):
                pending.append("部分结构化字段无法在商家原文中核对，已移除，请补充真实信息。")
            return list(dict.fromkeys(accepted))

        draft.specifications = fallback.specifications or extracted(draft.specifications)
        draft.target_audience = fallback.target_audience or "；".join(extracted([draft.target_audience]))
        draft.usage_scenarios = fallback.usage_scenarios or extracted(draft.usage_scenarios)
        draft.seo_keywords = list(fallback.seo_keywords)
        draft.subtitle = safe(draft.subtitle, fallback.subtitle, "副标题") if draft.subtitle else fallback.subtitle
        draft.promotion_copy = safe(draft.promotion_copy, "", "推广语") if draft.promotion_copy else ""
        draft.short_video_script = safe(draft.short_video_script, "", "视频文案") if draft.short_video_script else ""

        marketing_metadata = self._apply_marketing_enrichment(
            draft=draft,
            fallback=fallback,
            product=product,
            skill=skill,
            generated_candidates=generated_candidates,
            market_research=market_research,
            research_sources=research_sources,
        )
        for label, value in (("商品规格", draft.specifications), ("目标人群或使用场景", draft.target_audience or draft.usage_scenarios)):
            if not value:
                pending.append(f"请核对并补充{label}（如原始描述已包含，可确认后保留）。")
        draft.pending_confirmations = list(dict.fromkeys([*pending, *draft.pending_confirmations]))[:20]

        selected = {
            "target_style": skill.platform, "style_name": skill.name,
            "platform_skill_id": skill.skill_id, "platform_skill_version": skill.version,
            "adapted_title": draft.titles[0], "adapted_selling_points": draft.selling_points,
            "adapted_detail": draft.detail_copy,
            "visual_params": {key: getattr(skill, key) for key in ("color_scheme", "layout", "font_style")},
            "style_notes": f"{skill.name}：{skill.tone}",
        }
        return self._make_state_update("style_previews", {
            **selected, "draft": draft.model_dump(),
            # Legacy envelope contains only the selected platform.
            "previews": {skill.platform: dict(selected)},
            "pending_confirmations": draft.pending_confirmations,
            "style_characteristics": skill.characteristics,
            "marketing_enrichment": marketing_metadata,
            "fallback": bool(error), "guarded": guarded, "error": error,
        })

    @staticmethod
    def _research_sources(market_research: Dict[str, Any]) -> list[dict[str, str]]:
        sources: list[dict[str, str]] = []
        seen: set[str] = set()
        for source in market_research.get("sources") or []:
            if not isinstance(source, dict):
                continue
            url = str(source.get("url") or "").strip()
            if not url.startswith(("https://", "http://")) or url in seen:
                continue
            seen.add(url)
            sources.append({"title": str(source.get("title") or url), "url": url})
            if len(sources) >= 5:
                break
        return sources

    @staticmethod
    def _marketing_value_is_safe(value: Any, evidence: str, *, audience: bool = False) -> bool:
        if not isinstance(value, str):
            return False
        text = re.sub(r"\s+", " ", str(value or "")).strip()
        if not 2 <= len(text) <= 48:
            return False
        if _UNKNOWN.search(text) or _ALWAYS_BLOCK.search(text):
            return False
        if audience and _SENSITIVE_AUDIENCE.search(text) and text not in evidence:
            return False
        if any(match.group() not in evidence for match in _CLAIMS.finditer(text)):
            return False
        known_numbers = set(re.findall(r"\d+(?:\.\d+)?", evidence))
        return all(number in known_numbers for number in re.findall(r"\d+(?:\.\d+)?", text))

    @classmethod
    def _research_keyword_is_safe(
        cls,
        value: Any,
        evidence: str,
        known_terms: Iterable[Any],
    ) -> bool:
        """Allow sourced search intent, never an unconfirmed product attribute."""

        if not cls._marketing_value_is_safe(value, evidence):
            return False
        remainder = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", str(value).lower())
        compact_terms = sorted({
            re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", str(term).lower())
            for term in known_terms if len(str(term).strip()) >= 2
        }, key=len, reverse=True)
        matched = False
        for term in compact_terms:
            if term and term in remainder:
                remainder = remainder.replace(term, "")
                matched = True
        evidence_compact = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", evidence.lower())
        return matched and (
            not remainder
            or remainder in evidence_compact
            or bool(_SEARCH_INTENT_ONLY.fullmatch(remainder))
        )

    @classmethod
    def _apply_marketing_enrichment(
        cls,
        *,
        draft: ProductDraft,
        fallback: ProductDraft,
        product: Dict[str, Any],
        skill,
        generated_candidates: Dict[str, Any],
        market_research: Dict[str, Any],
        research_sources: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Enrich marketing fields while keeping every product fact merchant-grounded."""

        evidence = " ".join(str(product.get(field) or "") for field in (
            "title", "category", "description", "price", "specifications",
            "target_audience", "usage_scenarios",
        ))
        research_verified = bool(research_sources) and market_research.get("status") != "failed"

        # This may originate from a filled form field or a verbatim extraction
        # from the merchant's long description; both were grounded above.
        merchant_audiences = _fragments(draft.target_audience)
        audience_candidates: list[Any] = []
        if research_verified:
            audience_candidates.extend(market_research.get("audience_segments") or [])
            generated_audience = generated_candidates.get("target_audience")
            research_text = " ".join(str(value) for value in audience_candidates)
            if generated_audience and str(generated_audience) in research_text:
                audience_candidates.append(generated_audience)
        safe_audiences = [
            value for value in audience_candidates
            if cls._marketing_value_is_safe(value, evidence, audience=True)
        ]
        audiences = _unique_text([*merchant_audiences, *safe_audiences], limit=3)
        draft.target_audience = "；".join(audiences)

        title = str(product.get("title") or fallback.titles[0]).strip()
        category = str(product.get("category") or "").strip()
        descriptions = _fragments(str(product.get("description") or ""))
        specs = _fragments(str(product.get("specifications") or ""))
        scenes = _fragments(str(product.get("usage_scenarios") or ""))
        fact_terms = _unique_text(
            [title, category, *specs, *merchant_audiences, *scenes, *descriptions],
            limit=10,
        )

        if skill.platform in {"jd", "suning"}:
            preferred = [*specs, category, *scenes, *merchant_audiences, *descriptions]
        elif skill.platform == "xiaohongshu":
            preferred = [*scenes, *merchant_audiences, category, *descriptions, *specs]
        else:
            preferred = [category, *specs, *scenes, *merchant_audiences, *descriptions]

        research_keywords = []
        if research_verified:
            research_keywords = [
                value for value in (market_research.get("hot_keywords") or [])
                if cls._research_keyword_is_safe(
                    value,
                    evidence,
                    [*fact_terms, *safe_audiences],
                )
            ]

        combinations: list[str] = []
        for value in _unique_text(preferred, limit=8):
            if value != title:
                combinations.append(f"{title} {value}")
        for left, right in zip(fact_terms, fact_terms[1:]):
            if left != right:
                combinations.append(f"{left} {right}")
        if len(combinations) < 8:
            for value in fact_terms[1:]:
                combinations.append(f"{value} {title}")

        merchant_seo = product.get("seo_keywords") or []
        if isinstance(merchant_seo, str):
            merchant_seo = re.split(r"[,，\n]", merchant_seo)
        safe_merchant_seo = [
            value for value in merchant_seo
            if cls._marketing_value_is_safe(value, evidence)
        ]
        safe_generated_seo = [
            value for value in generated_candidates.get("seo_keywords") or []
            if str(value) in evidence and cls._marketing_value_is_safe(value, evidence)
        ]
        draft.seo_keywords = _unique_text([
            *safe_merchant_seo,
            *safe_generated_seo,
            *research_keywords,
            *fact_terms,
            *combinations,
        ], limit=12)

        research_used = research_verified and bool(research_keywords or safe_audiences)
        return {
            "source": "market_research" if research_used else "confirmed_input",
            "source_urls": [source["url"] for source in research_sources],
            "research_used": research_used,
            "subtitle_generated": bool(draft.subtitle),
            "audience_expanded": len(audiences) > len(_unique_text(merchant_audiences, limit=3)),
            "seo_expanded": len(draft.seo_keywords) > len(_unique_text(safe_merchant_seo, limit=12)),
        }

    @staticmethod
    def _merchant_draft(product, skill) -> ProductDraft:
        """Fallback never reuses potentially hallucinated upstream AI copy."""
        pending = []

        def confirmed(value, field):
            parts = _fragments(value)
            accepted = [part for part in parts if not _UNKNOWN.search(part) and not _ALWAYS_BLOCK.search(part)]
            if len(accepted) != len(parts):
                pending.append(f"请确认{field}中的不确定或不适合发布的内容。")
            return accepted

        name = str(product.get("title") or "").strip()
        description = confirmed(product.get("description"), "商品描述")
        specs = confirmed(product.get("specifications"), "规格")
        audience = confirmed(product.get("target_audience"), "目标人群")
        scenes = confirmed(product.get("usage_scenarios"), "场景")
        title = name if name and not _UNKNOWN.search(name) and not _ALWAYS_BLOCK.search(name) else (description or ["商品"])[0]
        points = (specs + description if skill.platform in {"jd", "suning"} else description + specs)[:5]
        sections = ["；".join(description) or title, "；".join(specs), "；".join(audience + scenes)]
        detail = "\n\n".join(f"【{heading}】\n{content}" for heading, content in zip(skill.detail_sections, sections) if content)
        subtitle_parts = _unique_text([*description, *specs, *scenes], limit=2)
        if not subtitle_parts:
            subtitle_parts = _unique_text([str(product.get("category") or ""), title], limit=2)
        subtitle = "｜".join(subtitle_parts)[:160] or title[:160]
        return ProductDraft(
            titles=[title[:skill.title_max_length]], selling_points=points,
            detail_copy=detail, specifications=specs, target_audience="；".join(audience),
            usage_scenarios=scenes, subtitle=subtitle,
            seo_keywords=[title[:skill.title_max_length]],
            pending_confirmations=pending,
        )

    @classmethod
    def get_available_styles(cls):
        return {key: {
            "name": skill.name, "description": "、".join(skill.characteristics),
            "title_style": skill.title_style, "color_scheme": skill.color_scheme,
            "platform_skill_id": skill.skill_id, "platform_skill_version": skill.version,
        } for key, skill in PLATFORM_SKILLS.items()}
