"""Copy generation agent for e-commerce product copywriting."""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.retrieval.rag_retriever import assess_rag_quality
from app.retrieval.service import RetrievalService

logger = logging.getLogger(__name__)

# Supported e-commerce platform styles
SUPPORTED_STYLES = {
    "pinduoduo": {
        "name": "拼多多",
        "description": "价格导向、紧迫感强、口语化、强调拼团和低价",
        "tone": "marketing",
    },
    "taobao": {
        "name": "淘宝",
        "description": "丰富多元、突出卖点、SEO友好、适合搜索曝光",
        "tone": "professional",
    },
    "jd": {
        "name": "京东",
        "description": "品质导向、强调正品和物流、参数详细、专业规范",
        "tone": "professional",
    },
    "suning": {
        "name": "苏宁",
        "description": "家电风格、强调售后和服务、品牌信任感",
        "tone": "warm",
    },
    "xiaohongshu": {
        "name": "小红书",
        "description": "种草风格、生活方式化、真实体验分享、年轻化表达",
        "tone": "warm",
    },
}


def build_structured_detail(
    *,
    base_detail: str,
    title: str,
    category: str,
    selling_points: Optional[List[str]] = None,
    specifications: Optional[List[str]] = None,
    target_audience: str = "",
    usage_scenarios: Optional[List[str]] = None,
    pending_confirmations: Optional[List[str]] = None,
) -> str:
    """Build a substantial, publishable detail page from guarded facts.

    The market panel may contain useful research, but market observations are
    intentionally not copied here as SKU attributes.  This function expands
    only the already-guarded product copy and merchant-provided fields.
    """
    base = str(base_detail or "").strip()
    product_title = str(title or "商品").strip()
    product_category = str(category or "商品").strip()

    def unique(values: Optional[List[str]], limit: int) -> List[str]:
        result: List[str] = []
        for item in values or []:
            value = str(item or "").strip()
            if value and value not in result:
                result.append(value)
            if len(result) >= limit:
                break
        return result

    points = unique(selling_points, 5)
    specs = unique(specifications, 10)
    scenes = unique(usage_scenarios, 6)
    confirmations = unique(pending_confirmations, 4)
    sections: List[str] = []

    if "【商品概览】" not in base:
        overview = base or f"{product_title}属于{product_category}类商品，当前详情根据商家已提供信息整理。"
        sections.append(
            f"【商品概览】\n{overview}\n"
            "以下内容仅围绕商家已确认的商品事实整理，未确认信息会单独列入购买前核对项。"
        )
    else:
        sections.append(base)

    if "【核心亮点】" not in base:
        highlight_lines = points or ["商品核心特点请以商家已填写内容和页面实物图为准"]
        sections.append("【核心亮点】\n" + "\n".join(f"• {item}" for item in highlight_lines))

    if "【规格参数】" not in base:
        spec_lines = specs or ["尺码、颜色、材质、容量或型号等关键规格请商家补充并最终确认"]
        sections.append("【规格参数】\n" + "\n".join(f"• {item}" for item in spec_lines))

    if "【适用人群与场景】" not in base:
        audience = str(target_audience or "适用范围请结合商品真实属性由商家确认").strip()
        scene_text = "、".join(scenes) if scenes else "具体使用场景请根据商品真实用途补充"
        sections.append(f"【适用人群与场景】\n适用人群：{audience}\n使用场景：{scene_text}")

    if "【购买前核对】" not in base:
        standard_review_lines = [
            "下单前请核对商品规格、尺寸、颜色、数量及适用范围",
            "图片可能因拍摄光线与显示设备存在观感差异，请以实际商品为准",
            "未明确的材质、功效、认证、优惠、物流及售后信息不作额外承诺",
            "页面未展示或未由商家确认的属性，请勿根据同类商品信息自行推断",
        ]
        review_lines = unique(confirmations + standard_review_lines, 7)
        sections.append("【购买前核对】\n" + "\n".join(f"• {item}" for item in review_lines))

    return "\n\n".join(sections)[:5000].strip()


