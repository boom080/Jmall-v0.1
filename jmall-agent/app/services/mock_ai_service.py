from app.clients.mock_provider_client import MockProviderClient
from app.models.requests import ProductCopyRequest
from app.models.responses import ProductCopyResponse


class MockAiService:
    def __init__(self, provider_client: MockProviderClient) -> None:
        self.provider_client = provider_client

    def generate_product_copy(self, request: ProductCopyRequest) -> ProductCopyResponse:
        return self.provider_client.generate_product_copy(
            title=request.title,
            category=request.category,
            selling_points=request.sellingPoints,
            tone=request.tone,
        )
