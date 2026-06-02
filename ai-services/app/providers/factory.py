from typing import Dict, List

from app.core.config import Settings
from app.models.responses import AiModelOptionResponse
from app.providers.base import ProductCopyProvider
from app.providers.mock_provider import MockProductCopyProvider
from app.providers.openai_compatible_provider import OpenAICompatibleProvider


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
