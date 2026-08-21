"""Search tools powered by Tavily for market research."""

import json
import logging
import re
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class SearchEvidence(str):
    """String-compatible search output carrying provider and source metadata."""

    def __new__(
        cls,
        content: str,
        *,
        provider: str,
        sources: Optional[List[Dict[str, str]]] = None,
        model: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> "SearchEvidence":
        instance = str.__new__(cls, content)
        instance.provider = provider
        instance.sources = sources or []
        instance.model = model
        instance.input_tokens = input_tokens
        instance.output_tokens = output_tokens
        return instance


def _provider_name(search_tool: Any) -> str:
    return str(getattr(search_tool, "name", type(search_tool).__name__))


def _extract_sources(value: Any) -> List[Dict[str, str]]:
    """Extract a compact, de-duplicated source list from search output."""
    items: List[Dict[str, str]] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict) and item.get("url"):
                items.append({
                    "title": str(item.get("title") or urlparse(str(item["url"])).netloc),
                    "url": str(item["url"]),
                })
    elif isinstance(value, str):
        # Qwen search commonly returns Markdown links.  Also accept bare URLs.
        for title, url in re.findall(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", value):
            items.append({"title": title.strip(), "url": url.rstrip(".,，。")})
        linked_urls = {item["url"] for item in items}
        for url in re.findall(r"https?://[^\s<>\]\)\}\"']+", value):
            normalized = url.rstrip(".,，。;；")
            if normalized not in linked_urls:
                items.append({"title": urlparse(normalized).netloc, "url": normalized})

    result: List[Dict[str, str]] = []
    seen = set()
    for item in items:
        url = item.get("url", "")
        if not url or url in seen:
            continue
        seen.add(url)
        result.append(item)
        if len(result) >= 8:
            break
    return result


def get_search_tool(
    api_key: str,
    qwen_api_key: str = "",
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    qwen_model: str = "qwen-plus",
) -> Any:
    """Get a realtime search tool with Tavily -> Qwen fallback.

    Returns a callable that performs web searches. Configuration problems are
    represented by an unavailable tool so callers can report failure honestly.

    Args:
        api_key: Tavily API key

    Returns:
        A TavilySearchResults instance or a mock search function
    """
    qwen_tool = None
    if qwen_api_key and qwen_api_key.strip():
        qwen_tool = _QwenWebSearchTool(
            qwen_api_key.strip(), qwen_base_url, qwen_model or "qwen-plus"
        )

    if not api_key or not api_key.strip():
        if qwen_tool is not None:
            logger.info("Tavily is not configured; using Qwen web search")
            return qwen_tool
        logger.warning("No realtime search provider is configured")
        return _UnavailableSearchTool(
            "Tavily API key is not configured and Qwen web search is unavailable"
        )

    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        tool = TavilySearchResults(
            max_results=5,
            tavily_api_key=api_key.strip(),
        )
        logger.info("Tavily search tool initialized (max_results=5)")
        return _FallbackSearchTool(tool, qwen_tool) if qwen_tool is not None else tool
    except ImportError:
        logger.warning(
            "langchain_community or tavily-python not installed; realtime search is unavailable. "
            "Install with: pip install langchain-community tavily-python"
        )
        if qwen_tool is not None:
            return qwen_tool
        return _UnavailableSearchTool("Tavily dependencies are not installed")
    except Exception as exc:
        logger.error("Failed to initialize Tavily search tool: %s", exc)
        if qwen_tool is not None:
            return qwen_tool
        return _UnavailableSearchTool(f"Tavily initialization failed: {exc}")


class _FallbackSearchTool:
    """Run the secondary provider when the primary search request fails."""

    name = "realtime_search_with_fallback"
    description = "Search the web with automatic provider fallback."

    def __init__(self, primary: Any, fallback: Any) -> None:
        self.primary = primary
        self.fallback = fallback

    def invoke(self, query: str) -> Any:
        try:
            result = self.primary.invoke(query)
            if isinstance(result, list):
                if not result or any(not isinstance(item, dict) or item.get("error") for item in result):
                    raise RuntimeError("Primary search returned invalid results")
            normalized = str(result).strip().lower()
            error_markers = (
                "httperror", "client error", "server error", "unauthorized",
                "forbidden", "rate limit", "api key", "timed out", "timeout",
            )
            if any(marker in normalized for marker in error_markers):
                raise RuntimeError(str(result)[:300])
            return SearchEvidence(
                _format_search_results(result) if isinstance(result, list) else str(result),
                provider=_provider_name(self.primary),
                sources=_extract_sources(result),
            )
        except Exception as exc:
            logger.warning("Primary search provider failed; switching to Qwen: %s", exc)
            return self.fallback.invoke(query)


class _QwenWebSearchTool:
    """Use Model Studio's official enable_search Chat Completions feature."""

    name = "qwen_web_search"
    description = "Search the web through Qwen Model Studio."

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def invoke(self, query: str) -> SearchEvidence:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是市场检索助手。必须联网检索，并给出带来源链接的最新事实摘要；"
                    "不要补造数据。"
                ),
            },
            {"role": "user", "content": query},
        ]
        compatible_payload = {
            "model": self.model,
            "messages": messages,
            "enable_search": True,
            "search_options": {"forced_search": True, "search_strategy": "turbo"},
            "temperature": 0.1,
            "max_tokens": 1400,
        }
        # The native DashScope endpoint can return structured search sources.
        # Fall back to the OpenAI-compatible endpoint for custom gateways.
        use_native = "/compatible-mode/v1" in self.base_url
        if use_native:
            api_root = self.base_url.split("/compatible-mode/v1", 1)[0]
            endpoint = f"{api_root}/api/v1/services/aigc/text-generation/generation"
            payload = {
                "model": self.model,
                "input": {"messages": messages},
                "parameters": {
                    "enable_search": True,
                    "search_options": {
                        "forced_search": True,
                        "search_strategy": "turbo",
                        "enable_source": True,
                        "enable_citation": True,
                    },
                    "result_format": "message",
                    "temperature": 0.1,
                    "max_tokens": 1400,
                },
            }
        else:
            endpoint = f"{self.base_url}/chat/completions"
            payload = compatible_payload
        response = httpx.post(
            endpoint,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
            timeout=45.0,
        )
        response.raise_for_status()
        data = response.json()
        output = data.get("output", {})
        choices = data.get("choices") or output.get("choices") or []
        content = choices[0].get("message", {}).get("content", "") if choices else ""
        if not str(content).strip():
            raise RuntimeError("Qwen web search returned no content")
        raw_sources = (
            data.get("search_info", {}).get("search_results", [])
            or output.get("search_info", {}).get("search_results", [])
        )
        usage = data.get("usage", {})
        input_tokens = int(usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0)
        output_tokens = int(usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0)
        sources = _extract_sources(raw_sources) or _extract_sources(str(content))
        return SearchEvidence(
            str(content).strip(),
            provider=self.name,
            sources=sources,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )


