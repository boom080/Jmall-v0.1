from typing import Dict, List

from app.providers.base import ProductCopyProvider


class MockProductCopyProvider(ProductCopyProvider):
    provider_name = "mock"
    mock = True

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
        normalized_tone = (tone or "professional").strip().lower()
        tone_prefix = {
            "professional": "专业推荐",
            "warm": "温和推荐",
            "marketing": "爆款推荐",
            "concise": "简洁推荐",
        }.get(normalized_tone, "智能推荐")

        points = [point.strip() for point in selling_points if point and point.strip()]
        if not points:
            points = ["信息完整", "支持模型切换", "支持知识库增强"]

        highlights = points[:3]
        summary_parts = [f"{title}主打{'、'.join(highlights)}"]
        if prompt_context:
            marker = "【电商知识库参考资料】"
            if marker in prompt_context:
                summary_parts.append("已参考知识库写法结构：【电商知识库参考资料】；不将知识库示例参数直接作为当前商品事实。")
            else:
                summary_parts.append("已参考生成任务组织文案结构。")
        summary_parts.append("合规风险提醒：未提供认证、保修、适用人数、价格活动等证据时不生成确定承诺。")
        summary_parts.append(f"当前结果由 {model_name or 'mock-product-copy-v1'} 规则生成。")

        return {
            "generatedTitle": f"{tone_prefix} | {title} | {category}",
            "highlights": highlights,
            "summary": "，".join(summary_parts),
            "pendingMerchantConfirmations": ["请商家确认是否有认证、保修、适用人数、材质等级、价格活动等补充信息。"],
            "provider": model_name or "mock-product-copy-v1",
            "mock": True,
            "success": True,
            "message": "商品文案生成成功（Mock/LangGraph）",
        }
