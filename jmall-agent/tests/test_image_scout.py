"""Tests for the v0.2 Image Scout candidate flow."""

import asyncio
import socket
from typing import List
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.images import get_image_scout_service
from app.main import app
from app.models.image_models import ImageCandidatesRequest
from app.models.agent_models import ProductInfoRequest
from app.providers.image_search import (
    ImageSearchError,
    ImageSearchUnavailable,
    QwenWebImagesProvider,
    RawImageCandidate,
    SerpApiGoogleImagesProvider,
    create_image_search_provider,
)
from app.core.config import Settings
from app.services.image_scout_service import (
    ImageScoutService,
    build_image_query,
    is_safe_public_url,
)


def _ready_request() -> ImageCandidatesRequest:
    return ImageCandidatesRequest(
        product_info=ProductInfoRequest(
            title="轻量保温杯",
            category="家居日用",
            description="食品级 304 不锈钢，500ml，杯盖可拆洗，适合通勤",
            specifications="食品级 304 不锈钢；500ml；12 小时保温",
            target_audience="学生和上班族",
            usage_scenarios="日常通勤",
            subtitle="500ml 可拆洗杯盖，适合日常通勤",
            seo_keywords=["轻量保温杯 通勤", "304 保温杯"],
        )
    )


class FakeProvider:
    name = "fake_google_images"

    def __init__(self, results: List[RawImageCandidate]) -> None:
        self.results = results
        self.calls = 0
        self.last_query = ""

    async def search(self, query: str, limit: int = 12):
        self.calls += 1
        self.last_query = query
        return self.results[:limit]


class FailingProvider:
    name = "failing_google_images"

    async def search(self, query: str, limit: int = 12):
        raise ImageSearchError("上游限流")


class UnavailableProvider:
    name = "unavailable_google_images"

    async def search(self, query: str, limit: int = 12):
        raise ImageSearchUnavailable("图片检索尚未配置")


def _raw(index: int, **overrides) -> RawImageCandidate:
    values = {
        "title": f"304 保温杯商品图 {index}",
        "thumbnail_url": f"https://thumbs.example.com/cup-{index}.jpg",
        "original_url": f"https://images.example.com/cup-{index}.jpg",
        "source_page_url": f"https://publisher.example.com/products/cup-{index}",
        "source_name": "Example Publisher",
        "width": 1200,
        "height": 1200,
        "unsafe": False,
    }
    values.update(overrides)
    return RawImageCandidate(**values)


def test_incomplete_input_does_not_call_provider():
    provider = FakeProvider([_raw(1)])
    service = ImageScoutService(provider, resolve_dns=False)
    request = ImageCandidatesRequest(
        product_info=ProductInfoRequest(title="保温杯", category="家居日用")
    )

    response = asyncio.run(service.find_candidates(request))

    assert response.status == "needs_input"
    assert response.candidates == []
    assert response.input_assessment.ready is False
    assert provider.calls == 0


def test_returns_at_most_three_safe_unique_candidates_with_sources():
    duplicate = _raw(4, original_url="https://images.example.com/cup-1.jpg")
    provider = FakeProvider(
        [
            _raw(1),
            _raw(2, width=400, height=400),
            _raw(3, title="带 watermark 和 logo 的保温杯"),
            duplicate,
            _raw(5, original_url="http://127.0.0.1/private.jpg"),
        ]
    )
    service = ImageScoutService(provider, resolve_dns=False)

    response = asyncio.run(service.find_candidates(_ready_request()))

    assert response.status == "ready"
    assert len(response.candidates) == 3
    assert provider.calls == 1
    assert "轻量保温杯" in provider.last_query
    assert "500ml" in provider.last_query
    assert len({item.original_url for item in response.candidates}) == 3
    assert all(item.source_page_url for item in response.candidates)
    assert all("license_unverified" in item.risk_flags for item in response.candidates)
    assert "low_resolution" in response.candidates[1].risk_flags
    assert "possible_watermark" in response.candidates[2].risk_flags
    assert "possible_competitor_brand" in response.candidates[2].risk_flags


def test_provider_failure_is_returned_as_structured_status():
    response = asyncio.run(
        ImageScoutService(FailingProvider(), resolve_dns=False).find_candidates(_ready_request())
    )

    assert response.status == "provider_error"
    assert response.candidates == []
    assert "上游限流" in response.message


def test_provider_unavailable_is_returned_as_structured_status():
    response = asyncio.run(
        ImageScoutService(UnavailableProvider(), resolve_dns=False).find_candidates(_ready_request())
    )

    assert response.status == "provider_unavailable"
    assert response.candidates == []
    assert response.provider == "unavailable_google_images"
    assert response.message == "图片检索尚未配置"


