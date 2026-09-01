"""Request and response models for Image Scout."""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.agent_models import InputAssessment, ProductInfoRequest


class ImageCandidatesRequest(BaseModel):
    """Search request using the same product facts as the orchestration gate."""

    product_info: ProductInfoRequest
    user_id: Optional[int] = Field(default=None, ge=1)


class ImageCandidate(BaseModel):
    """A source-backed image result. No usage-rights claim is implied."""

    candidate_id: str
    title: str = ""
    thumbnail_url: str
    original_url: str
    source_page_url: str
    source_name: str
    author: str
    width: Optional[int] = Field(default=None, ge=1)
    height: Optional[int] = Field(default=None, ge=1)
    risk_flags: List[str] = Field(default_factory=list)
    risk_reasons: List[str] = Field(default_factory=list)


class ImageCandidatesResponse(BaseModel):
    """Structured Image Scout result used by the Java proxy and merchant UI."""

    status: str = "ready"
    query: str = ""
    provider: str = ""
    candidates: List[ImageCandidate] = Field(default_factory=list, max_length=3)
    input_assessment: InputAssessment = Field(default_factory=InputAssessment)
    message: str = ""
    disclaimer: str = "Jmall 仅提供图片检索与展示，不保证图片使用权；请在使用前自行核对。"
