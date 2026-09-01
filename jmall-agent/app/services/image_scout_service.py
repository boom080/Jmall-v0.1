"""Image Scout query building, safety filtering, and risk labeling."""

import asyncio
import hashlib
import ipaddress
import re
import socket
import time
from typing import Iterable, List, Optional
from urllib.parse import urlparse

from app.services.input_assessment_service import assess_input_at_boundary
from app.core.metrics import record_image_search
from app.models.agent_models import InputAssessment, ProductInfoRequest
from app.models.image_models import (
    ImageCandidate,
    ImageCandidatesRequest,
    ImageCandidatesResponse,
)
from app.providers.image_search import (
    ImageSearchError,
    ImageSearchProvider,
    ImageSearchUnavailable,
    RawImageCandidate,
)


_BLOCKED_HOST_SUFFIXES = (".local", ".internal", ".localhost", ".home", ".lan")
_WATERMARK_MARKERS = ("watermark", "水印", "带水印")
_BRAND_MARKERS = ("logo", "品牌标志", "商标")
_MARKETPLACE_HOST_MARKERS = (
    "taobao.", "tmall.", "jd.", "pinduoduo.", "suning.", "amazon.",
)


class ImageScoutService:
    """Run Image Scout only after the deterministic product-input gate passes."""

    def __init__(
        self,
        provider: ImageSearchProvider,
        *,
        resolve_dns: bool = True,
        dns_timeout_seconds: float = 0.8,
    ) -> None:
        self.provider = provider
        self.resolve_dns = resolve_dns
        self.dns_timeout_seconds = dns_timeout_seconds

    async def find_candidates(
        self, request: ImageCandidatesRequest
    ) -> ImageCandidatesResponse:
        assessment = InputAssessment.model_validate(
            assess_input_at_boundary(request.product_info.model_dump(), "image")
        )
        if not assessment.ready:
            record_image_search(
                provider=self.provider.name,
                status="needs_input",
                duration_seconds=0.0,
                candidate_count=0,
            )
            return ImageCandidatesResponse(
                status="needs_input",
                input_assessment=assessment,
                message="商品信息尚不完整，未启动图片搜索",
            )

        query = build_image_query(request.product_info)
        started_at = time.perf_counter()
        try:
            raw_candidates = await self.provider.search(query, limit=12)
            candidates = await self._normalize_candidates(raw_candidates)
            status = "ready" if candidates else "no_results"
            message = "" if candidates else "没有找到来源完整且可安全展示的相关图片"
        except ImageSearchUnavailable as exc:
            candidates = []
            status = "provider_unavailable"
            message = str(exc)
        except ImageSearchError as exc:
            candidates = []
            status = "provider_error"
            message = str(exc)
        except Exception:
            candidates = []
            status = "provider_error"
            message = "图片检索暂时不可用，请稍后重试或上传自有图片"

        record_image_search(
            provider=self.provider.name,
            status=status,
            duration_seconds=time.perf_counter() - started_at,
            candidate_count=len(candidates),
        )
        return ImageCandidatesResponse(
            status=status,
            query=query,
            provider=self.provider.name,
            candidates=candidates,
            input_assessment=assessment,
            message=message,
        )

    async def _normalize_candidates(
        self, raw_candidates: Iterable[RawImageCandidate]
    ) -> List[ImageCandidate]:
        candidates: List[ImageCandidate] = []
        seen_urls = set()
        host_safety_cache: dict[str, bool] = {}
        for raw in raw_candidates:
            if raw.unsafe or raw.original_url in seen_urls:
                continue
            urls = (raw.thumbnail_url, raw.original_url, raw.source_page_url)
            if not all(is_safe_public_url(url) for url in urls):
                continue
            if self.resolve_dns and not all(
                await asyncio.gather(
                    *(self._url_resolves_public(url, host_safety_cache) for url in urls)
                )
            ):
                continue
            seen_urls.add(raw.original_url)
            source_name = raw.source_name or (urlparse(raw.source_page_url).hostname or "来源网站")
            risk_flags, risk_reasons = assess_image_risks(raw)
            candidates.append(
                ImageCandidate(
                    candidate_id=hashlib.sha256(raw.original_url.encode("utf-8")).hexdigest()[:16],
                    title=raw.title,
                    thumbnail_url=raw.thumbnail_url,
                    original_url=raw.original_url,
                    source_page_url=raw.source_page_url,
                    source_name=source_name,
                    author=source_name,
                    width=raw.width,
                    height=raw.height,
                    risk_flags=risk_flags,
                    risk_reasons=risk_reasons,
                )
            )
            if len(candidates) >= 3:
                break
        return candidates

    async def _url_resolves_public(
        self,
        value: str,
        cache: dict[str, bool],
    ) -> bool:
        hostname = (urlparse(value).hostname or "").rstrip(".").lower()
        if hostname in cache:
            return cache[hostname]
        try:
            address = ipaddress.ip_address(hostname)
            result = address.is_global
        except ValueError:
            try:
                loop = asyncio.get_running_loop()
                records = await asyncio.wait_for(
                    loop.getaddrinfo(hostname, None, type=socket.SOCK_STREAM),
                    timeout=self.dns_timeout_seconds,
                )
                addresses = {
                    record[4][0].split("%", 1)[0]
                    for record in records
                    if record and len(record) > 4 and record[4]
                }
                result = bool(addresses) and all(
                    ipaddress.ip_address(address).is_global for address in addresses
                )
            except (OSError, ValueError, asyncio.TimeoutError):
                result = False
        cache[hostname] = result
        return result


