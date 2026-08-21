import json
from typing import Dict, List

import httpx

from app.providers.base import ProductCopyProvider


class OpenAICompatibleProvider(ProductCopyProvider):
    def __init__(self, provider_name: str, api_key: str, base_url: str) -> None:
        self.provider_name = provider_name
        self.api_key = api_key
        self.base_url = (base_url or "").rstrip("/")
        self.mock = False

    def generate_product_copy(
        self,
        title: str,
        category: str,
        selling_points: List[str],
        tone: str,
        prompt_context: str,
        model_name: str,
        metadata: Dict[str, str],
    ) -> Dict[str, object]:
        if not self.api_key:
            raise RuntimeError(f"{self.provider_name} API Key 未配置")
        if not self.base_url:
            raise RuntimeError(f"{self.provider_name} base_url 未配置")

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key.strip()}"},
            json={
                "model": model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是 Jrunmall 商家端商品运营文案助手。请只输出 JSON，不要输出 Markdown。",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"{prompt_context}\n\n"
                            "请输出 JSON 字段：generatedTitle、highlights、summary、pendingMerchantConfirmations。"
                            "generatedTitle 为商品标题，highlights 为 3-5 条短卖点数组，summary 汇总详情页文案、短视频口播和合规风险提醒。"
                            "pendingMerchantConfirmations 为待商家确认信息数组，填写因商品输入缺证据而不能确定的参数、认证、保修、适用人数、功效或活动信息。"
                        ),
                    },
                ],
                "temperature": 0.4,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        content = (
            payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        parsed = self._parse_model_json(content, title, category, selling_points)
        parsed["provider"] = f"{self.provider_name}:{model_name}"
        parsed["mock"] = False
        parsed["success"] = True
        parsed["message"] = "商品文案生成成功"
        return parsed

    def _parse_model_json(
        self,
        raw: str,
        title: str,
        category: str,
        selling_points: List[str],
    ) -> Dict[str, object]:
        try:
            data = json.loads(self._extract_json(raw))
        except json.JSONDecodeError:
            data = {}
        generated_title = str(data.get("generatedTitle") or f"智能推荐 | {title} | {category}")
        highlights = data.get("highlights")
        if not isinstance(highlights, list):
            highlights = [point for point in selling_points if point][:5]
        normalized_highlights = [str(item).strip() for item in highlights if str(item).strip()][:5]
        if not normalized_highlights:
            normalized_highlights = ["核心卖点清晰", "场景表达完整", "适合电商转化"]
        summary = str(data.get("summary") or raw or "商品文案生成成功")
        pending = data.get("pendingMerchantConfirmations")
        if not isinstance(pending, list):
            pending = []
        normalized_pending = [str(item).strip() for item in pending if str(item).strip()]
        return {
            "generatedTitle": generated_title,
            "highlights": normalized_highlights,
            "summary": summary,
            "pendingMerchantConfirmations": normalized_pending,
        }

    def _extract_json(self, raw: str) -> str:
        if not raw:
            return "{}"
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            return raw[start:end + 1]
        return raw
