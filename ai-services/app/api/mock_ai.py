from fastapi import APIRouter, Depends

from app.api.dependencies import get_product_copy_workflow_service
from app.models.requests import ProductCopyRequest
from app.models.responses import ProductCopyResponse
from app.services.product_copy_workflow_service import ProductCopyWorkflowService

router = APIRouter(prefix="/mock", tags=["mock-ai"])


@router.post("/product-copy", response_model=ProductCopyResponse)
def product_copy(
    request: ProductCopyRequest,
    service: ProductCopyWorkflowService = Depends(get_product_copy_workflow_service),
) -> ProductCopyResponse:
    return service.generate_product_copy(request)
