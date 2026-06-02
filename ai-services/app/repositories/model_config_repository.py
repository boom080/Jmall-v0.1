from typing import List

from app.models.responses import AiModelOptionResponse
from app.providers.factory import ProviderFactory


class ModelConfigRepository:
    def __init__(self, provider_factory: ProviderFactory) -> None:
        self.provider_factory = provider_factory

    def list_models(self) -> List[AiModelOptionResponse]:
        return self.provider_factory.list_available_models()
