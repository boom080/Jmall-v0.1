from typing import List

from app.models.responses import ProductCopyResponse


class MockProviderClient:
    """Deterministic mock provider for future AI provider replacement."""

    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name

    def generate_product_copy(
        self,
        title: str,
        category: str,
        selling_points: List[str],
        tone: str,
    ) -> ProductCopyResponse:
        normalized_tone = (tone or "professional").strip().lower()
        tone_prefix = {
            "professional": "专业推荐",
            "warm": "温和推荐",
            "marketing": "爆款推荐",
            "concise": "简洁推荐",
        }.get(normalized_tone, "智能推荐")

        points = [point.strip() for point in selling_points if point and point.strip()]
        if not points:
            points = ["信息完整", "适合本地联调演示", "可平滑替换真实模型"]

        highlights = points[:3]
        generated_title = f"{tone_prefix} | {title} | {category}"
        summary = (
            f"{title}主打{'、'.join(highlights)}，"
            f"适合关注{category}品类的用户，当前结果由 Mock 规则生成。"
        )

        return ProductCopyResponse(
            generatedTitle=generated_title,
            highlights=highlights,
            summary=summary,
            provider=self.provider_name,
            mock=True,
            success=True,
            message="商品文案生成成功（Mock）",
        )
