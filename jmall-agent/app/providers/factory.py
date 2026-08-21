import json
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import Settings
from app.models.responses import AiModelOptionResponse
from app.providers.base import ProductCopyProvider
from app.providers.mock_provider import MockProductCopyProvider
from app.providers.openai_compatible_provider import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get_product_copy_provider(self, provider_name: str) -> ProductCopyProvider:
        normalized = (provider_name or self.settings.ai_provider or "mock").strip().lower()
        if normalized == "mock":
            return MockProductCopyProvider()
        if normalized == "deepseek":
            return OpenAICompatibleProvider(
                provider_name="deepseek",
                api_key=self.settings.deepseek_api_key,
                base_url=self.settings.deepseek_base_url,
            )
        if normalized == "qwen":
            return OpenAICompatibleProvider(
                provider_name="qwen",
                api_key=self.settings.qwen_api_key,
                base_url=self.settings.qwen_base_url,
            )
        raise ValueError(f"不支持的 provider: {provider_name}")

    def list_available_models(self) -> List[AiModelOptionResponse]:
        models = [
            AiModelOptionResponse(
                id="mock:mock-product-copy-v1",
                label="Mock / mock-product-copy-v1",
                provider="mock",
                modelName="mock-product-copy-v1",
                description="本地可稳定联调的 Mock 文案模型",
            ),
        ]
        if self.settings.deepseek_api_key.strip():
            deepseek_model = self.settings.deepseek_model or "deepseek-chat"
            models.append(
                AiModelOptionResponse(
                    id=f"deepseek:{deepseek_model}",
                    label=f"DeepSeek / {deepseek_model}",
                    provider="deepseek",
                    modelName=deepseek_model,
                    description="OpenAI 兼容接口，已检测到 DeepSeek API Key",
                )
            )
        if self.settings.qwen_api_key.strip():
            qwen_model = self.settings.qwen_chat_model or "qwen-plus"
            models.append(
                AiModelOptionResponse(
                    id=f"qwen:{qwen_model}",
                    label=f"Qwen / {qwen_model}",
                    provider="qwen",
                    modelName=qwen_model,
                    description="阿里云百炼 OpenAI 兼容模型，已检测到 Qwen API Key",
                )
            )
        return models

    def resolve_model_name(self, provider_name: str, request_model_name: str) -> str:
        explicit = (request_model_name or "").strip()
        if explicit:
            return explicit
        defaults: Dict[str, str] = {
            "mock": self.settings.ai_model_name or "mock-product-copy-v1",
            "deepseek": self.settings.deepseek_model or "deepseek-chat",
            "qwen": self.settings.qwen_chat_model or "qwen-plus",
        }
        return defaults.get(provider_name, self.settings.ai_model_name or "mock-product-copy-v1")

    def chat(
        self,
        provider_name: str,
        model_name: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
    ) -> Dict[str, Any]:
        """General-purpose chat completion for agent LLM calls.

        Args:
            provider_name: "mock", "deepseek", or "qwen"
            model_name: The model to use (e.g., "deepseek-chat", "gpt-4o")
            messages: List of {"role": "system"|"user"|"assistant"|"tool", "content": "..."}
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum output tokens
            tools: Optional list of OpenAI-compatible tool definitions
            tool_choice: "auto", "none", "required", or a specific tool choice dict

        Returns:
            Dict with keys: content (str|None), input_tokens (int), output_tokens (int),
            provider (str), model (str), success (bool), error (str|None),
            tool_calls (list|None) — present when the model returns tool calls
        """
        normalized = (provider_name or self.settings.ai_provider or "mock").strip().lower()
        started_at = time.monotonic()

        if normalized == "mock":
            result = self._mock_chat(model_name, messages, tools)
            result.update({"http_status": None, "duration_ms": int((time.monotonic() - started_at) * 1000), "retry_count": 0})
            logger.info(
                "llm_call provider=%s model=%s status=mock duration_ms=%s retry_count=0 prompt_tokens=%s completion_tokens=%s",
                normalized, model_name, result["duration_ms"], result.get("input_tokens", 0), result.get("output_tokens", 0),
            )
            return result

        # Resolve API credentials for real providers
        if normalized == "deepseek":
            api_key = self.settings.deepseek_api_key
            base_url = self.settings.deepseek_base_url
        elif normalized == "qwen":
            api_key = self.settings.qwen_api_key
            base_url = self.settings.qwen_base_url
        else:
            result = {
                "content": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "provider": normalized,
                "model": model_name,
                "success": False,
                "error": f"Unsupported provider: {normalized}",
                "http_status": None,
                "duration_ms": int((time.monotonic() - started_at) * 1000),
                "retry_count": 0,
            }
            logger.error("llm_call provider=%s model=%s status=unsupported duration_ms=%s retry_count=0", normalized, model_name, result["duration_ms"])
            return result

        if not api_key or not api_key.strip():
            result = {
                "content": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "provider": normalized,
                "model": model_name,
                "success": False,
                "error": f"API key is not configured for provider: {normalized}",
                "tool_calls": None,
                "http_status": None,
                "duration_ms": int((time.monotonic() - started_at) * 1000),
                "retry_count": 0,
            }
            logger.error("llm_call provider=%s model=%s status=missing_key duration_ms=%s retry_count=0", normalized, model_name, result["duration_ms"])
            return result

        try:
            request_body: Dict[str, Any] = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if tools:
                request_body["tools"] = tools
                request_body["tool_choice"] = tool_choice

            response = httpx.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {api_key.strip()}"},
                json=request_body,
                timeout=self.settings.ai_timeout_seconds or 60,
            )
            response.raise_for_status()
            payload = response.json()

            choice = payload.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content", "")
            tool_calls = message.get("tool_calls", None)
            usage = payload.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            result = {
                "content": content or None,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "provider": normalized,
                "model": model_name,
                "success": True,
                "error": None,
                "tool_calls": tool_calls if tool_calls else None,
                "finish_reason": choice.get("finish_reason", "stop"),
                "http_status": response.status_code,
                "duration_ms": int((time.monotonic() - started_at) * 1000),
                "retry_count": 0,
                "total_tokens": usage.get("total_tokens", input_tokens + output_tokens),
            }
            logger.info(
                "llm_call provider=%s model=%s status=%s duration_ms=%s retry_count=0 prompt_tokens=%s completion_tokens=%s total_tokens=%s",
                normalized, model_name, response.status_code, result["duration_ms"], input_tokens, output_tokens, result["total_tokens"],
            )
            return result
        except Exception as exc:
            status_code = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            duration_ms = int((time.monotonic() - started_at) * 1000)
            logger.error(
                "llm_call provider=%s model=%s status=%s duration_ms=%s retry_count=0 prompt_tokens=0 completion_tokens=0 error=%s",
                normalized, model_name, status_code or "error", duration_ms, exc,
            )
            return {
                "content": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "provider": normalized,
                "model": model_name,
                "success": False,
                "error": str(exc),
                "tool_calls": None,
                "http_status": status_code,
                "duration_ms": duration_ms,
                "retry_count": 0,
            }

    def _mock_chat(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Mock chat that returns canned responses based on message content.

        When tools are provided and the user content contains search-relevant
        keywords, returns a mock tool_call instead of a direct response.
        """
        user_content = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_content += msg.get("content", "") + " "

        # If tools are available and the request looks search-worthy, return a tool call
        if tools:
            search_tool = next((t for t in tools
                if t.get("type") == "function"
                and t.get("function", {}).get("name") == "search_market_trends"), None)
            if search_tool and self._should_search(user_content, messages):
                return self._mock_tool_call(model_name, search_tool, user_content)

        system_content = ""
        for msg in messages:
            if msg.get("role") == "system":
                system_content = msg.get("content", "")

        mock_response = self._generate_mock_response(system_content, user_content)

        return {
            "content": mock_response,
            "input_tokens": len(user_content) // 4,
            "output_tokens": len(mock_response) // 4,
            "provider": "mock",
            "model": model_name or "mock-product-copy-v1",
            "success": True,
            "error": None,
            "tool_calls": None,
            "finish_reason": "stop",
        }

    @staticmethod
    def _should_search(user_content: str, messages: List[Dict[str, str]]) -> bool:
        """Heuristic: decide whether the mock should simulate a search tool call."""
        content_lower = user_content.lower()
        # Check for market/category context that would warrant search
        search_signals = [
            "市场", "趋势", "热搜", "竞品", "价格带", "search", "trend",
            "品类", "电商", "行情", "调研", "分析",
        ]
        return any(signal in content_lower for signal in search_signals)

    def _mock_tool_call(
        self,
        model_name: str,
        tool_def: Dict[str, Any],
        user_content: str,
    ) -> Dict[str, Any]:
        """Generate a mock tool_call response for testing tool calling flow."""
        # Extract category from user content for the mock tool arguments
        import re
        category = "未分类"
        # Try to find category mentions
        for line in user_content.split("\n"):
            if "分类" in line or "category" in line.lower():
                parts = line.split("：") if "：" in line else line.split(":")
                if len(parts) > 1:
                    category = parts[-1].strip()
                    break

        tool_name = tool_def.get("function", {}).get("name", "search_market_trends")
        mock_args = {
            "category": category,
            "keywords": ["热销", "趋势"],
        }
        # Also try to extract a title-based keyword
        for line in user_content.split("\n"):
            if "标题" in line or "title" in line.lower():
                parts = line.split("：") if "：" in line else line.split(":")
                if len(parts) > 1:
                    kw = parts[-1].strip()
                    if kw and kw not in mock_args["keywords"]:
                        mock_args["keywords"].append(kw)

        return {
            "content": None,
            "input_tokens": len(user_content) // 4,
            "output_tokens": 50,
            "provider": "mock",
            "model": model_name or "mock-product-copy-v1",
            "success": True,
            "error": None,
            "tool_calls": [
                {
                    "id": "mock_call_001",
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(mock_args, ensure_ascii=False),
                    },
                }
            ],
            "finish_reason": "tool_calls",
        }

    def _generate_mock_response(self, system_prompt: str, user_content: str) -> str:
        """Generate a structured mock response based on the prompt context."""
        sys_lower = system_prompt.lower()

        # Orchestrator mock
        if "运营总监" in system_prompt or "orchestrat" in sys_lower:
            return json.dumps({
                "plan": [
                    {"step": "market_research", "description": "分析市场趋势和竞品", "depends_on": []},
                    {"step": "copy_generation", "description": "根据商品信息生成文案", "depends_on": ["market_research"]},
                    {"step": "compliance_review", "description": "检查合规性和风险", "depends_on": ["copy_generation"]},
                    {"step": "style_adaptation", "description": "适配目标平台风格", "depends_on": ["copy_generation"]},
                ],
                "reasoning": "根据任务复杂度，按市场调研→文案生成→合规审查→风格适配的顺序执行",
            }, ensure_ascii=False)

        # Market research mock
        if "市场分析师" in system_prompt or "market research" in sys_lower:
            return json.dumps({
                "status": "failed",
                "trends_summary": "Mock 模式未连接实时搜索，未生成趋势结论。",
                "hot_keywords": [],
                "competitor_price_range": {"low": 0, "mid": 0, "high": 0, "currency": "CNY"},
                "suggestions": ["配置真实搜索服务后再生成市场结论"],
            }, ensure_ascii=False)

        # Copywriter mock
        if "电商文案" in system_prompt or "copywriter" in sys_lower or "资深电商" in system_prompt:
            return json.dumps({
                "titles": [
                    "【商品信息】请核对名称与规格",
                    "商品详情待商家确认",
                    "按真实信息完善后发布",
                ],
                "selling_points": [
                    "商品名称清晰",
                    "规格信息待确认",
                    "使用场景待补充",
                    "价格由商家填写",
                    "服务承诺需核实",
                ],
                "detail_copy": "当前为 Mock 模式。请根据商品真实资料补充特点、规格、用途和售后信息。",
                "short_video_script": "",
                "subtitle": "商品信息待完善",
                "price_suggestion": None,
                "specifications": ["请补充可核验规格"],
                "target_audience": "请根据真实适用范围补充",
                "usage_scenarios": ["请根据真实用途补充"],
                "seo_keywords": [],
                "promotion_copy": "商品信息请以商家最终发布内容为准。",
                "pending_confirmations": ["规格", "适用人群", "服务政策"],
            }, ensure_ascii=False)

        # Reviewer mock
        if "合规审查" in system_prompt or "reviewer" in sys_lower:
            return json.dumps({
                "status": "passed",
                "warnings": [],
                "issues": [],
                "summary": "文案内容基本合规，未发现明显违规问题。建议商家补充认证和检测信息。",
            }, ensure_ascii=False)

        # Style adapter mock
        if "风格专家" in system_prompt or "style" in sys_lower or "视觉" in system_prompt:
            return json.dumps({
                "adapted_title": "【商品信息】请核对名称与规格",
                "adapted_selling_points": [
                    "信息清晰展示",
                    "规格需要核实",
                    "优惠以实际设置为准",
                ],
                "adapted_detail": "当前为 Mock 风格预览，不包含销量、认证、服务或折扣承诺。",
                "visual_params": {
                    "color_scheme": "warm-red",
                    "layout": "emotion-driven",
                    "font_style": "bold-highlight",
                },
            }, ensure_ascii=False)

        # Default mock response
        return json.dumps({
            "response": "Mock agent response for testing purposes.",
            "note": "Configure a real AI provider for production use.",
        }, ensure_ascii=False)
