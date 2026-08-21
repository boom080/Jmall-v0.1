"""Orchestrator agent that decomposes user tasks and coordinates sub-agents."""

import json
import logging
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """Main orchestrator that decomposes user tasks and coordinates sub-agents.

    Input: User request with product info and target style.
    Decomposes into: market_research -> copy_generation -> compliance_review -> style_adaptation.
    Runs sub-agents in sequence or parallel as appropriate.
    Aggregates results.

    Uses the strong model tier for planning and decomposition.
    """

    agent_type = "orchestration"
    model_preference = "cheap"  # Planning is a simple task — use fast/cheap model

    SYSTEM_PROMPT = (
        "你是 Jmall 的 AI 运营总监，负责协调多个 AI 助手完成商家任务。\n\n"
        "你可以调用的助手：\n"
        "1. market_research - 市场调研助手：搜索品类趋势、热搜关键词、竞品价格带\n"
        "2. copy_generation - 文案生成助手：创作商品标题、卖点、详情页、短视频脚本\n"
        "3. compliance_review - 合规审查助手：检查广告法合规、价格合理性、信息完整性\n"
        "4. style_adaptation - 风格适配助手：将文案适配到目标平台（淘宝/拼多多/京东/苏宁/小红书）\n\n"
        "你的职责：\n"
        "1. 理解商家的需求，拆解为可执行的子任务\n"
        "2. 确定任务执行顺序和依赖关系\n"
        "3. 汇总各助手的结果，形成完整的交付物\n"
        "4. 在出现问题时做出决策（跳过、重试、降级）\n\n"
        "输出要求：\n"
        "请只输出 JSON，不要输出 Markdown。JSON 格式：\n"
        "{\n"
        '  "plan": [\n'
        '    {"step": "agent_type", "description": "任务描述", "depends_on": ["前置步骤"]},\n'
        '    ...\n'
        '  ],\n'
        '  "reasoning": "任务分解的理由（字符串）",\n'
        '  "expected_output": "期望的最终交付物描述（字符串）",\n'
        '  "estimated_time_seconds": 60\n'
        "}"
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.system_prompt = self.SYSTEM_PROMPT

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Decompose user request into an execution plan.

        Args:
            state: Current orchestration state

        Returns:
            State update with execution plan
        """
        user_request = state.get("user_request", "")
        product_info = state.get("product_info", {})
        target_style = state.get("target_style", "taobao")
        knowledge_base_id = state.get("knowledge_base_id", "")

        title = product_info.get("title", "")
        category = product_info.get("category", "未分类")
        description = product_info.get("description", "")

        logger.info(
            "OrchestratorAgent: planning for '%s' style=%s kb=%s",
            title, target_style, knowledge_base_id or "none",
        )

        prompt = (
            f"商家需求：{user_request or f'为商品「{title}」生成{target_style}风格的电商文案'}\n\n"
            f"商品信息：\n"
            f"  标题：{title}\n"
            f"  分类：{category}\n"
            f"  描述：{description or '无'}\n"
            f"  目标平台：{target_style}\n"
            f"  知识库：{'已配置' if knowledge_base_id else '未配置'}\n\n"
            "请分析以上需求，拆解为子任务并输出执行计划 JSON。"
        )

        fallback_error = ""
        try:
            llm_result = self._call_llm(prompt, temperature=0.4, max_tokens=1024)
            parsed = self._parse_json_response(llm_result)
        except Exception as exc:
            logger.warning("OrchestratorAgent LLM call failed, using default plan: %s", exc)
            fallback_error = str(exc)
            parsed = {}

        # Build default plan if parsing fails
        plan = parsed.get("plan", [])
        if not plan or not isinstance(plan, list):
            plan = self._build_default_plan(knowledge_base_id)

        reasoning = parsed.get("reasoning", "自动生成的标准执行流程")
        expected_output = parsed.get("expected_output", "完整的电商文案交付物")

        execution_plan = {
            "plan": plan,
            "reasoning": reasoning,
            "expected_output": expected_output,
            "target_style": target_style,
            "knowledge_base_available": bool(knowledge_base_id),
            "fallback": bool(fallback_error),
            "error": fallback_error,
        }

        logger.info(
            "OrchestratorAgent: plan=%d steps, reasoning=%s",
            len(plan), reasoning[:80],
        )

        return self._make_state_update("orchestration_plan", execution_plan)

    def _build_default_plan(self, knowledge_base_id: str) -> List[Dict[str, Any]]:
        """Build default execution plan when LLM parsing fails."""
        plan = [
            {
                "step": "market_research",
                "description": "搜索品类市场趋势、热搜关键词和竞品价格带",
                "depends_on": [],
            },
            {
                "step": "copy_generation",
                "description": "根据商品信息和市场调研结果生成电商文案",
                "depends_on": ["market_research"],
            },
            {
                "step": "compliance_review",
                "description": "审查生成文案的合规性和质量",
                "depends_on": ["copy_generation"],
            },
            {
                "step": "style_adaptation",
                "description": "将文案适配到目标平台的风格",
                "depends_on": ["copy_generation"],
            },
        ]
        if not knowledge_base_id:
            note = "注意：未配置知识库，文案生成将仅基于商品信息和市场调研"
            for step in plan:
                if step["step"] == "copy_generation":
                    step["description"] += f"（{note}）"
        return plan

    def aggregate_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from all sub-agents into a final deliverable.

        Args:
            state: Complete orchestration state with all agent results

        Returns:
            Final aggregated result dict
        """
        product_info = state.get("product_info", {})
        market_research = state.get("market_research", {})
        copy_drafts = state.get("copy_drafts", {})
        review_result = state.get("review_result", {})
        style_previews = state.get("style_previews", {})
        errors = list(dict.fromkeys(state.get("errors", [])))
        title = product_info.get("title", "")

        # The final editable form must use the selected, guarded platform
        # preview.  This keeps the applied title/detail identical to what the
        # merchant sees in the corresponding preview card.
        selected_copy = dict(copy_drafts)
        if style_previews:
            selected_copy["titles"] = [
                style_previews.get("adapted_title")
                or (copy_drafts.get("titles") or [title])[0]
            ]
            selected_copy["selling_points"] = (
                style_previews.get("adapted_selling_points")
                or copy_drafts.get("selling_points", [])
            )
            selected_copy["detail_copy"] = (
                style_previews.get("adapted_detail")
                or copy_drafts.get("detail_copy", "")
            )
        # Determine overall status
        review_status = review_result.get("status", "unknown")
        if review_status == "rejected":
            overall_status = "needs_revision"
        elif review_status == "warning":
            overall_status = "ready_with_warnings"
        elif errors:
            overall_status = "partial_success"
        else:
            overall_status = "success"

        final_result = {
            "product_title": title,
            "overall_status": overall_status,
            "market_insights": {
                "trends": market_research.get("trends_summary", ""),
                "keywords": market_research.get("hot_keywords", []),
                "price_range": market_research.get("competitor_price_range", {}),
                "suggestions": market_research.get("suggestions", []),
                "sources": market_research.get("sources", []),
                "source_count": market_research.get("source_count", 0),
                "search_provider": market_research.get("search_tool", ""),
                "research_scope": market_research.get("research_scope", ""),
                "method": market_research.get("method", ""),
            },
            "copy": {
                "titles": selected_copy.get("titles", []),
                "selling_points": selected_copy.get("selling_points", []),
                "detail_copy": selected_copy.get("detail_copy", ""),
                "short_video_script": copy_drafts.get("short_video_script", ""),
                "subtitle": copy_drafts.get("subtitle", ""),
                "price_suggestion": copy_drafts.get("price_suggestion"),
                "specifications": copy_drafts.get("specifications", []),
                "target_audience": copy_drafts.get("target_audience", ""),
                "usage_scenarios": copy_drafts.get("usage_scenarios", []),
                "seo_keywords": copy_drafts.get("seo_keywords", []),
                "promotion_copy": copy_drafts.get("promotion_copy", ""),
                "style": copy_drafts.get("style", ""),
            },
            "compliance": {
                "status": review_result.get("status", "unknown"),
                "issues": review_result.get("issues", []),
                "warnings": review_result.get("warnings", []),
                "summary": review_result.get("summary", ""),
                "checklist": review_result.get("checklist", {}),
            },
            "style_adaptation": {
                "target_style": style_previews.get("target_style", ""),
                "adapted_title": style_previews.get("adapted_title", ""),
                "adapted_selling_points": style_previews.get("adapted_selling_points", []),
                "adapted_detail": style_previews.get("adapted_detail", ""),
                "visual_params": style_previews.get("visual_params", {}),
                "style_notes": style_previews.get("style_notes", ""),
                "previews": style_previews.get("previews", {}),
            },
            "pending_confirmations": copy_drafts.get("pending_confirmations", []),
            "errors": errors,
            "generation_metadata": {
                "agents_executed": [
                    name for name in ["market_research", "copy_drafts", "review_result", "style_previews"]
                    if state.get(name)
                ],
                "has_errors": bool(errors),
            },
        }

        logger.info(
            "OrchestratorAggregation: status=%s agents=%d",
            overall_status, len(final_result["generation_metadata"]["agents_executed"]),
        )

        return final_result
