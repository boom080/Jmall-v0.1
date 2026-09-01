"""Image search provider abstraction and source-backed implementations."""

from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
import re
from typing import Any, List, Optional, Protocol
from urllib.parse import urlparse

import httpx

from app.core.config import Settings


class ImageSearchError(RuntimeError):
    """Base error for an upstream image search failure."""


class ImageSearchUnavailable(ImageSearchError):
    """Raised when no real image search provider is configured."""


@dataclass(frozen=True)
class RawImageCandidate:
    """Provider-neutral image metadata before product risk processing."""

    title: str
    thumbnail_url: str
    original_url: str
    source_page_url: str
    source_name: str
    width: Optional[int] = None
    height: Optional[int] = None
    unsafe: bool = False


class ImageSearchProvider(Protocol):
    name: str

    async def search(self, query: str, limit: int = 12) -> List[RawImageCandidate]:
        """Return provider-ranked image results."""


class UnavailableImageSearchProvider:
    name = "unavailable"

    def __init__(self, reason: str) -> None:
        self.reason = reason

    async def search(self, query: str, limit: int = 12) -> List[RawImageCandidate]:
        raise ImageSearchUnavailable(self.reason)


class SerpApiGoogleImagesProvider:
    """Retrieve structured Google Images results through SerpAPI."""

    name = "serpapi_google_images"

    def __init__(
        self,
        api_key: str,
        *,
        endpoint: str = "https://serpapi.com/search.json",
        timeout_seconds: float = 7.5,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        self.api_key = api_key.strip()
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def search(self, query: str, limit: int = 12) -> List[RawImageCandidate]:
        if not self.api_key:
            raise ImageSearchUnavailable("SERPAPI_API_KEY 未配置")
        parsed_endpoint = urlparse(self.endpoint)
        provider_host = (parsed_endpoint.hostname or "").lower()
        if parsed_endpoint.scheme != "https":
            raise ImageSearchUnavailable("SERPAPI_BASE_URL 必须使用 HTTPS")
        if provider_host != "serpapi.com" and not provider_host.endswith(".serpapi.com"):
            raise ImageSearchUnavailable("SERPAPI_BASE_URL 必须指向 serpapi.com")

        params = {
            "engine": "google_images",
            "q": query,
            "api_key": self.api_key,
            "safe": "active",
            "hl": "zh-cn",
            "gl": "cn",
            "ijn": 0,
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                response = await client.get(self.endpoint, params=params)
                response.raise_for_status()
                payload: Any = response.json()
        except httpx.TimeoutException as exc:
            raise ImageSearchError("Google 图片检索超时") from exc
        except httpx.HTTPStatusError as exc:
            raise ImageSearchError(
                f"Google 图片检索返回 HTTP {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ImageSearchError("Google 图片检索网络错误") from exc
        except ValueError as exc:
            raise ImageSearchError("Google 图片检索返回了无效 JSON") from exc

        if not isinstance(payload, dict):
            raise ImageSearchError("Google 图片检索返回了无效数据")
        if payload.get("error"):
            raise ImageSearchError("Google 图片检索服务拒绝请求，请检查 Provider 配置或额度")

        results: List[RawImageCandidate] = []
        for item in payload.get("images_results") or []:
            if not isinstance(item, dict):
                continue
            original = str(item.get("original") or "").strip()
            thumbnail = str(item.get("thumbnail") or "").strip()
            source_page = str(item.get("link") or "").strip()
            if not original or not thumbnail or not source_page:
                continue
            results.append(
                RawImageCandidate(
                    title=str(item.get("title") or "").strip(),
                    thumbnail_url=thumbnail,
                    original_url=original,
                    source_page_url=source_page,
                    source_name=str(item.get("source") or "").strip(),
                    width=_positive_int(item.get("original_width")),
                    height=_positive_int(item.get("original_height")),
                    unsafe=bool(item.get("unsafe", False)),
                )
            )
            if len(results) >= max(1, limit):
                break
        return results


class _QwenImageHtmlParser(HTMLParser):
    """Extract images and an optional enclosing source link from Qwen HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: List[str] = []
        self.images: List[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        attributes = {key.lower(): (value or "") for key, value in attrs}
        if tag.lower() == "a":
            self.links.append(attributes.get("href", "").strip())
            return
        if tag.lower() != "img":
            return
        self.images.append(
            {
                "url": (attributes.get("src") or attributes.get("data-src") or "").strip(),
                "title": attributes.get("alt", "").strip(),
                "source_page": self.links[-1] if self.links else "",
                "width": _positive_int(attributes.get("width")),
                "height": _positive_int(attributes.get("height")),
            }
        )

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.links:
            self.links.pop()


class QwenWebImagesProvider:
    """Use Qwen web search with mixed text/image output for image candidates."""

    name = "qwen_web_images"

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: str = "qwen-plus-latest",
        timeout_seconds: float = 20.0,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model = model.strip()
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def search(self, query: str, limit: int = 12) -> List[RawImageCandidate]:
        if not self.api_key:
            raise ImageSearchUnavailable("JMALL_QWEN_API_KEY 未配置")
        if not self.model:
            raise ImageSearchUnavailable("picture_base 未配置图片搜索模型")
        endpoint = self._endpoint()
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是商品图片检索助手。必须联网寻找与查询准确匹配的真实商品图片，"
                        "不要生成图片，不要编造图片 URL。回复中最多嵌入 6 张候选图片，"
                        "每张图片应有准确的 alt 描述；如能取得来源页面，请用来源链接包裹图片。"
                    ),
                },
                {"role": "user", "content": query},
            ],
            "enable_search": True,
            "enable_text_image_mixed": True,
            "search_options": {
                "forced_search": True,
                "search_strategy": "turbo",
            },
            "enable_thinking": False,
            "temperature": 0.1,
            "max_tokens": 900,
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                )
                response.raise_for_status()
                data: Any = response.json()
        except httpx.TimeoutException as exc:
            raise ImageSearchError("千问图片检索超时") from exc
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code == 400:
                raise ImageSearchError(
                    f"千问图片检索返回 HTTP 400；模型 {self.model} 可能不支持图文混排"
                ) from exc
            raise ImageSearchError(f"千问图片检索返回 HTTP {status_code}") from exc
        except httpx.HTTPError as exc:
            raise ImageSearchError("千问图片检索网络错误") from exc
        except ValueError as exc:
            raise ImageSearchError("千问图片检索返回了无效 JSON") from exc

        content = _qwen_response_content(data)
        if not content:
            raise ImageSearchError("千问图片检索未返回内容")
        candidates = _extract_qwen_image_candidates(content, limit=max(1, limit))
        if not candidates:
            raise ImageSearchError(
                f"千问模型 {self.model} 完成了联网检索，但没有返回可展示图片；"
                "请改用支持图文混排的图片模型"
            )
        return candidates

    def _endpoint(self) -> str:
        parsed = urlparse(self.base_url)
        provider_host = (parsed.hostname or "").lower()
        if parsed.scheme != "https":
            raise ImageSearchUnavailable("QWEN_BASE_URL 必须使用 HTTPS")
        if provider_host != "aliyuncs.com" and not provider_host.endswith(".aliyuncs.com"):
            raise ImageSearchUnavailable("QWEN_BASE_URL 必须指向阿里云 aliyuncs.com")
        if parsed.path.rstrip("/").endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"


def create_image_search_provider(settings: Settings) -> ImageSearchProvider:
    """Build the configured provider without silently returning mock images."""

    provider = (settings.image_search_provider or "").strip().lower()
    if provider in {"qwen", "qwen_web_images", "qwen_images"}:
        if not settings.qwen_api_key.strip():
            return UnavailableImageSearchProvider(
                "图片检索尚未配置：请设置 JMALL_QWEN_API_KEY"
            )
        if not settings.image_search_model.strip():
            return UnavailableImageSearchProvider(
                "图片检索尚未配置：请设置 picture_base"
            )
        return QwenWebImagesProvider(
            settings.qwen_api_key,
            base_url=settings.qwen_base_url,
            model=settings.image_search_model,
            timeout_seconds=settings.image_search_timeout_seconds,
        )
    if provider in {"serpapi", "serpapi_google_images"}:
        if not settings.serpapi_api_key.strip():
            return UnavailableImageSearchProvider(
                "图片检索尚未配置：请设置 SERPAPI_API_KEY"
            )
        return SerpApiGoogleImagesProvider(
            settings.serpapi_api_key,
            endpoint=settings.serpapi_base_url,
            timeout_seconds=settings.image_search_timeout_seconds,
        )
    if provider in {"", "disabled", "none"}:
        return UnavailableImageSearchProvider("图片检索 Provider 未启用")
    return UnavailableImageSearchProvider(
        f"不支持的图片检索 Provider：{settings.image_search_provider}"
    )


def _positive_int(value: Any) -> Optional[int]:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _qwen_response_content(payload: Any) -> str:
    if not isinstance(payload, dict):
        raise ImageSearchError("千问图片检索返回了无效数据")
    output = payload.get("output")
    output = output if isinstance(output, dict) else {}
    choices = payload.get("choices") or output.get("choices") or []
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return ""
    message = choices[0].get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(
            str(item.get("text") or "").strip()
            for item in content
            if isinstance(item, dict) and item.get("text")
        ).strip()
    return ""


def _extract_qwen_image_candidates(content: str, *, limit: int) -> List[RawImageCandidate]:
    parser = _QwenImageHtmlParser()
    parser.feed(content)
    extracted = list(parser.images)

    # Accept both linked and plain Markdown images for compatible gateways.
    for match in re.finditer(
        r"\[!\[(?P<alt>[^\]]*)\]\((?P<image>https://[^\s)]+)\)\]\((?P<page>https://[^\s)]+)\)"
        r"|!\[(?P<plain_alt>[^\]]*)\]\((?P<plain_image>https://[^\s)]+)\)",
        content,
        flags=re.IGNORECASE,
    ):
        image_url = match.group("image") or match.group("plain_image") or ""
        extracted.append(
            {
                "url": image_url,
                "title": match.group("alt") or match.group("plain_alt") or "",
                "source_page": match.group("page") or "",
                "width": None,
                "height": None,
            }
        )

    candidates: List[RawImageCandidate] = []
    seen = set()
    for item in extracted:
        image_url = unescape(str(item.get("url") or "").strip())
        if not image_url or image_url in seen:
            continue
        seen.add(image_url)
        source_page = unescape(str(item.get("source_page") or "").strip())
        if not source_page.startswith("https://"):
            source_page = image_url
        source_name = urlparse(source_page).hostname or "千问联网图片"
        candidates.append(
            RawImageCandidate(
                title=unescape(str(item.get("title") or "").strip()),
                thumbnail_url=image_url,
                original_url=image_url,
                source_page_url=source_page,
                source_name=source_name,
                width=item.get("width"),
                height=item.get("height"),
            )
        )
        if len(candidates) >= limit:
            break
    return candidates
