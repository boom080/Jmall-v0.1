"""Market research agent that uses Tavily search for e-commerce market analysis.

Refactored to use true LLM Function Calling / Tool Calling:
- LLM decides whether to invoke the search tool based on the user's request.
- If the LLM returns a tool_call, the agent executes the search and feeds results back.
- If the LLM decides no search is needed, it returns the analysis directly.
- Falls back to the old imperative search→summarize pipeline on any tool-calling failure.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.tools.search import (
    SEARCH_MARKET_TRENDS_TOOL,
    SearchEvidence,
    execute_search_tool,
    get_search_tool,
    search_market_trends,
)

logger = logging.getLogger(__name__)


class MarketResearchAgent(BaseAgent):
    """Market research agent for e-commerce category analysis.

    Uses LLM Function Calling to decide whether web search is needed:
    - If the request mentions a real product category/category trends → LLM may call search_market_trends
    - If the request is generic/no real-time data needed → LLM can answer directly

    Uses the cheap model tier (DeepSeek/Haiku).
    """

    agent_type = "market_research"
    model_preference = "cheap"

    SYSTEM_PROMPT = (
        "你是电商市场分析师。根据商品品类分析当前市场趋势、热搜关键词、同品类价格带。\n\n"
        "你的职责：\n"
        "1. 分析该品类在电商平台的当前趋势和热度\n"
        "2. 提取高价值的搜索关键词和长尾词\n"
        "3. 总结同品类商品的价格带分布（低/中/高）\n"
        "4. 给出针对该商品的运营建议\n\n"
        "工具使用指南：\n"
        "- 如果需要了解品类的最新市场趋势、热搜关键词、竞品价格，请使用 search_market_trends 工具\n"
        "- 如果问题不涉及实时市场信息或品类分析，可以直接回答\n\n"
        "输出要求：\n"
        "请只输出 JSON，不要输出 Markdown 或其他文字。JSON 格式：\n"
        "{\n"
        '  "trends_summary": "市场趋势总结（字符串）",\n'
        '  "hot_keywords": ["关键词1", "关键词2", ...],\n'
        '  "competitor_price_range": {"low": 最低价, "mid": 中间价, "high": 最高价, "currency": "CNY"},\n'
        '  "suggestions": ["建议1", "建议2", ...]\n'
        "}"
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.system_prompt = self.SYSTEM_PROMPT
        # Prefer Tavily and automatically fall back to Qwen's official web
        # search feature, reusing the Model Studio key already configured for AI.
        self.search_tool = get_search_tool(
            self.settings.tavily_api_key,
            self.settings.qwen_api_key,
            self.settings.qwen_base_url,
            self.settings.qwen_chat_model,
        )
        # Register available tools for LLM function calling
        self.tools = [SEARCH_MARKET_TRENDS_TOOL]
        self._latest_search_evidence: Optional[SearchEvidence] = None

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute the search_market_trends tool when the LLM requests it."""
        if tool_name == "search_market_trends":
            evidence = await execute_search_tool(self.search_tool, arguments)
            self._latest_search_evidence = evidence
            return evidence
        raise ValueError(f"Unknown tool: {tool_name}")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute market research using LLM tool calling.

        The LLM decides whether to search the web or answer directly.
        Falls back to imperative search→summarize on failure.

        Args:
            state: Orchestration state with product_info

        Returns:
            State update with market_research results
        """
        product_info = state.get("product_info", {})
        category = product_info.get("category", "未分类")
        title = product_info.get("title", "")
        description = product_info.get("description", "")
        self._latest_search_evidence = None

        logger.info("MarketResearchAgent: researching category='%s' (tool-calling mode)", category)

        # Build the user prompt
        user_prompt = (
            f"请分析'{category}'品类的电商市场情况：\n\n"
            f"商品标题：{title}\n"
            f"商品描述：{description}\n"
        )

        # ---- Primary path: LLM tool calling ----
        try:
            llm_result = await self._call_llm_with_tools(
                user_message=user_prompt,
                tools=self.tools,
                temperature=0.3,
                max_tokens=1024,
                max_iterations=3,
            )

            content = llm_result.get("content", "")
            tool_history = llm_result.get("tool_call_history", [])

            failed_tools = [call for call in tool_history if not call.get("success")]
            successful_tools = [call for call in tool_history if call.get("success")]
            if failed_tools and not successful_tools:
                error = failed_tools[-1].get("error", "市场搜索不可用")
                return self._make_state_update(
                    "market_research",
                    self._unavailable_result(category, error, tool_history),
                )

            if content:
                parsed = self._parse_json_response(llm_result)
                research_result = self._build_research_result(
                    parsed=parsed,
                    category=category,
                    tool_history=tool_history,
                    method="tool_calling",
                )
                logger.info(
                    "MarketResearchAgent (tool-calling): completed, %d tool calls, %d keywords",
                    len(tool_history),
                    len(research_result.get("hot_keywords", [])),
                )
                return self._make_state_update("market_research", research_result)

            # If LLM returned neither content nor tool calls, fall through to fallback
            logger.warning(
                "MarketResearchAgent: tool-calling returned no content, "
                "falling back to imperative search"
            )
        except Exception as exc:
            logger.warning(
                "MarketResearchAgent: tool-calling failed (%s), "
                "falling back to imperative search",
                exc,
            )

        # ---- Fallback: imperative search → summarize (original behavior) ----
        return await self._run_imperative_fallback(state)

    async def _run_imperative_fallback(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Original imperative search→summarize pipeline, kept as fallback."""
        product_info = state.get("product_info", {})
        category = product_info.get("category", "未分类")
        title = product_info.get("title", "")
        description = product_info.get("description", "")

        logger.info("MarketResearchAgent (fallback): running imperative search pipeline")

        # Step 1: Perform web search
        keywords = []
        if title:
            keywords.append(title)
        try:
            search_results = search_market_trends(
                self.search_tool,
                category=category,
                keywords=keywords,
            )
        except Exception as exc:
            logger.warning("MarketResearchAgent: realtime search unavailable: %s", exc)
            return self._make_state_update(
                "market_research",
                self._unavailable_result(category, str(exc), []),
            )
        self._track_standalone_search_usage(search_results)

        # Step 2: Use LLM to analyze and structure the search results
        prompt = (
            f"请根据以下搜索结果，分析'{category}'品类的电商市场情况：\n\n"
            f"商品标题：{title}\n"
            f"商品描述：{description}\n\n"
            f"搜索结果：\n{search_results}\n\n"
            "请基于搜索结果输出结构化的 JSON 分析报告。"
        )

        try:
            llm_result = self._call_llm(prompt, temperature=0.3, max_tokens=1024)
        except Exception as exc:
            logger.warning(
                "MarketResearchAgent fallback LLM call failed: %s, using raw search results", exc,
            )
            research_result = self._build_research_result(
                parsed={},
                category=category,
                tool_history=[],
                method="imperative_fallback",
            )
            research_result["trends_summary"] = search_results
            research_result["hot_keywords"] = [category]
            research_result["suggestions"] = ["LLM分析暂时不可用，请直接参考搜索原始结果"]
            return self._make_state_update("market_research", research_result)

        parsed = self._parse_json_response(llm_result)

        research_result = self._build_research_result(
            parsed=parsed,
            category=category,
            tool_history=[],
            method="imperative_fallback",
        )

        logger.info(
            "MarketResearchAgent (fallback): completed, %d keywords",
            len(research_result.get("hot_keywords", [])),
        )

        return self._make_state_update("market_research", research_result)

    def _track_standalone_search_usage(self, evidence: SearchEvidence) -> None:
        """Track Qwen web-search tokens when no tool-calling loop owns the call."""
        self._latest_search_evidence = evidence
        input_tokens = int(getattr(evidence, "input_tokens", 0) or 0)
        output_tokens = int(getattr(evidence, "output_tokens", 0) or 0)
        if self.cost_tracker and (input_tokens or output_tokens):
            self.cost_tracker.track(
                provider=getattr(evidence, "provider", "search"),
                model=getattr(evidence, "model", "") or "unknown_search_model",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                agent_type=f"{self.agent_type}.web_search",
            )

    def _unavailable_result(
        self,
        category: str,
        error: str,
        tool_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Return a truthful, usable result without inventing realtime claims."""
        return {
            "category": category,
            "status": "failed",
            "method": "realtime_search_unavailable",
            "search_tool": getattr(self.search_tool, "name", "tavily"),
            "sources": [],
            "source_count": 0,
            "research_scope": "公开互联网实时检索",
            "trends_summary": "实时市场调研暂时不可用，未生成趋势结论。",
            "hot_keywords": [],
            "competitor_price_range": {
                "low": 0, "mid": 0, "high": 0, "currency": "CNY",
            },
            "suggestions": ["可继续完善商品基础信息，稍后重试实时市场调研"],
            "error": error,
            "tool_calls": tool_history,
        }

    def _build_research_result(
        self,
        parsed: Dict[str, Any],
        category: str,
        tool_history: List[Dict[str, Any]],
        method: str,
    ) -> Dict[str, Any]:
        """Build the standardized research result dict.

        Ensures consistent output format regardless of which code path was taken.
        """
        research_result: Dict[str, Any] = {
            "category": category,
            "search_tool": (
                getattr(self._latest_search_evidence, "provider", "")
                or getattr(self.search_tool, "name", "mock_search")
            ),
            "method": method,
            **parsed,
        }

        sources: List[Dict[str, str]] = list(
            getattr(self._latest_search_evidence, "sources", []) or []
        )
        if not sources:
            for call in tool_history:
                for source in call.get("sources", []) or []:
                    if isinstance(source, dict):
                        sources.append(source)
        deduplicated_sources: List[Dict[str, str]] = []
        seen_urls = set()
        for source in sources:
            url = str(source.get("url", "")).strip()
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduplicated_sources.append({
                    "title": str(source.get("title") or url),
                    "url": url,
                })
        research_result["sources"] = deduplicated_sources[:8]
        research_result["source_count"] = len(research_result["sources"])
        research_result["research_scope"] = "公开互联网实时检索"

        # If parsing failed, use raw content as fallback
        if "raw_content" in research_result and "parse_error" in research_result:
            research_result["status"] = "failed"
            research_result["trends_summary"] = "市场结果结构化失败，未生成趋势结论。"
            research_result["hot_keywords"] = []
            research_result["competitor_price_range"] = {
                "low": 0, "mid": 0, "high": 0, "currency": "CNY",
            }
            research_result["suggestions"] = ["请稍后重试，或人工核验搜索资料"]
            research_result["error"] = research_result.get("parse_error", "LLM response JSON parsing failed")
            research_result["raw_content"] = ""

        # Attach tool call history for observability
        if tool_history:
            research_result["tool_calls"] = tool_history

        return research_result