def test_empty_and_unsafe_provider_results_do_not_get_padded():
    provider = FakeProvider([_raw(1, unsafe=True)])

    response = asyncio.run(
        ImageScoutService(provider, resolve_dns=False).find_candidates(_ready_request())
    )

    assert response.status == "no_results"
    assert response.candidates == []
    assert provider.calls == 1


def test_public_url_guard_rejects_local_and_non_web_targets():
    assert is_safe_public_url("https://images.example.com/a.jpg") is True
    assert is_safe_public_url("http://images.example.com/a.jpg") is False
    assert is_safe_public_url("http://127.0.0.1/a.jpg") is False
    assert is_safe_public_url("http://[::1]/a.jpg") is False
    assert is_safe_public_url("http://service.internal/a.jpg") is False
    assert is_safe_public_url("https://user:pass@example.com/a.jpg") is False
    assert is_safe_public_url("file:///etc/passwd") is False
    assert is_safe_public_url("data:image/png;base64,AAAA") is False
    assert is_safe_public_url("https://images.example.com/has space.jpg") is False
    assert is_safe_public_url("https://images.example.com/" + "a" * 2049) is False
    assert is_safe_public_url("https://images.example.com:bad/a.jpg") is False
    assert is_safe_public_url("https://images.example.com:99999/a.jpg") is False


def test_dns_resolution_rejects_hostname_that_points_to_private_network():
    provider = FakeProvider([_raw(1)])
    service = ImageScoutService(provider, resolve_dns=True)
    private_record = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))
    ]

    with patch("socket.getaddrinfo", return_value=private_record):
        response = asyncio.run(service.find_candidates(_ready_request()))

    assert response.status == "no_results"
    assert response.candidates == []


def test_query_is_compact_and_uses_confirmed_product_fields():
    query = build_image_query(_ready_request().product_info)

    assert "轻量保温杯" in query
    assert "家居日用" in query
    assert "学生和上班族" in query
    assert "500ml 可拆洗杯盖" in query
    assert "轻量保温杯 通勤" in query
    assert query.endswith("商品实物图")
    assert len(query) <= 220
    assert "食品级 304 不锈钢，500ml，杯盖可拆洗" not in query


def test_serpapi_provider_maps_google_image_metadata():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["engine"] == "google_images"
        assert request.url.params["safe"] == "active"
        assert request.url.params["q"] == "保温杯 商品实物图"
        return httpx.Response(
            200,
            json={
                "images_results": [
                    {
                        "title": "保温杯",
                        "thumbnail": "https://thumbs.example.com/cup.jpg",
                        "original": "https://images.example.com/cup.jpg",
                        "link": "https://publisher.example.com/cup",
                        "source": "Publisher",
                        "original_width": 1600,
                        "original_height": 1200,
                        "unsafe": False,
                    }
                ]
            },
        )

    provider = SerpApiGoogleImagesProvider(
        "test-key",
        transport=httpx.MockTransport(handler),
    )
    results = asyncio.run(provider.search("保温杯 商品实物图"))

    assert len(results) == 1
    assert results[0].source_name == "Publisher"
    assert results[0].width == 1600
    assert results[0].height == 1200


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"error": "Invalid API key: test-key"}, "拒绝请求"),
        (["not", "an", "object"], "无效数据"),
    ],
)
def test_serpapi_sanitizes_invalid_upstream_payloads(payload, message):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    provider = SerpApiGoogleImagesProvider(
        "test-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ImageSearchError, match=message) as error:
        asyncio.run(provider.search("保温杯"))
    assert "test-key" not in str(error.value)


def test_serpapi_without_key_fails_before_any_http_request():
    provider = SerpApiGoogleImagesProvider("")

    with pytest.raises(ImageSearchUnavailable, match="SERPAPI_API_KEY"):
        asyncio.run(provider.search("保温杯"))


def test_serpapi_refuses_to_send_key_over_plain_http():
    provider = SerpApiGoogleImagesProvider(
        "test-key",
        endpoint="http://serpapi.example.com/search.json",
    )

    with pytest.raises(ImageSearchUnavailable, match="必须使用 HTTPS"):
        asyncio.run(provider.search("保温杯"))


def test_serpapi_refuses_to_send_key_to_untrusted_host():
    provider = SerpApiGoogleImagesProvider(
        "test-key",
        endpoint="https://search-proxy.example.com/search.json",
    )

    with pytest.raises(ImageSearchUnavailable, match="serpapi.com"):
        asyncio.run(provider.search("保温杯"))


def test_qwen_provider_requests_mixed_web_images_and_maps_html():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == (
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        )
        assert request.headers["Authorization"] == "Bearer test-qwen-key"
        payload = __import__("json").loads(request.content)
        assert payload["model"] == "qwen-plus-latest"
        assert payload["enable_search"] is True
        assert payload["enable_text_image_mixed"] is True
        assert payload["search_options"]["forced_search"] is True
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '<a href="https://shop.example.com/cup">'
                                '<img src="https://img.example.com/cup.jpg" '
                                'alt="304 保温杯" width="1200" height="900"></a>'
                                '<img src="https://img.example.com/cup-2.jpg" alt="杯盖细节">'
                            )
                        }
                    }
                ]
            },
        )

    provider = QwenWebImagesProvider(
        "test-qwen-key",
        model="qwen-plus-latest",
        transport=httpx.MockTransport(handler),
    )

    results = asyncio.run(provider.search("保温杯 商品实物图", limit=3))

    assert len(results) == 2
    assert results[0].source_page_url == "https://shop.example.com/cup"
    assert results[0].original_url == "https://img.example.com/cup.jpg"
    assert results[0].title == "304 保温杯"
    assert results[0].width == 1200
    assert results[1].source_page_url == results[1].original_url