class _UnavailableSearchTool:
    """Search tool placeholder that preserves an explicit failure state."""

    name = "tavily_search_unavailable"
    description = "Realtime market search is unavailable."

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def invoke(self, query: str) -> str:
        raise RuntimeError(self.reason)


class _MockSearchTool:
    """Mock search tool that returns canned results when Tavily is unavailable."""

    name = "tavily_search_results_json"
    description = "Search the web for market trends and information."

    def __init__(self) -> None:
        self._mock_results: Dict[str, List[Dict[str, str]]] = {
            "茶叶": [
                {"title": "2024茶叶消费趋势报告：健康化、年轻化成主旋律", "url": "https://example.com/tea-trends-2024", "content": "茶叶市场呈现健康化、便捷化、年轻化趋势。龙井茶作为绿茶代表，搜索量同比增长23%。"},
                {"title": "淘宝茶叶品类热搜关键词TOP20", "url": "https://example.com/taobao-tea-keywords", "content": "龙井茶、明前茶、春茶、绿茶、送礼茶叶等关键词搜索热度持续走高。"},
                {"title": "高端茶叶价格带分析：500-2000元成主流", "url": "https://example.com/tea-pricing", "content": "茶叶礼盒500-2000元价格带占比最高，散装茶100-500元为主流。"},
            ],
            "炒锅": [
                {"title": "厨房锅具市场分析：不粘锅仍是主力", "url": "https://example.com/cookware-market", "content": "不粘锅占锅具市场份额45%，铁锅和精铁锅增长迅速。"},
                {"title": "2024炒锅热搜词：无涂层、健康、轻便", "url": "https://example.com/wok-keywords", "content": "消费者越来越关注健康烹饪，无涂层铁锅搜索量增长67%。"},
            ],
            "手机": [
                {"title": "2024手机市场趋势：折叠屏成新增长点", "url": "https://example.com/phone-trends", "content": "折叠屏手机出货量同比增长52%，AI手机概念热度飙升。"},
                {"title": "电商平台手机品类价格带分布", "url": "https://example.com/phone-pricing", "content": "2000-4000元价位段竞争最激烈，占销量的38%。"},
            ],
        }

    def invoke(self, query: str) -> str:
        """Simulate a search by returning mock results."""
        results: List[Dict[str, str]] = []
        query_lower = query.lower()
        for keyword, items in self._mock_results.items():
            if keyword in query or keyword in query_lower:
                results.extend(items)
        if not results:
            results = [
                {"title": f"搜索结果：{query}", "url": "https://example.com/search", "content": f"关于'{query}'的市场信息：该品类在电商平台表现活跃，建议关注当前热搜趋势和价格带分布。"},
            ]
        # Format results as JSON string (mimicking Tavily output)
        return json.dumps(results, ensure_ascii=False)

    def __call__(self, query: str) -> str:
        return self.invoke(query)


