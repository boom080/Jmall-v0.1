from app.langchain_flows.product_copy_graph import ProductCopyLangGraphFlow
from app.models.requests import ProductCopyRequest
from app.models.responses import ProductCopyResponse


class ProductCopyWorkflowService:
    def __init__(self, flow: ProductCopyLangGraphFlow) -> None:
        self.flow = flow

    def generate_product_copy(self, request: ProductCopyRequest) -> ProductCopyResponse:
        return self.flow.invoke(request)
