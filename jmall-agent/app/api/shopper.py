from fastapi import APIRouter, Depends

from app.api.dependencies import get_shopper_intent_service
from app.models.requests import ShopperIntentRequest
from app.models.responses import ShopperIntentResponse
from app.services.shopper_intent_service import ShopperIntentService


router = APIRouter(prefix="/shopper", tags=["shopper-assistant"])


@router.post("/intent", response_model=ShopperIntentResponse)
def parse_shopper_intent(
    request: ShopperIntentRequest,
    service: ShopperIntentService = Depends(get_shopper_intent_service),
) -> ShopperIntentResponse:
    return service.analyze(request)