def build_image_query(product: ProductInfoRequest) -> str:
    """Build a compact query from the latest AI-enriched, merchant-visible draft."""

    def fragments(value: str, *, limit: int) -> List[str]:
        return [
            part.strip()[:48]
            for part in re.split(r"[,，;；。\n]+", value or "")
            if part.strip()
        ][:limit]

    parts = [
        product.title,
        product.category,
        *fragments(product.subtitle or "", limit=2),
        *fragments(product.specifications or "", limit=3),
        *(product.seo_keywords or [])[:4],
        *fragments(product.target_audience or "", limit=1),
        *fragments(product.usage_scenarios or "", limit=1),
    ]
    unique_parts: List[str] = []
    seen = set()
    for value in parts:
        normalized = re.sub(r"\s+", " ", value).strip(" ,，;；。")
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique_parts.append(normalized)
    suffix = " 商品实物图"
    body = " ".join(unique_parts)[:220 - len(suffix)].rstrip()
    return f"{body}{suffix}".strip()


def is_safe_public_url(value: str) -> bool:
    """Reject non-web, credentialed, local, and literal private-network URLs."""

    try:
        if not isinstance(value, str) or len(value) > 2048:
            return False
        if any(character.isspace() or ord(character) < 32 for character in value):
            return False
        parsed = urlparse(value)
        hostname = (parsed.hostname or "").rstrip(".").lower()
        if parsed.scheme != "https" or not hostname:
            return False
        # Accessing .port validates malformed and out-of-range ports.
        parsed.port
        if parsed.username is not None or parsed.password is not None:
            return False
        if hostname == "localhost" or hostname.endswith(_BLOCKED_HOST_SUFFIXES):
            return False
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            return True
        return address.is_global
    except (TypeError, ValueError):
        return False


def assess_image_risks(raw: RawImageCandidate) -> tuple[List[str], List[str]]:
    """Use only metadata heuristics; do not alter or claim rights to the image."""

    flags = ["license_unverified", "visual_risk_unverified"]
    reasons = [
        "图片使用权未经 Jmall 核验，请自行确认",
        "系统只检查来源元数据，请人工查看水印、品牌和内容风险",
    ]
    metadata = " ".join(
        [raw.title, raw.source_name, raw.original_url, raw.source_page_url]
    ).casefold()
    if any(marker in metadata for marker in _WATERMARK_MARKERS):
        flags.append("possible_watermark")
        reasons.append("标题或链接信息提示图片可能带有水印")
    source_host = (urlparse(raw.source_page_url).hostname or "").casefold()
    if any(marker in metadata for marker in _BRAND_MARKERS) or any(
        marker in source_host for marker in _MARKETPLACE_HOST_MARKERS
    ):
        flags.append("possible_competitor_brand")
        reasons.append("来源或标题可能包含第三方品牌信息")
    if raw.width and raw.height and (
        min(raw.width, raw.height) < 600 or raw.width * raw.height < 360_000
    ):
        flags.append("low_resolution")
        reasons.append(f"原图分辨率仅 {raw.width}×{raw.height}")
    elif not raw.width or not raw.height:
        flags.append("resolution_unknown")
        reasons.append("搜索结果未提供原图分辨率，请自行检查清晰度")
    return flags, reasons