def search_market_trends(
    search_tool: Any,
    category: str,
    keywords: Optional[List[str]] = None,
) -> SearchEvidence:
    """Perform market trend search for a product category.

    Args:
        search_tool: A Tavily search tool or mock
        category: The product category to search for
        keywords: Optional additional keywords

    Returns:
        Formatted search results as a string
    """
    query_parts = [f"{category} 电商 市场趋势 热搜"]
    if keywords:
        query_parts.extend(keywords[:3])
    query = " ".join(query_parts)

    try:
        result = search_tool.invoke(query)
        if isinstance(result, list):
            if not result:
                raise RuntimeError("Realtime search returned no results")
            if any(not isinstance(item, dict) or item.get("error") for item in result):
                raise RuntimeError(f"Realtime search returned an error result: {result[0]}")
            return SearchEvidence(
                _format_search_results(result),
                provider=_provider_name(search_tool),
                sources=_extract_sources(result),
            )
        if isinstance(result, str):
            normalized = result.strip().lower()
            error_markers = (
                "httperror", "client error", "server error", "unauthorized",
                "forbidden", "rate limit", "api key", "timed out", "timeout",
            )
            if not normalized or any(marker in normalized for marker in error_markers):
                raise RuntimeError(f"Realtime search returned an error response: {result[:300]}")
            if isinstance(result, SearchEvidence):
                return result
            return SearchEvidence(
                result,
                provider=_provider_name(search_tool),
                sources=_extract_sources(result),
            )
        return SearchEvidence(
            str(result),
            provider=_provider_name(search_tool),
            sources=_extract_sources(result),
        )
    except Exception as exc:
        logger.error("Search failed for query '%s': %s", query, exc)
        raise RuntimeError(f"Realtime search failed: {exc}") from exc


def _format_search_results(results: List[Dict[str, Any]]) -> str:
    """Format search results into a readable string."""
    lines = ["【市场搜索结果】"]
    for i, item in enumerate(results, 1):
        title = item.get("title", "无标题")
        content = item.get("content", item.get("snippet", ""))
        url = item.get("url", "")
        lines.append(f"{i}. {title}")
        if content:
            lines.append(f"   摘要：{content}")
        if url:
            lines.append(f"   链接：{url}")
    return "\n".join(lines)


# ---- OpenAI-compatible Tool Definition ----

SEARCH_MARKET_TRENDS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_market_trends",
        "description": (
            "搜索互联网上的实时电商市场信息，包括当前市场趋势、热搜关键词、"
            "消费者关注点、竞品价格带分布和品类动态。"
            "当你需要了解某个品类的真实市场状况、最新趋势或消费者偏好时，"
            "应使用此工具获取实时数据。"
            "如果用户的问题不涉及实时市场信息或品类分析，可以不调用此工具。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "要搜索的商品品类，如'茶叶'、'手机'、'炒锅'、'护肤品'等",
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "额外的搜索关键词，用于细化搜索范围，如['龙井', '送礼']",
                },
            },
            "required": ["category"],
        },
    },
}


async def execute_search_tool(
    search_tool: Any,
    arguments: Dict[str, Any],
) -> SearchEvidence:
    """Execute the search_market_trends tool from LLM tool_call arguments.

    This is the executor called by MarketResearchAgent._execute_tool().

    Args:
        search_tool: The search tool instance (Tavily or mock)
        arguments: Parsed tool_call arguments from the LLM

    Returns:
        Formatted search results string to be sent back to the LLM
    """
    category = arguments.get("category", "")
    keywords = arguments.get("keywords", [])
    if isinstance(keywords, str):
        keywords = [keywords]
    return search_market_trends(
        search_tool=search_tool,
        category=category,
        keywords=keywords,
    )
