import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_shopper_intent_service
from app.api.shopper import router
from app.core.config import Settings
from app.models.requests import ShopperIntentRequest
from app.models.responses import ShopperIntentResponse
from app.services.shopper_intent_service import ShopperIntentService


class StubProviderFactory:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


def real_tier_settings(**overrides):
    values = {
        "_env_file": None,
        "ai_provider": "qwen",
        "qwen_api_key": "configured-for-test",
        "agent_cheap_provider": "qwen",
        "agent_cheap_model": "qwen-turbo",
        "SHOPPER_INTENT_TIMEOUT_SECONDS": 4,
    }
    values.update(overrides)
    return Settings(**values)


def test_fast_model_expands_vague_play_intent():
    factory = StubProviderFactory({
        "success": True,
        "content": json.dumps({
            "normalizedQuery": "适合娱乐和游戏的数码产品",
            "intentSummary": "想找能玩的娱乐数码",
            "keywords": ["游戏", "娱乐", "智能"],
            "categoryHints": ["手机数码"],
            "useCases": ["休闲娱乐"],
            "maxPriceCents": None,
            "sortBy": "relevance",
            "intents": ["play", "digital"],
        }, ensure_ascii=False),
    })
    service = ShopperIntentService(real_tier_settings(), factory)

    result = service.analyze(ShopperIntentRequest(query="想找点玩的"))

    assert result.source == "model"
    assert result.categoryHints == ["手机数码"]
    assert "游戏" in result.keywords
    assert factory.calls[0]["model_name"] == "qwen-turbo"
    assert factory.calls[0]["temperature"] == 0.0
    assert factory.calls[0]["max_tokens"] == 220
    assert factory.calls[0]["timeout_seconds"] == 4


def test_invalid_model_output_uses_bounded_local_fallback():
    factory = StubProviderFactory({"success": True, "content": "not-json"})
    service = ShopperIntentService(real_tier_settings(), factory)

    result = service.analyze(ShopperIntentRequest(query="找点玩的"))

    assert result.source == "fallback"
    assert result.categoryHints == ["手机数码"]
    assert result.keywords[:2] == ["游戏", "娱乐"]


def test_model_zero_budget_is_treated_as_no_budget():
    factory = StubProviderFactory({
        "success": True,
        "content": json.dumps({
            "normalizedQuery": "玩的",
            "intentSummary": "寻找娱乐或休闲类商品",
            "keywords": ["玩", "娱乐", "休闲"],
            "categoryHints": [],
            "useCases": ["娱乐", "休闲"],
            "maxPriceCents": 0,
            "sortBy": "relevance",
            "intents": ["play"],
        }, ensure_ascii=False),
    })
    service = ShopperIntentService(real_tier_settings(), factory)

    result = service.analyze(ShopperIntentRequest(query="玩的"))

    assert result.source == "model"
    assert result.maxPriceCents is None


def test_failed_model_preserves_budget_for_local_ranking():
    factory = StubProviderFactory({"success": False, "content": None, "error": "timeout"})
    service = ShopperIntentService(real_tier_settings(), factory)

    result = service.analyze(ShopperIntentRequest(query="想买 100 元以内的零食"))

    assert result.source == "fallback"
    assert result.maxPriceCents == 10_000
    assert result.categoryHints == ["食品饮料"]


def test_shopper_intent_api_validates_and_returns_response():
    class StubService:
        def analyze(self, request):
            assert request.query == "玩的"
            return ShopperIntentResponse(
                normalizedQuery="娱乐 手机数码",
                intentSummary="娱乐数码",
                keywords=["娱乐"],
                categoryHints=["手机数码"],
                useCases=["休闲娱乐"],
                provider="qwen",
                model="qwen-turbo",
                source="model",
            )

    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_shopper_intent_service] = lambda: StubService()
    client = TestClient(app)

    response = client.post("/api/shopper/intent", json={"query": " 玩的 "})

    assert response.status_code == 200
    assert response.json()["categoryHints"] == ["手机数码"]
    assert response.json()["source"] == "model"

    invalid = client.post("/api/shopper/intent", json={"query": "   "})
    assert invalid.status_code == 422
