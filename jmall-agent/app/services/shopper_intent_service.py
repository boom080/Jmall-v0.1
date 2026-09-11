"""Fast, bounded intent parsing for the shopper assistant."""

from __future__ import annotations

import json
import re
from typing import Any

from app.core.config import Settings
from app.llm.router import LLMRouter
from app.models.requests import ShopperIntentRequest
from app.models.responses import ShopperIntentResponse
from app.providers.factory import ProviderFactory


KNOWN_CATEGORIES = {
    "手机数码",
    "茶叶",
    "厨房电器",
    "服饰鞋包",
    "食品饮料",
    "家居日用",
    "美妆护肤",
    "其他",
}
KNOWN_INTENTS = {
    "commute",
    "gift",
    "digital",
    "food",
    "home",
    "beauty",
    "clothing",
    "play",
    "popular",
    "budget",
}
KNOWN_SORTS = {"relevance", "popularity", "price_asc"}


class ShopperIntentService:
    def __init__(self, settings: Settings, provider_factory: ProviderFactory) -> None:
        self.settings = settings
        self.provider_factory = provider_factory
        self.router = LLMRouter(settings)

    def analyze(self, request: ShopperIntentRequest) -> ShopperIntentResponse:
        provider, model = self.router.route("shopper_intent")
        result = self.provider_factory.chat(
            provider_name=provider,
            model_name=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是电商导购意图解析器。只输出一个 JSON 对象，不要 Markdown。"
                        "把口语、错别字和模糊表达扩展为可检索意图，但不要编造用户没有说的商品属性。"
                        "字段必须为 normalizedQuery、intentSummary、keywords、categoryHints、"
                        "useCases、maxPriceCents、sortBy、intents。"
                        "categoryHints 只能从 手机数码、茶叶、厨房电器、服饰鞋包、食品饮料、"
                        "家居日用、美妆护肤、其他 中选择。"
                        "sortBy 只能是 relevance、popularity、price_asc。"
                        "intents 只能是 commute、gift、digital、food、home、beauty、clothing、"
                        "play、popular、budget。"
                        "例如“想找点玩的”应理解为娱乐/游戏/休闲，可扩展到手机数码；"
                        "“给妈妈买点东西”应保留送礼和目标对象线索。"
                    ),
                },
                {"role": "user", "content": request.query},
            ],
            temperature=0.0,
            max_tokens=220,
            timeout_seconds=self.settings.shopper_intent_timeout_seconds,
        )

        if result.get("success"):
            parsed = self._parse_model_json(result.get("content"))
            if parsed is not None:
                return self._response_from_model(request.query, parsed, provider, model)

        return self._fallback_response(request.query, provider, model)

    def _parse_model_json(self, content: Any) -> dict[str, Any] | None:
        text = str(content or "").strip()
        if not text:
            return None
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            payload = json.loads(text[start : end + 1])
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def _response_from_model(
        self,
        query: str,
        payload: dict[str, Any],
        provider: str,
        model: str,
    ) -> ShopperIntentResponse:
        keywords = self._clean_list(payload.get("keywords"), 8)
        use_cases = self._clean_list(payload.get("useCases"), 5)
        categories = [
            item for item in self._clean_list(payload.get("categoryHints"), 4)
            if item in KNOWN_CATEGORIES
        ]
        intents = [
            item for item in self._clean_list(payload.get("intents"), 6)
            if item in KNOWN_INTENTS
        ]
        max_price = self._clean_price(payload.get("maxPriceCents"))
        sort_by = str(payload.get("sortBy") or "relevance").strip()
        if sort_by not in KNOWN_SORTS:
            sort_by = "relevance"
        normalized = self._clean_text(payload.get("normalizedQuery"), 100) or query
        summary = self._clean_text(payload.get("intentSummary"), 80)
        if not summary:
            summary = "、".join([*categories, *keywords[:3]]) or "按你的描述找好物"

        if not any((keywords, use_cases, categories, intents, max_price is not None)):
            return self._fallback_response(query, provider, model)

        return ShopperIntentResponse(
            normalizedQuery=normalized,
            intentSummary=summary,
            keywords=keywords,
            categoryHints=categories,
            useCases=use_cases,
            maxPriceCents=max_price,
            sortBy=sort_by,
            provider=provider,
            model=model,
            source="model",
        )

    def _fallback_response(self, query: str, provider: str, model: str) -> ShopperIntentResponse:
        compact = re.sub(r"\s+", "", query.lower())
        keywords: list[str] = []
        categories: list[str] = []
        use_cases: list[str] = []
        intents: list[str] = []

        rules = [
            (("玩", "游戏", "娱乐", "休闲"), ["游戏", "娱乐", "智能"], ["手机数码"], ["娱乐"], "play"),
            (("吃", "零食", "早餐"), ["食品", "零食"], ["食品饮料"], ["日常食用"], "food"),
            (("喝", "饮料", "茶", "咖啡", "牛奶"), ["饮料", "茶", "牛奶"], ["食品饮料", "茶叶"], ["日常饮用"], "food"),
            (("穿", "衣服", "鞋", "包"), ["穿搭", "服饰", "鞋包"], ["服饰鞋包"], ["日常穿搭"], "clothing"),
            (("家里", "家用", "做饭", "厨房"), ["家用", "厨房"], ["家居日用", "厨房电器"], ["居家"], "home"),
            (("送", "礼物", "礼盒"), ["送礼", "礼盒"], [], ["送礼"], "gift"),
            (("通勤", "上班", "办公"), ["通勤", "便携", "办公"], [], ["通勤"], "commute"),
            (("热门", "人气", "爆款"), ["人气", "热门"], [], [], "popular"),
        ]
        for needles, extra_keywords, extra_categories, extra_cases, intent in rules:
            if any(needle in compact for needle in needles):
                keywords.extend(extra_keywords)
                categories.extend(extra_categories)
                use_cases.extend(extra_cases)
                intents.append(intent)

        budget = self._parse_budget(query)
        if budget is not None:
            intents.append("budget")
        sort_by = "popularity" if "popular" in intents else "price_asc" if any(word in compact for word in ("便宜", "实惠", "低价")) else "relevance"
        if not keywords:
            keywords = [part for part in re.split(r"[\s,，。！？、；;:：/\\|]+", query) if len(part.strip()) > 1][:5]

        categories = list(dict.fromkeys(categories))
        keywords = list(dict.fromkeys(keywords))
        use_cases = list(dict.fromkeys(use_cases))
        summary = "、".join([*use_cases, *categories, *keywords[:2]]) or "按你的描述找好物"
        return ShopperIntentResponse(
            normalizedQuery=" ".join([query, *categories, *keywords]),
            intentSummary=summary,
            keywords=keywords,
            categoryHints=categories,
            useCases=use_cases,
            maxPriceCents=budget,
            sortBy=sort_by,
            provider=provider,
            model=model,
            source="fallback",
        )

    @staticmethod
    def _clean_text(value: Any, max_length: int) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()[:max_length]

    @classmethod
    def _clean_list(cls, value: Any, limit: int) -> list[str]:
        if not isinstance(value, list):
            return []
        cleaned = [cls._clean_text(item, 24) for item in value]
        return list(dict.fromkeys(item for item in cleaned if item))[:limit]

    @staticmethod
    def _clean_price(value: Any) -> int | None:
        if value is None or value == "":
            return None
        try:
            price = int(float(value))
        except (TypeError, ValueError):
            return None
        return price if 0 < price <= 100_000_000 else None

    @staticmethod
    def _parse_budget(query: str) -> int | None:
        compact = re.sub(r"\s+", "", query)
        chinese_budgets = {"百元": 10_000, "一百元": 10_000, "两百元": 20_000, "二百元": 20_000, "三百元": 30_000}
        for marker, cents in chinese_budgets.items():
            if marker in compact:
                return cents
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:元|块|¥|￥)", query)
        if not match:
            match = re.search(r"(?:预算|不超过|低于|少于|以内|以下)\s*(\d+(?:\.\d+)?)", query)
        if not match:
            return None
        return max(0, round(float(match.group(1)) * 100))
