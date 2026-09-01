"""Image Scout API."""

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.models.image_models import ImageCandidatesRequest, ImageCandidatesResponse
from app.providers.image_search import create_image_search_provider
from app.services.image_scout_service import ImageScoutService


router = APIRouter(prefix="/agent/images", tags=["image-scout"])


def get_image_scout_service(
    settings: Settings = Depends(get_settings),
) -> ImageScoutService:
    return ImageScoutService(create_image_search_provider(settings))


@router.post("/candidates", response_model=ImageCandidatesResponse)
async def image_candidates(
    request: ImageCandidatesRequest,
    service: ImageScoutService = Depends(get_image_scout_service),
) -> ImageCandidatesResponse:
    """Return at most three source-backed candidates; never download or alter them."""

    return await service.find_candidates(request)