def test_qwen_provider_accepts_linked_markdown_images_and_deduplicates():
    content = (
        "[![白色保温杯](https://img.example.com/white.jpg)]"
        "(https://source.example.com/white)\n"
        "![白色保温杯](https://img.example.com/white.jpg)\n"
        "![黑色保温杯](https://img.example.com/black.jpg)"
    )

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    provider = QwenWebImagesProvider(
        "test-qwen-key",
        transport=httpx.MockTransport(handler),
    )
    results = asyncio.run(provider.search("保温杯"))

    assert [item.original_url for item in results] == [
        "https://img.example.com/white.jpg",
        "https://img.example.com/black.jpg",
    ]
    assert results[0].source_page_url == "https://source.example.com/white"


def test_qwen_provider_reports_unsupported_mixed_output_without_leaking_key():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"message": "invalid test-qwen-key"})

    provider = QwenWebImagesProvider(
        "test-qwen-key",
        model="qwen3.7-flash",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ImageSearchError, match="可能不支持图文混排") as error:
        asyncio.run(provider.search("保温杯"))
    assert "test-qwen-key" not in str(error.value)


def test_qwen_provider_reports_text_only_result_as_capability_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": "已联网检索到若干保温杯商品信息。"}}
                ]
            },
        )

    provider = QwenWebImagesProvider(
        "test-qwen-key",
        model="qwen3.7-flash",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ImageSearchError, match="没有返回可展示图片"):
        asyncio.run(provider.search("保温杯"))


@pytest.mark.parametrize(
    "base_url",
    [
        "http://dashscope.aliyuncs.com/compatible-mode/v1",
        "https://qwen-proxy.example.com/compatible-mode/v1",
    ],
)
def test_qwen_provider_refuses_to_send_key_to_unsafe_endpoint(base_url):
    provider = QwenWebImagesProvider("test-qwen-key", base_url=base_url)

    with pytest.raises(ImageSearchUnavailable):
        asyncio.run(provider.search("保温杯"))


def test_image_provider_factory_uses_qwen_model_from_settings():
    settings = Settings(
        image_search_provider="qwen",
        image_search_model="qwen-plus-latest",
        qwen_api_key="configured-key",
        _env_file=None,
    )

    provider = create_image_search_provider(settings)

    assert isinstance(provider, QwenWebImagesProvider)
    assert provider.model == "qwen-plus-latest"


def test_image_candidates_api_uses_dependency_and_returns_contract():
    service = ImageScoutService(FakeProvider([_raw(1)]), resolve_dns=False)
    app.dependency_overrides[get_image_scout_service] = lambda: service
    client = TestClient(app)
    try:
        response = client.post(
            "/api/agent/images/candidates",
            json={
                "product_info": {
                    "title": "轻量保温杯",
                    "category": "家居日用",
                    "description": "食品级 304 不锈钢，500ml，杯盖可拆洗",
                    "specifications": "304 不锈钢；500ml；12 小时保温",
                    "target_audience": "学生和上班族",
                }
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert len(body["candidates"]) == 1
    assert body["candidates"][0]["author"] == "Example Publisher"
    assert "不保证图片使用权" in body["disclaimer"]
