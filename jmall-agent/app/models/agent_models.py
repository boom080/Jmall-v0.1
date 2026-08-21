"""Request/response models for the agent orchestration API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

# Supported e-commerce platform styles
SUPPORTED_STYLES = ["pinduoduo", "taobao", "jd", "suning", "xiaohongshu"]


class ProductInfoRequest(BaseModel):
    """Product information for agent tasks."""
    title: str = Field(..., min_length=1, max_length=120, description="商品标题")
    category: str = Field("未分类", max_length=60, description="商品分类")
    description: Optional[str] = Field(default="", max_length=5000, description="商品描述")
    price: Optional[str] = Field(default="", max_length=20, description="商品价格（数字字符串）")
    specifications: Optional[str] = Field(default="", max_length=2000, description="商家已确认的规格参数")
    target_audience: Optional[str] = Field(default="", max_length=500, description="商家已确认的目标人群")
    usage_scenarios: Optional[str] = Field(default="", max_length=1000, description="商家已确认的使用场景")

    @field_validator(
        "title", "category", "description", "price",
        "specifications", "target_audience", "usage_scenarios",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value):
        if value is None:
            return value
        return str(value).strip()


class OrchestrateRequest(BaseModel):
    """Request for the main agent orchestration endpoint."""
    product_info: ProductInfoRequest = Field(..., description="商品信息")
    target_style: str = Field("taobao", description="目标平台风格")
    knowledge_base_id: Optional[str] = Field(default=None, max_length=64, description="知识库 ID（可选）")
    user_request: Optional[str] = Field(default="", max_length=1000, description="商家的自定义需求描述")
    user_id: Optional[int] = Field(default=None, ge=1, description="发起任务的用户 ID（由后端代理注入）")
    product_draft_id: Optional[int] = Field(default=None, ge=1, description="关联商品草稿 ID（可选）")

    @field_validator("target_style", mode="before")
    @classmethod
    def normalize_style(cls, value):
        normalized = str(value).strip().lower() if value else "taobao"
        if normalized not in SUPPORTED_STYLES:
            raise ValueError(f"target_style 仅支持：{', '.join(SUPPORTED_STYLES)}")
        return normalized

    @field_validator("user_request", mode="before")
    @classmethod
    def normalize_request(cls, value):
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("knowledge_base_id", mode="before")
    @classmethod
    def normalize_kb_id(cls, value):
        return value or None


class CopyOnlyRequest(BaseModel):
    """Request for single-agent copy generation."""
    product_info: ProductInfoRequest = Field(..., description="商品信息")
    target_style: str = Field("taobao", description="目标平台风格")
    knowledge_base_id: Optional[str] = Field(default=None, max_length=64, description="知识库 ID")

    @field_validator("target_style", mode="before")
    @classmethod
    def normalize_style(cls, value):
        normalized = str(value).strip().lower() if value else "taobao"
        if normalized not in SUPPORTED_STYLES:
            raise ValueError(f"target_style 仅支持：{', '.join(SUPPORTED_STYLES)}")
        return normalized

    @field_validator("knowledge_base_id", mode="before")
    @classmethod
    def normalize_kb_id(cls, value):
        return value or None


class ReviewOnlyRequest(BaseModel):
    """Request for single-agent compliance review."""
    product_info: ProductInfoRequest = Field(..., description="商品信息")
    copy_content: Optional[str] = Field(default="", max_length=5000, description="需要审查的文案内容")

    @field_validator("copy_content", mode="before")
    @classmethod
    def normalize_content(cls, value):
        if value is None:
            return ""
        return str(value).strip()


class InsightsRequest(BaseModel):
    """Request for market insights."""
    category: str = Field(..., min_length=1, max_length=60, description="商品品类")
    keywords: Optional[List[str]] = Field(default=None, max_length=10, description="额外关键词")

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value):
        if value is None:
            raise ValueError("category 不能为空")
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("category 不能为空")
        return normalized


class StylePreviewRequest(BaseModel):
    """Request for style preview."""
    product_info: ProductInfoRequest = Field(..., description="商品信息")
    target_style: str = Field("taobao", description="目标平台风格")
    copy_drafts: Optional[Dict[str, Any]] = Field(default=None, description="已有的文案草稿（可选）")

    @field_validator("target_style", mode="before")
    @classmethod
    def normalize_style(cls, value):
        normalized = str(value).strip().lower() if value else "taobao"
        if normalized not in SUPPORTED_STYLES:
            raise ValueError(f"target_style 仅支持：{', '.join(SUPPORTED_STYLES)}")
        return normalized


class SearchTrendsRequest(BaseModel):
    """Request for market trend search."""
    category: str = Field(..., min_length=1, max_length=60, description="商品品类")
    keywords: Optional[List[str]] = Field(default=None, max_length=10, description="额外搜索关键词")

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value):
        if value is None:
            raise ValueError("category 不能为空")
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("category 不能为空")
        return normalized


# ---- Response Models ----

class OrchestrateResponse(BaseModel):
    """Response from the full agent orchestration."""
    success: bool = True
    message: str = ""
    overall_status: str = ""
    product_title: str = ""
    market_insights: Dict[str, Any] = Field(default_factory=dict)
    copy_content: Dict[str, Any] = Field(default_factory=dict, alias="copy")
    compliance: Dict[str, Any] = Field(default_factory=dict)
    style_adaptation: Dict[str, Any] = Field(default_factory=dict)
    pending_confirmations: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    generation_metadata: Dict[str, Any] = Field(default_factory=dict)
    cost_stats: Optional[Dict[str, Any]] = Field(default=None)


class CopyOnlyResponse(BaseModel):
    """Response from single-agent copy generation."""
    success: bool = True
    message: str = ""
    titles: List[str] = Field(default_factory=list)
    selling_points: List[str] = Field(default_factory=list)
    detail_copy: str = ""
    short_video_script: str = ""
    style: str = ""
    pending_confirmations: List[str] = Field(default_factory=list)


class ReviewOnlyResponse(BaseModel):
    """Response from single-agent compliance review."""
    success: bool = True
    message: str = ""
    status: str = "warning"
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checklist: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    suggestions: List[str] = Field(default_factory=list)


class InsightsResponse(BaseModel):
    """Response from market insights."""
    success: bool = True
    message: str = ""
    category: str = ""
    trends_summary: str = ""
    hot_keywords: List[str] = Field(default_factory=list)
    competitor_price_range: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)


class StyleInfo(BaseModel):
    """Style information."""
    id: str
    name: str
    description: str
    title_style: str = ""
    color_scheme: str = ""


class StylesListResponse(BaseModel):
    """List of available styles."""
    styles: List[StyleInfo] = Field(default_factory=list)
    total: int = 0


class StylePreviewResponse(BaseModel):
    """Response from style preview."""
    success: bool = True
    message: str = ""
    target_style: str = ""
    style_name: str = ""
    adapted_title: str = ""
    adapted_selling_points: List[str] = Field(default_factory=list)
    adapted_detail: str = ""
    visual_params: Dict[str, Any] = Field(default_factory=dict)
    style_notes: str = ""


class SearchTrendsResponse(BaseModel):
    """Response from search trends."""
    success: bool = True
    message: str = ""
    category: str = ""
    search_results: str = ""
    trends_summary: str = ""
    hot_keywords: List[str] = Field(default_factory=list)
    competitor_price_range: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)


class CostStatsResponse(BaseModel):
    """Cost tracking statistics."""
    daily_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    budget_daily_usd: float = 5.0
    over_budget: bool = False
    total_calls: int = 0
    cost_by_agent: Dict[str, float] = Field(default_factory=dict)
    tracking_enabled: bool = True


class RAGEvaluateRequest(BaseModel):
    """Request for RAG retrieval quality evaluation."""
    query: str = Field(..., min_length=1, max_length=500, description="检索查询")
    knowledge_base_id: str = Field(..., min_length=1, max_length=64, description="知识库 ID")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="检索数量")

    @field_validator("query", mode="before")
    @classmethod
    def normalize_query(cls, value):
        if value is None:
            raise ValueError("query 不能为空")
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("query 不能为空")
        return normalized

    @field_validator("knowledge_base_id", mode="before")
    @classmethod
    def normalize_kb_id(cls, value):
        if value is None:
            raise ValueError("knowledge_base_id 不能为空")
        return str(value).strip()


class RAGEvaluateResponse(BaseModel):
    """Response from RAG quality evaluation."""
    success: bool = True
    message: str = ""
    query: str = ""
    knowledge_base_id: str = ""
    total_retrieved: int = 0
    avg_relevance: float = 0.0
    hit_rate: float = 0.0
    mrr: float = 0.0
    ndcg: float = 0.0
    precision_at_k: float = 0.0
    judgments: List[Dict[str, Any]] = Field(default_factory=list)