class CopywriterAgent(BaseAgent):
    """Copy generation agent for e-commerce product copywriting.

    Generates:
    - Product titles (3 versions)
    - Selling points (5)
    - Detail page copy
    - Short video script

    Supports 5 platform styles: pinduoduo, taobao, jd, suning, xiaohongshu
    Uses the strong model tier (GPT-4o/Qwen-Max).
    """

    agent_type = "copy_generation"
    model_preference = "strong"

    SYSTEM_PROMPT = (
        "你是资深电商文案。生成可直接回填商品编辑器的结构化商品资料。\n\n"
        "你的职责：\n"
        "1. 根据商品信息和目标平台风格，创作高质量电商文案\n"
        "2. 生成3个不同角度的商品标题\n"
        "3. 提炼5条核心卖点\n"
        "4. 撰写350至900字的详情页文案，至少包含商品概览、核心亮点、规格参数、适用人群与场景、购买前核对\n"
        "5. 提供短视频口播脚本（30秒版）\n"
        "6. 生成副标题、规格建议、目标人群、使用场景、SEO关键词和促销短文案\n"
        "7. 仅在有市场依据时给出价格建议，否则 price_suggestion 输出 null\n\n"
        "事实约束规则：\n"
        "- 商品输入中没有提供的信息，不要编造；市场趋势和RAG内容不能当成当前商品属性\n"
        "- 不得伪造第一人称体验、亲友评价、购买/囤货经历、儿童/孕妇等适用人群\n"
        "- 不得声称未提供的配料、添加剂、营养、功效、包装标签、口感或内部结构\n"
        '- 不要主动生成未提供的认证、销量、排名、保修、适用人数、材质等级\n'
        '- 如果信息不足，用"请商家确认……"表达\n'
        "- 避免使用绝对化用语：'最好'、'第一'、'100%'、'永不'、'绝对'等\n"
        "- RAG资料只作为文案结构和写法参考，不代表当前商品一定具备其中所有特性\n\n"
        "输出要求：\n"
        "请只输出 JSON，不要输出 Markdown。JSON 格式：\n"
        "{\n"
        '  "titles": ["标题版本1", "标题版本2", "标题版本3"],\n'
        '  "selling_points": ["卖点1", "卖点2", "卖点3", "卖点4", "卖点5"],\n'
        '  "detail_copy": "详情页完整文案（含分段和场景描述）",\n'
        '  "short_video_script": "30秒短视频口播脚本",\n'
        '  "subtitle": "商品副标题",\n'
        '  "price_suggestion": null,\n'
        '  "specifications": ["待确认的规格项"],\n'
        '  "target_audience": "目标人群描述",\n'
        '  "usage_scenarios": ["使用场景1"],\n'
        '  "seo_keywords": ["关键词1"],\n'
        '  "promotion_copy": "平台促销短文案，不编造优惠",\n'
        '  "pending_confirmations": ["待商家确认项1", ...]\n'
        "}"
    )

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.system_prompt = self.SYSTEM_PROMPT
        self.retrieval_service = retrieval_service

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate product copy based on product info and market research.

        Args:
            state: Orchestration state with product_info, target_style, market_research

        Returns:
            State update with copy_drafts
        """
        product_info = state.get("product_info", {})
        target_style = state.get("target_style", "taobao")
        market_research = state.get("market_research", {})
        knowledge_base_id = state.get("knowledge_base_id", "")

        title = product_info.get("title", "")
        category = product_info.get("category", "未分类")
        description = product_info.get("description", "")
        price = product_info.get("price", "")

        style_config = SUPPORTED_STYLES.get(target_style, SUPPORTED_STYLES["taobao"])
        logger.info(
            "CopywriterAgent: generating copy for '%s' in style '%s' (%s)",
            title, target_style, style_config["name"],
        )

        # Build RAG context — prefer pre-retrieved context from rag_retrieval node
        rag_context = state.get("rag_context", "")
        if not rag_context:
            # Fallback: retrieve inline (backward compatible with standalone calls)
            rag_context = await self._get_rag_context(
                knowledge_base_id=knowledge_base_id,
                title=title,
                category=category,
            )

        # Build market research context
        market_context = self._format_market_context(market_research)

        # Build the prompt
        prompt = self._build_prompt(
            title=title,
            category=category,
            description=description,
            price=price,
            product_info=product_info,
            target_style=target_style,
            style_name=style_config["name"],
            style_desc=style_config["description"],
            rag_context=rag_context,
            market_context=market_context,
        )

        fallback_error = ""
        try:
            llm_result = self._call_llm(prompt, temperature=0.7, max_tokens=3072)
            parsed = self._parse_json_response(llm_result)

            # Apply fact guard: check for high-risk phrases
            parsed = self._apply_fact_guard(parsed, product_info, market_research)
            # Keep the model's wording while applying deterministic fallbacks
            # and de-duplication.  The previous implementation replaced every
            # generated field with the merchant's original sentence, which
            # made a successful AI call indistinguishable from doing nothing.
            parsed = self._finalize_publishable_copy(parsed, product_info)
        except Exception as exc:
            logger.warning("CopywriterAgent LLM call failed, using fallback: %s", exc)
            fallback_error = str(exc)
            parsed = self._build_safe_fallback(
                title=title,
                category=category,
                description=description,
                target_style=target_style,
                error=str(exc),
            )

        copy_result = {
            "style": target_style,
            "style_name": style_config["name"],
            "titles": parsed.get("titles", [f"【品质好物】{title}"]),
            "selling_points": parsed.get("selling_points", ["品质优选"]),
            "detail_copy": parsed.get("detail_copy", ""),
            "short_video_script": parsed.get("short_video_script", ""),
            "subtitle": parsed.get("subtitle", ""),
            "price_suggestion": parsed.get("price_suggestion"),
            "specifications": parsed.get("specifications", []),
            "target_audience": parsed.get("target_audience", ""),
            "usage_scenarios": parsed.get("usage_scenarios", []),
            "seo_keywords": parsed.get("seo_keywords", []),
            "promotion_copy": parsed.get("promotion_copy", ""),
            "pending_confirmations": parsed.get("pending_confirmations", []),
            "rag_used": bool(rag_context),
            "market_context_used": bool(market_context) and market_research.get("status") != "failed",
            "fallback": bool(fallback_error),
            "error": fallback_error,
        }

        logger.info(
            "CopywriterAgent: generated %d titles, %d selling points",
            len(copy_result["titles"]),
            len(copy_result["selling_points"]),
        )

        return self._make_state_update("copy_drafts", copy_result)

    @staticmethod
    def _finalize_publishable_copy(
        parsed: Dict[str, Any],
        product_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Normalize guarded model copy without erasing its creative rewrite.

        High-risk unsupported claims have already been removed by
        ``_apply_fact_guard``.  This boundary supplies truthful fallbacks,
        removes duplicates, and only accepts specification values that are
        present in the merchant description (or explicitly marked as pending
        confirmation).
        """
        title = str(product_info.get("title", "")).strip() or "商品"
        category = str(product_info.get("category", "")).strip()
        description = str(product_info.get("description", "")).strip()
        merchant_specifications = str(product_info.get("specifications", "")).strip()
        merchant_target_audience = str(product_info.get("target_audience", "")).strip()
        merchant_usage_scenarios = str(product_info.get("usage_scenarios", "")).strip()

        fact_fragments = [
            fragment.strip(" ，,。；;\n\t")
            for fragment in re.split(r"[。；;！？!?\n]+", description)
            if fragment.strip(" ，,。；;\n\t")
        ]
        locked = dict(parsed)

        def unique_text_list(value: Any, *, limit: int) -> List[str]:
            if not isinstance(value, list):
                return []
            result: List[str] = []
            for item in value:
                text = str(item).strip()
                if text and text not in result:
                    result.append(text)
                if len(result) >= limit:
                    break
            return result

        titles = unique_text_list(locked.get("titles"), limit=3) or [title]
        selling_points = unique_text_list(locked.get("selling_points"), limit=5)
        if not selling_points:
            selling_points = fact_fragments[:5] or ["商品详情请以商家实际信息为准"]

        # Specifications are factual SKU attributes.  Keep exact merchant
        # evidence and explicit review placeholders, never an ungrounded value.
        specifications = unique_text_list(
            [line.strip() for line in merchant_specifications.splitlines() if line.strip()],
            limit=10,
        )
        for value in unique_text_list(locked.get("specifications"), limit=10):
            if (
                value not in specifications
                and (
                    value in f"{description}\n{merchant_specifications}"
                    or re.search(r"请.*(?:确认|补充)|待确认", value)
                )
            ):
                specifications.append(value)
        for pattern in (
            r"净含量\s*[:：]?\s*[0-9.]+\s*(?:克|千克|公斤|g|kg|毫升|升|ml|l)",
            r"(?:规格|型号|尺寸|容量|重量)\s*[:：]\s*[^，,。；;\n]{1,40}",
        ):
            for match in re.findall(pattern, description, flags=re.IGNORECASE):
                value = str(match).strip()
                if value and value not in specifications:
                    specifications.append(value)

        detail_copy = str(locked.get("detail_copy", "")).strip()
        subtitle = str(locked.get("subtitle", "")).strip()
        short_video_script = str(locked.get("short_video_script", "")).strip()
        promotion_copy = str(locked.get("promotion_copy", "")).strip()
        target_audience = str(locked.get("target_audience") or merchant_target_audience).strip()
        usage_scenarios = unique_text_list(locked.get("usage_scenarios"), limit=6) \
            or [value.strip() for value in re.split(r"[，,；;\n]+", merchant_usage_scenarios) if value.strip()]
        pending_confirmations = unique_text_list(locked.get("pending_confirmations"), limit=8)
        structured_detail = build_structured_detail(
            base_detail=detail_copy or description,
            title=titles[0] if titles else title,
            category=category,
            selling_points=selling_points,
            specifications=specifications,
            target_audience=target_audience,
            usage_scenarios=usage_scenarios,
            pending_confirmations=pending_confirmations,
        )
        locked.update({
            "titles": titles,
            "selling_points": selling_points,
            "detail_copy": structured_detail,
            "short_video_script": short_video_script or (f"介绍{title}：{description}" if description else ""),
            "subtitle": subtitle or (fact_fragments[0][:80] if fact_fragments else ""),
            "specifications": specifications,
            "target_audience": target_audience,
            "usage_scenarios": usage_scenarios,
            "seo_keywords": unique_text_list(locked.get("seo_keywords"), limit=12)
                or [value for value in (title, category) if value],
            "promotion_copy": promotion_copy or f"了解{title}，具体信息以商品详情和实物为准。",
            "fact_source": "merchant_input_with_guarded_ai_rewrite",
        })
        return locked

    @staticmethod
    def _build_safe_fallback(
        title: str,
        category: str,
        description: str,
        target_style: str,
        error: str,
    ) -> Dict[str, Any]:
        """Create platform-distinct copy using only merchant-provided facts."""
        templates = {
            "pinduoduo": ("【好物推荐】", ["核心信息前置", "表达简洁易读", "优惠请按实际情况补充"]),
            "taobao": ("【商品推荐】", ["商品名与品类清晰", "详情结构便于浏览", "补充真实规格有助于搜索"]),
            "jd": ("【规格清晰】", ["信息规范展示", "建议补充可核验参数", "认证与服务以实际承诺为准"]),
            "suning": ("【品质商品】", ["突出品类与用途", "建议补充真实参数", "售后政策请据实填写"]),
            "xiaohongshu": ("✨ 使用灵感｜", ["从真实场景切入", "自然分享商品特点", "功效与数据需要可核验依据"]),
        }
        prefix, points = templates.get(target_style, templates["taobao"])
        detail = build_structured_detail(
            base_detail=description,
            title=title,
            category=category,
            selling_points=points,
            specifications=["请补充可核验规格"],
            target_audience="请根据真实适用范围补充",
            usage_scenarios=["请根据真实用途补充"],
        )
        return {
            "titles": [f"{prefix}{title}"],
            "selling_points": points,
            "detail_copy": detail,
            "short_video_script": "",
            "subtitle": f"{category}商品信息待完善",
            "price_suggestion": None,
            "specifications": ["请补充可核验规格"],
            "target_audience": "请根据真实适用范围补充",
            "usage_scenarios": ["请根据真实用途补充"],
            "seo_keywords": [title, category],
            "promotion_copy": f"{prefix}{title}，具体价格与优惠以商家实际设置为准。",
            "pending_confirmations": [
                f"模型服务失败：{error}",
                f"请核实{category}商品的规格、价格与描述后再发布",
            ],
        }

    async def _get_rag_context(
        self,
        knowledge_base_id: str,
        title: str,
        category: str,
    ) -> str:
        """Retrieve relevant context from the knowledge base via RAG."""
        if not knowledge_base_id or not self.retrieval_service:
            return ""

        try:
            query = f"{title} {category}"
            chunks = self.retrieval_service.retrieve(
                knowledge_base_id,
                query,
                top_k=self.settings.rag_top_k or 4,
            )
            quality = assess_rag_quality(chunks)
            logger.info("Copywriter RAG quality: %s", quality)
            if not chunks:
                return ""

            lines = ["【知识库参考资料】"]
            for i, chunk in enumerate(chunks, 1):
                content = chunk.get("content", "")
                source = chunk.get("sourceFilename", "未知来源")
                score = float(chunk.get("score", 0))
                lines.append(f"{i}. 来源：{source}（相关度：{score:.2f}）\n{content}")
            return "\n\n".join(lines)
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s", exc)
            return ""

    def _format_market_context(self, market_research: dict) -> str:
        """Format market research results as prompt context."""
        if not market_research or market_research.get("status") == "failed":
            return ""

        parts = ["【市场调研参考】"]
        trends = market_research.get("trends_summary", "")
        if trends:
            parts.append(f"市场趋势：{trends}")

        keywords = market_research.get("hot_keywords", [])
        if keywords:
            parts.append(f"热搜关键词：{'、'.join(keywords[:10])}")

        price_range = market_research.get("competitor_price_range", {})
        if price_range:
            parts.append(
                f"价格带：{price_range.get('low', '?')}-{price_range.get('high', '?')}元"
            )

        suggestions = market_research.get("suggestions", [])
        if suggestions:
            parts.append(f"运营建议：{'；'.join(suggestions[:3])}")

        return "\n".join(parts)

    def _build_prompt(
        self,
        title: str,
        category: str,
        description: str,
        price: str,
        product_info: Dict[str, Any],
        target_style: str,
        style_name: str,
        style_desc: str,
        rag_context: str,
        market_context: str,
    ) -> str:
        """Build the complete prompt for copy generation."""
        parts = [
            "【生成任务】",
            f"目标平台：{style_name}（{style_desc}）",
            f"商品标题：{title}",
            f"商品分类：{category}",
            f"商品描述：{description or '无额外描述'}",
            f"商品价格：{price or '未填写'}",
        ]

        specifications = str(product_info.get("specifications", "")).strip()
        target_audience = str(product_info.get("target_audience", "")).strip()
        usage_scenarios = str(product_info.get("usage_scenarios", "")).strip()
        if specifications:
            parts.append(f"商家已填规格：{specifications}")
        if target_audience:
            parts.append(f"商家已填目标人群：{target_audience}")
        if usage_scenarios:
            parts.append(f"商家已填使用场景：{usage_scenarios}")

        if market_context:
            parts.append(f"\n{market_context}")

        if rag_context:
            parts.append(f"\n{rag_context}")

        parts.append(
            "\n请根据以上信息生成符合{0}风格的商品文案。".format(style_name)
        )
        parts.append("注意：标题需控制在30字以内，卖点每条不超过15字；详情页需写成350至900字的分段长文案。")

        return "\n".join(parts)

    def _apply_fact_guard(
        self,
        parsed: dict,
        product_info: dict,
        market_research: Optional[dict] = None,
    ) -> dict:
        """Apply fact guard rules to prevent hallucination."""
        evidence_text = " ".join([
            str(product_info.get("title", "")),
            str(product_info.get("category", "")),
            str(product_info.get("description", "")),
            str(product_info.get("specifications", "")),
            str(product_info.get("target_audience", "")),
            str(product_info.get("usage_scenarios", "")),
        ]).lower()

        market_research = market_research or {}
        research_only_phrases = []
        for keyword in market_research.get("hot_keywords", []) or []:
            phrase = str(keyword).strip().lower()
            if len(phrase) >= 2 and phrase not in evidence_text:
                research_only_phrases.append(phrase)

        high_risk_phrases = {
            "永不": "请商家确认产品耐久性依据",
            "100%": "请商家确认该比率的检测依据",
            "绝对": "请商家确认相关检测或资质证明",
            "最好": "避免使用绝对化用语'最好'",
            "第一": "请商家提供排名或奖项证明",
            "顶级": "请商家确认该定位的标准依据",
            "唯一": "请商家确认独家性证明",
        }

        pending = list(parsed.get("pending_confirmations", []))

        # These claims are especially common in platform-style copy but must
        # be backed by merchant facts. If evidence does not contain the same
        # fact, discard the affected generated field instead of merely warning.
        unsupported_patterns = {
            r"我家|我上周|上周|昨天|闺蜜|同事|领导|朋友|已囤|亲测|我穿|让我|穿上它|洗过|陌生人|问链接|追着问|要了?链接|不是广告|别问我是怎么知道|姐妹们": "请商家确认是否允许使用真实体验叙事",
            r"无添加|添加剂|人工色素|反式脂肪|配料.{0,12}(干净|清爽|清晰|完整|详实)|健康零食|成分党|零负担": "请商家提供配料与营养依据",
            r"儿童|孩子|小朋友|宝宝|孕妇|老人|\d+岁": "请商家确认适用人群与年龄范围",
            r"包装上.{0,12}(标注|注明)|更放心|吃得更安心": "请商家核实包装标签与安全性描述",
            r"多巴胺|瞳孔地震|根本停不下来|最佳伴侣|心头好": "请商家确认主观体验类表述",
            r"柔软|软糯|亲肤|纯棉|棉质|加绒|保暖|不起球|不褪色|厚实|显白|不挑肤色|舒适|不勒|不卡|不滑落": "请商家提供材质或性能依据",
            r"秋冬必备|完美适应|完美适配|脱颖而出|衣橱.{0,8}新宠": "请商家确认主观营销表述",
        }

        evidence_compact = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", evidence_text)

        def has_merchant_grounding(text: str) -> bool:
            """Require at least one concrete fact fragment in publishable copy."""
            if re.search(r"请.*(?:确认|补充)|待确认|以.*为准", text):
                return True
            compact = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text.lower())
            if not compact:
                return False
            latin_tokens = [token for token in re.findall(r"[a-z0-9]{2,}", compact) if token]
            if any(token in evidence_compact for token in latin_tokens):
                return True
            cjk = "".join(re.findall(r"[\u4e00-\u9fff]", compact))
            return any(cjk[i:i + 2] in evidence_compact for i in range(max(0, len(cjk) - 1)))

        def unsupported(text: str, *, require_grounding: bool = True) -> bool:
            hit = False
            for pattern, confirmation in unsupported_patterns.items():
                if re.search(pattern, text, flags=re.IGNORECASE) and not re.search(
                    pattern, evidence_text, flags=re.IGNORECASE
                ):
                    hit = True
                    if confirmation not in pending:
                        pending.append(confirmation)
            if any(phrase in text.lower() for phrase in research_only_phrases):
                hit = True
                confirmation = "市场热词并非当前商品属性，已从可发布文案中移除"
                if confirmation not in pending:
                    pending.append(confirmation)
            evidence_numbers = set(re.findall(r"\d+(?:\.\d+)?", evidence_text))
            if any(number not in evidence_numbers for number in re.findall(r"\d+(?:\.\d+)?", text)):
                hit = True
                confirmation = "生成内容包含商家未提供的数字，已从可发布文案中移除"
                if confirmation not in pending:
                    pending.append(confirmation)
            if require_grounding and not has_merchant_grounding(text):
                hit = True
                confirmation = "生成内容缺少商家事实依据，已从可发布文案中移除"
                if confirmation not in pending:
                    pending.append(confirmation)
            return hit

        trend_marker = re.compile(
            r"(?:20\d{2}年|今年|马年|本命年|爆款|热销|热度|时尚宠儿|销售旺季)",
            flags=re.IGNORECASE,
        )

        def strip_research_only_claims(text: str) -> str:
            """Keep research as evidence in the side panel, not product facts."""
            fragments = re.split(r"(?<=[。！？!?；;])", str(text or ""))
            retained = []
            for fragment in fragments:
                normalized = fragment.strip()
                if not normalized:
                    continue
                if trend_marker.search(normalized):
                    continue
                if any(phrase in normalized.lower() for phrase in research_only_phrases):
                    continue
                retained.append(normalized)
            return "".join(retained)

        for key in ["titles", "selling_points", "specifications", "usage_scenarios", "seo_keywords"]:
            values = parsed.get(key)
            if isinstance(values, list):
                parsed[key] = [
                    cleaned for value in values
                    if (cleaned := strip_research_only_claims(str(value)))
                ]
        for key in ["detail_copy", "short_video_script", "subtitle", "target_audience", "promotion_copy"]:
            value = parsed.get(key)
            if isinstance(value, str):
                parsed[key] = strip_research_only_claims(value)

        safe_title = str(product_info.get("title", "商品"))
        safe_description = str(product_info.get("description", "")).strip()
        safe_detail = safe_description or f"请商家补充「{safe_title}」的可核验商品详情。"

        for key in ["titles", "selling_points", "specifications", "usage_scenarios", "seo_keywords"]:
            values = parsed.get(key)
            if isinstance(values, list):
                parsed[key] = [str(value) for value in values if not unsupported(str(value))]
        if not parsed.get("titles"):
            parsed["titles"] = [safe_title]
        if not parsed.get("selling_points"):
            parsed["selling_points"] = [safe_description or "请商家补充可核验卖点"]

        for key in ["detail_copy", "short_video_script", "subtitle", "target_audience", "promotion_copy"]:
            value = parsed.get(key)
            if isinstance(value, str) and unsupported(value):
                if key == "detail_copy":
                    parsed[key] = safe_detail
                elif key == "short_video_script":
                    parsed[key] = f"介绍{safe_title}：{safe_detail}"
                elif key == "target_audience":
                    parsed[key] = "请商家根据真实适用范围确认"
                else:
                    parsed[key] = safe_title

        for phrase, confirmation in high_risk_phrases.items():
            # Check if phrase appears in generated content but not in evidence
            all_text = json.dumps(parsed, ensure_ascii=False).lower()
            if phrase.lower() in all_text and phrase.lower() not in evidence_text:
                if confirmation not in pending:
                    pending.append(confirmation)

        # Replace risky phrases in the output
        for key in ["titles", "selling_points"]:
            if key in parsed and isinstance(parsed[key], list):
                parsed[key] = [
                    self._sanitize_text(str(item)) for item in parsed[key]
                ]
        for key in ["detail_copy", "short_video_script"]:
            if key in parsed and isinstance(parsed[key], str):
                parsed[key] = self._sanitize_text(parsed[key])

        parsed["pending_confirmations"] = pending
        return parsed

    def _sanitize_text(self, text: str) -> str:
        """Replace high-risk phrases with conservative alternatives."""
        replacements = {
            "永不粘锅": "不粘性能请以实际测试为准",
            "永不过时": "风格简洁",
            "永不": "注重",
            "100%有效": "实际效果请核实",
            "绝对好用": "使用体验请以实际为准",
            "最好": "可选",
            "第一": "推荐",
            "顶级": "优选",
            "唯一": "特色",
        }
        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
        return result
